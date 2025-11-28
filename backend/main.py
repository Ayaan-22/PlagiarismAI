import io
import logging
import os
from typing import List, Dict, Tuple, Optional, Set

import aiohttp
import asyncio
import docx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer, util

# ---------------------------------------------------------
# Environment & Config
# ---------------------------------------------------------

load_dotenv()
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
CHUNK_SIZE = 700                        # characters per chunk
MAX_PAGE_CHUNKS_PER_SOURCE = 20
MIN_PAGE_CHUNK_LENGTH = 50
SIMILARITY_THRESHOLD = 30.0            # %
MAX_CHUNKS_QUICK_SCAN = 15
HTTP_TIMEOUT_SECONDS = 10
MAX_CONCURRENT_REQUESTS = 5
MAX_RESULTS_PER_CHUNK = 5              # SERP results per chunk
MAX_MATCHES_RETURNED = 20
MAX_PAGE_TEXT_CHARS = 35_000           # per page fetch, to avoid huge embeddings

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("plagiarism-checker")

# ---------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------

app = FastAPI(title="Plagiarism Checker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In real prod, restrict this to your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# ML Model (loaded once at startup)
# ---------------------------------------------------------

try:
    logger.info("Loading SentenceTransformer model...")
    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.exception("Failed to load SentenceTransformer model.")
    raise e

# ---------------------------------------------------------
# Utility Functions: Text Extraction
# ---------------------------------------------------------


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
            text.append(page_text)
        except Exception as e:
            logger.warning("Error extracting text from a PDF page: %s", e)
    return "\n".join(text)


def extract_docx_text(file_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_txt_text(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
    """Split text into fixed-size character chunks."""
    text = text.strip()
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]


# ---------------------------------------------------------
# Security: Basic SSRF Protection
# ---------------------------------------------------------


def is_safe_url(url: str) -> bool:
    """
    Basic SSRF protection:
    - Disallow localhost / loopback
    - Disallow typical private IP ranges
    """
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()

        if not hostname:
            return False

        # Block localhost / loopback
        if hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
            return False

        # Block typical private ranges
        private_prefixes = (
            "10.",
            "192.168.",
            "172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
            "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
            "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
        )
        if any(hostname.startswith(prefix) for prefix in private_prefixes):
            return False

        return True
    except Exception as e:
        logger.warning("Failed to validate URL %s: %s", url, e)
        return False


# ---------------------------------------------------------
# SerpAPI Search
# ---------------------------------------------------------


async def serp_search_async(query: str, session: aiohttp.ClientSession) -> List[Dict]:
    """Async Google search using SerpAPI."""

    if not SERPAPI_KEY:
        logger.warning("SERPAPI_KEY not configured. Skipping web search.")
        return []

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": MAX_RESULTS_PER_CHUNK,
    }

    try:
        async with session.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                logger.warning("SerpAPI returned non-200 status: %s", response.status)
                return []

            data = await response.json()
            results = data.get("organic_results", []) or []
            cleaned: List[Dict] = []
            for result in results[:MAX_RESULTS_PER_CHUNK]:
                link = result.get("link")
                snippet = result.get("snippet", "")
                if link and is_safe_url(link):
                    cleaned.append({"url": link, "snippet": snippet})
            return cleaned

    except asyncio.TimeoutError:
        logger.warning("SerpAPI request timed out.")
        return []
    except Exception as e:
        logger.exception("Error during SerpAPI search: %s", e)
        return []


# ---------------------------------------------------------
# Web Page Fetching
# ---------------------------------------------------------


async def fetch_page_async(url: str, session: aiohttp.ClientSession) -> str:
    """Async fetch of page content, including PDF extraction."""

    if not is_safe_url(url):
        logger.warning("Blocked unsafe URL: %s", url)
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        async with session.get(url, headers=headers, timeout=timeout) as response:
            if response.status != 200:
                logger.info("Skipping URL %s (status %s)", url, response.status)
                return ""

            content_type = response.headers.get("Content-Type", "").lower()
            content_length = response.headers.get("Content-Length")

            if content_length is not None:
                try:
                    if int(content_length) > 10 * 1024 * 1024:  # 10 MB
                        logger.info("Skipping large response from %s", url)
                        return ""
                except ValueError:
                    pass

            # Handle PDF
            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                try:
                    pdf_bytes = await response.read()
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    text_parts: List[str] = []
                    for page in reader.pages:
                        try:
                            t = page.extract_text() or ""
                            text_parts.append(t)
                        except Exception as e:
                            logger.warning("Error extracting PDF page from %s: %s", url, e)
                    text = "\n".join(text_parts)
                    return text[:MAX_PAGE_TEXT_CHARS]
                except Exception as e:
                    logger.warning("Error extracting PDF from %s: %s", url, e)
                    return ""

            # Handle HTML / text
            if "text/html" in content_type or "text/plain" in content_type:
                try:
                    raw = await response.text(errors="ignore")
                except TypeError:
                    # For older aiohttp versions without errors param
                    raw = await response.text()

                soup = BeautifulSoup(raw, "html.parser")
                # Remove noisy tags
                for tag in soup(["script", "style", "meta", "noscript", "header", "footer", "nav"]):
                    tag.extract()

                text = soup.get_text(separator=" ", strip=True)
                return text[:MAX_PAGE_TEXT_CHARS]

            # Other content types (images, videos, etc.) are skipped
            return ""

    except asyncio.TimeoutError:
        logger.info("Timeout fetching URL %s", url)
        return ""
    except Exception as e:
        logger.warning("Error fetching %s: %s", url, e)
        return ""


# ---------------------------------------------------------
# Similarity Computation (Batched)
# ---------------------------------------------------------


def compute_best_similarity(chunk: str, page_text: str) -> Tuple[float, str]:
    """
    Compute the best similarity by comparing the chunk against
    all chunks of the page using batched embeddings.
    Returns (max_similarity, best_matching_chunk_text).
    """
    if not page_text or len(page_text) < 100:
        return 0.0, ""

    page_chunks = chunk_text(page_text, size=CHUNK_SIZE)
    if not page_chunks:
        return 0.0, ""

    # Limit number of chunks for performance
    page_chunks = page_chunks[:MAX_PAGE_CHUNKS_PER_SOURCE]

    # Encode user chunk once
    chunk_emb = model.encode(chunk, convert_to_tensor=True)

    # Encode all page chunks in batch
    page_embs = model.encode(page_chunks, convert_to_tensor=True)

    # Compute cosine similarities
    similarities = util.pytorch_cos_sim(chunk_emb, page_embs)[0] * 100.0  # convert to %
    similarities_list = similarities.tolist()

    max_similarity = 0.0
    best_match_chunk = ""

    for idx, page_chunk in enumerate(page_chunks):
        if len(page_chunk.strip()) < MIN_PAGE_CHUNK_LENGTH:
            continue
        sim = similarities_list[idx]
        if sim > max_similarity:
            max_similarity = sim
            best_match_chunk = page_chunk

    return round(max_similarity, 2), best_match_chunk


# ---------------------------------------------------------
# Per-chunk Processing
# ---------------------------------------------------------


async def process_chunk(
    chunk: str,
    chunk_index: int,
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
) -> List[Dict]:
    """
    Process a single text chunk:
    - Search web via SerpAPI
    - Fetch candidate pages
    - Compute similarity
    - Return list of matches above threshold
    """
    async with semaphore:
        search_query = chunk[:150]
        logger.info("Searching web for chunk %d...", chunk_index)
        search_results = await serp_search_async(search_query, session)

        chunk_matches: List[Dict] = []

        for result in search_results:
            url = result["url"]
            snippet = result.get("snippet", "")

            page_text = await fetch_page_async(url, session)

            # If page fetch failed but we have a snippet, use snippet as fallback
            if not page_text and snippet:
                page_text = snippet

            if not page_text:
                continue

            similarity, matched_chunk = compute_best_similarity(chunk, page_text)

            if similarity >= SIMILARITY_THRESHOLD:
                chunk_matches.append(
                    {
                        "chunk_index": chunk_index,
                        "chunk": chunk,
                        "source": url,
                        "similarity": similarity,
                        "matched_content": matched_chunk,
                    }
                )

        return chunk_matches


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------


@app.get("/health")
async def health_check():
    """Health check endpoint for frontend connection status."""
    return {"status": "ok", "message": "Backend is running"}


@app.post("/check")
async def check_plagiarism(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    scan_mode: str = Form("quick"),  # "quick" or "deep"
):
    """
    Main plagiarism-checking endpoint.

    - Accepts raw text or a file (PDF/DOCX/TXT).
    - Splits input into chunks.
    - For each chunk, performs web search and similarity check.
    - Returns plagiarism percentage + top matches.
    """

    # -------------------------------
    # Input Handling (file or text)
    # -------------------------------
    if file is not None:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max allowed size is {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB.",
            )

        filename = (file.filename or "").lower()
        logger.info("Processing uploaded file: %s", filename)

        try:
            if filename.endswith(".pdf"):
                text = extract_pdf_text(file_bytes)
            elif filename.endswith(".docx"):
                text = extract_docx_text(file_bytes)
            elif filename.endswith(".txt"):
                text = extract_txt_text(file_bytes)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file format. Please upload PDF, DOCX, or TXT.",
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error processing uploaded file: %s", e)
            raise HTTPException(status_code=500, detail="Failed to process uploaded file.")

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No text provided.")

    text = text.strip()
    chunks = chunk_text(text)

    if not chunks:
        raise HTTPException(status_code=400, detail="Text is too short to analyze.")

    # -------------------------------
    # Scan mode handling
    # -------------------------------
    scan_mode = (scan_mode or "quick").lower()
    if scan_mode not in {"quick", "deep"}:
        scan_mode = "quick"

    if scan_mode == "quick":
        if len(chunks) > MAX_CHUNKS_QUICK_SCAN:
            chunks = chunks[:MAX_CHUNKS_QUICK_SCAN]
        logger.info("Running QUICK scan on %d chunks.", len(chunks))
    else:
        logger.info("Running DEEP scan on %d chunks.", len(chunks))

    # -------------------------------
    # Async processing of chunks
    # -------------------------------
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        tasks = [
            process_chunk(chunk, idx, session, semaphore)
            for idx, chunk in enumerate(chunks)
        ]
        try:
            results = await asyncio.gather(*tasks)
        except Exception as e:
            logger.exception("Unexpected error during chunk processing: %s", e)
            raise HTTPException(status_code=500, detail="Error while processing text.")

    # Flatten matches
    all_matches: List[Dict] = [
        match for chunk_matches in results for match in chunk_matches
    ]

    # -------------------------------
    # Plagiarism percentage calculation
    # -------------------------------
    if all_matches:
        # Count how many distinct chunks have any match
        matched_chunk_indices: Set[int] = {m["chunk_index"] for m in all_matches}
        plagiarism_percent = round(
            (len(matched_chunk_indices) / len(chunks)) * 100.0, 2
        )
    else:
        plagiarism_percent = 0.0

    # Sort matches by similarity (highest first)
    all_matches.sort(key=lambda x: x["similarity"], reverse=True)

    # Remove duplicate sources, keeping highest similarity per source
    seen_sources: Set[str] = set()
    unique_matches: List[Dict] = []
    for match in all_matches:
        source = match["source"]
        if source in seen_sources:
            continue
        seen_sources.add(source)
        unique_matches.append(match)

    # Limit number of matches in response
    unique_matches = unique_matches[:MAX_MATCHES_RETURNED]

    return {
        "plagiarism_percent": plagiarism_percent,
        "matches": unique_matches,
        "scan_mode": scan_mode,
        "total_chunks_analyzed": len(chunks),
    }


if __name__ == "__main__":
    import uvicorn

    # For production, run via: `uvicorn main:app --host 0.0.0.0 --port 9001`
    uvicorn.run(app, host="127.0.0.1", port=9001)
