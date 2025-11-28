"""
Production-ready Plagiarism Checker API (FastAPI)

Key features:
- File + raw text input (PDF / DOCX / TXT)
- Async web search using SerpAPI
- Async content fetching (HTML + PDF)
- Sentence-transformer based similarity
- Proper citation detection and handling
- Clear status labels for each chunk
- Overall plagiarism percentage (citation-safe chunks excluded)
"""

import asyncio
import io
import logging
import os
import re
from typing import List, Dict, Tuple, Optional, Set, Any

import aiohttp
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
CHUNK_SIZE = 700  # characters per chunk
MAX_PAGE_CHUNKS_PER_SOURCE = 20
MIN_PAGE_CHUNK_LENGTH = 50

SIMILARITY_THRESHOLD = 30.0  # %
HIGH_SIMILARITY_THRESHOLD = 60.0  # % (for stronger warnings)

MAX_CHUNKS_QUICK_SCAN = 15
HTTP_TIMEOUT_SECONDS = 10
MAX_CONCURRENT_REQUESTS = 5
MAX_RESULTS_PER_CHUNK = 5  # SERP results per chunk
MAX_MATCHES_RETURNED = 20
MAX_PAGE_TEXT_CHARS = 35_000  # per page fetch, to avoid huge embeddings

# ---------------------------------------------------------
# Citation Patterns
# ---------------------------------------------------------
# Note: Kept relatively broad on purpose to avoid missing citations.
# We combine them with quote detection + context-based decisions later.

CITATION_PATTERNS: List[str] = [
    r"\([A-Z][a-z]+,\s?\d{4}\)",          # (Smith, 2020)  - APA style
    r"\([A-Z][a-z]+\s\d{4}\)",            # (Smith 2020)   - Variant APA/MLA
    r"\[[0-9]+\]",                        # [1]            - IEEE / numeric
    r"[A-Z][a-z]+\s\d{4},\s?\d+–\d+",     # Brown 1999, 17–19
    r"\d+\s?[A-Z][a-z]+\s?\d{4}",         # 12 Smith 2020  - inline numeric
    r"\bet al\.\b",                       # et al.
    r"\d+\.",                             # 1. / 2. (footnote-like references; broad!)
]

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

app = FastAPI(
    title="Plagiarism Checker API",
    version="5.0.0",
    description="Async plagiarism checker with citation awareness.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend domains
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
    """Extract text from a PDF file."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts: List[str] = []

    for page_idx, page in enumerate(reader.pages):
        try:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
        except Exception as e:
            logger.warning("Error extracting text from PDF page %d: %s", page_idx, e)

    return "\n".join(text_parts)


def extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from a DOCX file."""
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(para.text for para in document.paragraphs if para.text.strip())


def extract_txt_text(file_bytes: bytes) -> str:
    """Extract text from a TXT file."""
    return file_bytes.decode("utf-8", errors="ignore")


def chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
    """
    Split text into fixed-size character chunks.

    We don't try to be sentence-smart here on purpose;
    this keeps behavior deterministic and simple.
    """
    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    for i in range(0, len(text), size):
        chunk = text[i : i + size].strip()
        if chunk:
            chunks.append(chunk)

    return chunks


# ---------------------------------------------------------
# Security: Basic SSRF Protection
# ---------------------------------------------------------


def is_safe_url(url: str) -> bool:
    """
    Basic SSRF protection:
    - Disallow localhost / loopback
    - Disallow typical private IP ranges
    - Reject empty hostnames
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

        # Block typical private ranges (IPv4)
        private_prefixes = (
            "10.",
            "192.168.",
            "172.16.", "172.17.", "172.18.", "172.19.", "172.20.",
            "172.21.", "172.22.", "172.23.", "172.24.", "172.25.",
            "172.26.", "172.27.", "172.28.", "172.29.", "172.30.", "172.31.",
        )
        if any(hostname.startswith(prefix) for prefix in private_prefixes):
            return False

        # Simple IPv6 localhost check
        if hostname in {"::1"}:
            return False

        return True
    except Exception as e:
        logger.warning("Failed to validate URL %s: %s", url, e)
        return False


# ---------------------------------------------------------
# Citation Detection
# ---------------------------------------------------------


def _infer_citation_style_from_pattern(pattern: str) -> str:
    """
    Roughly infer citation style based on which regex matched.
    This is heuristic and not perfect, but good enough for feedback.
    """
    if pattern == r"\[[0-9]+\]":
        return "IEEE / Numeric"
    if "et al" in pattern.lower():
        return "Author + et al."
    if pattern in {r"\d+\.", r"\d+\s?[A-Z][a-z]+\s?\d{4}"}:
        return "Footnote / Numeric"
    # Default fallback
    return "Author-Date (APA/MLA-like)"


def detect_citation(chunk: str) -> Tuple[bool, str]:
    """
    Detect if the chunk contains a proper academic citation.

    Returns:
        (is_cited, citation_style)
    - is_cited: True if any citation pattern is detected.
    - citation_style: Rough description of detected style.
    """
    if not chunk or len(chunk.strip()) < 20:
        return False, ""

    # Check for quotes: if a passage is quoted and also has citation patterns,
    # we treat it as more likely properly cited.
    has_quotes = '"' in chunk or "“" in chunk or "”" in chunk or "'" in chunk

    # Match patterns case-insensitively
    for pattern in CITATION_PATTERNS:
        if re.search(pattern, chunk, flags=re.IGNORECASE):
            style = _infer_citation_style_from_pattern(pattern)

            # If quoted + citation → very likely properly cited
            if has_quotes:
                return True, f"Quoted + {style}"

            return True, style

    return False, ""


# ---------------------------------------------------------
# SerpAPI Search
# ---------------------------------------------------------


async def serp_search_async(query: str, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """
    Async Google search using SerpAPI.

    Returns a list of dicts:
        {"url": str, "snippet": str}
    """
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

            cleaned: List[Dict[str, Any]] = []
            for result in results[:MAX_RESULTS_PER_CHUNK]:
                link = result.get("link")
                snippet = result.get("snippet", "") or ""
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
    """
    Async fetch of page content, including PDF extraction.

    Returns:
        Cleaned plain text (truncated to MAX_PAGE_TEXT_CHARS), or "" on failure.
    """
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

            content_type = (response.headers.get("Content-Type") or "").lower()
            content_length = response.headers.get("Content-Length")

            if content_length is not None:
                try:
                    if int(content_length) > 10 * 1024 * 1024:  # 10 MB
                        logger.info("Skipping large response from %s", url)
                        return ""
                except ValueError:
                    # If Content-Length is invalid, ignore and continue
                    pass

            # ----------------- PDF Handling -----------------
            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                try:
                    pdf_bytes = await response.read()
                    reader = PdfReader(io.BytesIO(pdf_bytes))

                    text_parts: List[str] = []
                    for page_idx, page in enumerate(reader.pages):
                        try:
                            t = page.extract_text() or ""
                            if t.strip():
                                text_parts.append(t)
                        except Exception as e:
                            logger.warning(
                                "Error extracting PDF page from %s (page %d): %s", url, page_idx, e
                            )

                    full_text = "\n".join(text_parts)
                    return full_text[:MAX_PAGE_TEXT_CHARS]
                except Exception as e:
                    logger.warning("Error extracting PDF from %s: %s", url, e)
                    return ""

            # ----------------- HTML / Text Handling -----------------
            if "text/html" in content_type or "text/plain" in content_type:
                try:
                    raw = await response.text(errors="ignore")
                except TypeError:
                    # For older aiohttp versions without 'errors' param
                    raw = await response.text()

                soup = BeautifulSoup(raw, "html.parser")

                # Remove noisy tags
                for tag in soup(
                    ["script", "style", "meta", "noscript", "header", "footer", "nav"]
                ):
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

    Returns:
        (max_similarity, best_matching_chunk_text)
    """
    if not page_text or len(page_text) < 100:
        return 0.0, ""

    page_chunks = chunk_text(page_text, size=CHUNK_SIZE)
    if not page_chunks:
        return 0.0, ""

    # Limit number of chunks per source for performance
    page_chunks = page_chunks[:MAX_PAGE_CHUNKS_PER_SOURCE]

    # Encode user chunk once
    chunk_emb = model.encode(chunk, convert_to_tensor=True)

    # Encode all page chunks in batch
    page_embs = model.encode(page_chunks, convert_to_tensor=True)

    # Compute cosine similarities and convert to percentage
    similarities = util.pytorch_cos_sim(chunk_emb, page_embs)[0] * 100.0
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


def classify_similarity_status(similarity: float, cited: bool) -> str:
    """
    Map similarity + citation presence to a human-readable status.

    This is used for frontend labels.
    """
    if cited:
        return "Properly Cited — No Plagiarism"

    if similarity < SIMILARITY_THRESHOLD:
        return "No Significant Match Detected"

    if similarity >= HIGH_SIMILARITY_THRESHOLD:
        return "High Risk — Strong Overlap, Citation Required"

    return "Potential Plagiarism — Add Citation or Rewrite"


# ---------------------------------------------------------
# Per-chunk Processing
# ---------------------------------------------------------


async def process_chunk(
    chunk: str,
    chunk_index: int,
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    """
    Process a single text chunk:
    - Check for citations (skip web search if clearly cited)
    - If not cited, search web via SerpAPI
    - Fetch candidate pages
    - Compute similarity
    - Return list of matches above threshold, or citation-safe info
    """
    chunk = chunk.strip()
    if not chunk:
        return []

    # ----------------- 1. Check for citations -----------------
    is_cited, citation_style = detect_citation(chunk)

    if is_cited:
        logger.info(
            "Chunk %d detected as properly cited (%s). Skipping web search.",
            chunk_index,
            citation_style,
        )
        return [
            {
                "chunk_index": chunk_index,
                "chunk": chunk,
                "citation_safe": True,
                "citation_style": citation_style,
                "similarity": 0.0,
                "status": classify_similarity_status(0.0, cited=True),
                "source": "Citation Detected",
                "matched_content": "",
                "recommendation": (
                    "This passage appears to be properly cited. Ensure your bibliography "
                    "or reference list includes the full source details in a consistent "
                    "citation style (e.g., APA, MLA, IEEE)."
                ),
            }
        ]

    # ----------------- 2. Web search for uncited chunk -----------------
    async with semaphore:
        search_query = chunk[:150]
        logger.info("Searching web for chunk %d...", chunk_index)
        search_results = await serp_search_async(search_query, session)

        chunk_matches: List[Dict[str, Any]] = []

        for result in search_results:
            url = result["url"]
            snippet = result.get("snippet", "") or ""

            page_text = await fetch_page_async(url, session)

            # If page fetch failed but we have a snippet, use snippet as fallback
            if not page_text and snippet:
                page_text = snippet

            if not page_text:
                continue

            similarity, matched_chunk = compute_best_similarity(chunk, page_text)

            if similarity >= SIMILARITY_THRESHOLD:
                status_label = classify_similarity_status(similarity, cited=False)

                # Recommendation text to help user fix the issue
                if similarity >= HIGH_SIMILARITY_THRESHOLD:
                    recommendation = (
                        "This section is very similar to an external source. "
                        "Either rewrite it in your own words OR keep the wording but "
                        "add a clear in-text citation and full reference (APA/MLA/IEEE)."
                    )
                else:
                    recommendation = (
                        "Part of this text closely matches an external source. "
                        "Add a proper citation (author, year, page) and include the "
                        "source in your reference list, or paraphrase more strongly."
                    )

                chunk_matches.append(
                    {
                        "chunk_index": chunk_index,
                        "chunk": chunk,
                        "source": url,
                        "similarity": similarity,
                        "matched_content": matched_chunk,
                        "citation_safe": False,
                        "citation_style": "",
                        "status": status_label,
                        "recommendation": recommendation,
                    }
                )

        # If no matches found for this uncited chunk, we still return nothing.
        # The overall plagiarism percentage only considers chunks with matches.
        return chunk_matches


# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------


@app.get("/health")
async def health_check() -> Dict[str, str]:
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
    - Splits input into character-based chunks.
    - For each chunk:
        - Detects citations.
        - If not cited, performs web search + similarity checks.
    - Returns:
        - overall plagiarism percentage (excluding properly cited chunks)
        - detailed per-chunk matches
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
                detail=(
                    f"File too large. Max allowed size is "
                    f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
                ),
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
            # Re-raise HTTP errors directly
            raise
        except Exception as e:
            logger.exception("Error processing uploaded file: %s", e)
            raise HTTPException(
                status_code=500, detail="Failed to process uploaded file."
            )

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No text provided.")

    text = text.strip()
    chunks = chunk_text(text)

    if not chunks:
        raise HTTPException(
            status_code=400, detail="Text is too short to analyze meaningfully."
        )

    # -------------------------------
    # Scan mode handling
    # -------------------------------
    scan_mode_normalized = (scan_mode or "quick").lower()
    if scan_mode_normalized not in {"quick", "deep"}:
        scan_mode_normalized = "quick"

    if scan_mode_normalized == "quick":
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
            results: List[List[Dict[str, Any]]] = await asyncio.gather(*tasks)
        except Exception as e:
            logger.exception("Unexpected error during chunk processing: %s", e)
            raise HTTPException(
                status_code=500, detail="Error while processing text."
            )

    # Flatten matches
    all_matches: List[Dict[str, Any]] = [
        match for chunk_matches in results for match in chunk_matches
    ]

    # -------------------------------
    # Plagiarism percentage calculation
    # -------------------------------
    if all_matches:
        # Chunks explicitly marked as citation-safe
        citation_safe_indices: Set[int] = {
            m["chunk_index"] for m in all_matches if m.get("citation_safe")
        }

        # Chunks that have plagiarism-like matches (NOT citation safe)
        plagiarized_chunk_indices: Set[int] = {
            m["chunk_index"]
            for m in all_matches
            if not m.get("citation_safe")
            and m.get("similarity", 0.0) >= SIMILARITY_THRESHOLD
        }

        # Ensure citation-safe chunks are NOT counted as plagiarized
        plagiarized_chunk_indices -= citation_safe_indices

        plagiarism_percent = round(
            (len(plagiarized_chunk_indices) / len(chunks)) * 100.0, 2
        )
    else:
        plagiarism_percent = 0.0

    # -------------------------------
    # Post-processing of matches
    # -------------------------------
    # Sort matches by similarity (highest first; citation-safe entries have 0)
    all_matches.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)

    # Remove duplicate non-citation sources, keeping highest similarity per source.
    # Citation entries ("Citation Detected") are preserved per chunk.
    seen_sources: Set[str] = set()
    unique_matches: List[Dict[str, Any]] = []

    for match in all_matches:
        source = match.get("source", "")

        # Allow multiple "Citation Detected" entries (one per chunk)
        # because they tell the frontend exactly which chunks are fine.
        if match.get("citation_safe"):
            unique_matches.append(match)
            continue

        if source in seen_sources:
            continue

        seen_sources.add(source)
        unique_matches.append(match)

    # Limit number of matches in response
    unique_matches = unique_matches[:MAX_MATCHES_RETURNED]

    # High-level summary for frontend UI
    summary = {
        "total_chunks_analyzed": len(chunks),
        "chunks_with_matches": len(
            {
                m["chunk_index"]
                for m in unique_matches
                if not m.get("citation_safe")
                and m.get("similarity", 0.0) >= SIMILARITY_THRESHOLD
            }
        ),
        "citation_safe_chunks": len(
            {m["chunk_index"] for m in unique_matches if m.get("citation_safe")}
        ),
    }

    return {
        "scan_mode": scan_mode_normalized,
        "plagiarism_percent": plagiarism_percent,
        "summary": summary,
        "matches": unique_matches,
    }


if __name__ == "__main__":
    import uvicorn

    # For production, run via:
    #   uvicorn main:app --host 0.0.0.0 --port 9001
    uvicorn.run(app, host="127.0.0.1", port=9001)
