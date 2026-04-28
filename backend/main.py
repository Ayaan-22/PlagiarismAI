import asyncio
import logging
import ssl
from typing import List, Dict, Any, Optional

import aiohttp
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from langdetect import detect, LangDetectException

# Config
from config import (
    ALLOWED_ORIGINS, MAX_FILE_SIZE_BYTES, MAX_TEXT_INPUT_CHARS,
    MAX_CHUNKS_QUICK_SCAN, SIMILARITY_THRESHOLD, HIGH_SIMILARITY_THRESHOLD,
    MAX_CONCURRENT_REQUESTS, MAX_MATCHES_RETURNED
)

# Security
from security.auth import get_api_key
from security.rate_limiter import limiter
from security.headers import SecurityHeadersMiddleware
from security.sanitizer import sanitize_html

# Services
from services.text_extraction import (
    get_mime_type, extract_pdf_text, extract_docx_text, 
    extract_txt_text, chunk_text
)
from services.search import search_cache, build_search_query, serp_search_async
from services.scraper import fetch_page_async
from services.citation import detect_citation
from services.similarity import load_model, compute_best_similarity_async

# Middleware
from middleware.logging_middleware import AuditLoggingMiddleware

# ---------------------------------------------------------
# Logging setup
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")
logger = logging.getLogger("plagiarism-checker.main")

# ---------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------

app = FastAPI(title="Secure Plagiarism Checker API", version="6.1.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom Security Middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLoggingMiddleware)

# Setup Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Load ML Model on Startup
@app.on_event("startup")
async def startup_event():
    logger.info("Loading SentenceTransformer model...")
    load_model()
    logger.info("Model loaded successfully.")

# ---------------------------------------------------------
# Per-chunk Processing
# ---------------------------------------------------------

def classify_similarity_status(similarity: float, cited: bool) -> str:
    if cited:
        return "Properly Cited \u2014 No Plagiarism"
    if similarity < SIMILARITY_THRESHOLD:
        return "No Significant Match Detected"
    if similarity >= HIGH_SIMILARITY_THRESHOLD:
        return "High Risk \u2014 Strong Overlap, Citation Required"
    return "Potential Plagiarism \u2014 Add Citation or Rewrite"

async def process_chunk(
    chunk: str,
    chunk_index: int,
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
) -> List[Dict[str, Any]]:
    chunk = chunk.strip()
    if not chunk:
        return []

    try:
        lang = detect(chunk)
    except LangDetectException:
        lang = "unknown"

    is_cited, citation_style = detect_citation(chunk)

    if is_cited:
        return [{
            "chunk_index": chunk_index,
            "chunk": chunk,
            "citation_safe": True,
            "citation_style": citation_style,
            "similarity": 0.0,
            "status": classify_similarity_status(0.0, cited=True),
            "source": "Citation Detected",
            "matched_content": "",
            "recommendation": "This passage appears to be properly cited."
        }]

    async with semaphore:
        search_query = build_search_query(chunk)
        search_results = await serp_search_async(search_query, session, lang=None if lang == "unknown" else lang)

        chunk_matches: List[Dict[str, Any]] = []

        for result in search_results:
            url = result["url"]
            snippet = result.get("snippet", "") or ""
            page_text = await fetch_page_async(url, session)

            if not page_text and snippet:
                page_text = snippet

            if not page_text:
                continue

            similarity, matched_chunk = await compute_best_similarity_async(chunk, page_text)

            if similarity >= SIMILARITY_THRESHOLD:
                status_label = classify_similarity_status(similarity, cited=False)
                if similarity >= HIGH_SIMILARITY_THRESHOLD:
                    recommendation = "This section is very similar to an external source. Rewrite it or add a clear in-text citation."
                else:
                    recommendation = "Part of this text closely matches an external source. Add a proper citation."

                # Sanitize output
                safe_matched_chunk = sanitize_html(matched_chunk)

                chunk_matches.append({
                    "chunk_index": chunk_index,
                    "chunk": chunk,
                    "source": url,
                    "similarity": similarity,
                    "matched_content": safe_matched_chunk,
                    "citation_safe": False,
                    "citation_style": "",
                    "status": status_label,
                    "recommendation": recommendation,
                })

        return chunk_matches

# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "message": "Backend is running securely"}

@app.post("/check")
@limiter.limit("5/minute", exempt_when=lambda: False) # Default to quick limit, but dynamically handled
async def check_plagiarism(
    request: Request,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    scan_mode: str = Form("quick"),
    api_key: str = Depends(get_api_key)
):
    # Dynamic Rate Limiting Adjustment based on scan_mode
    scan_mode_normalized = (scan_mode or "quick").lower()
    if scan_mode_normalized == "deep":
        # Check deep limit
        limiter_deep = limiter.limit("1/minute")(lambda request: None)
        try:
            limiter_deep(request)
        except Exception as e:
            raise RateLimitExceeded(detail="Rate limit exceeded for deep scan (1 per minute)")

    raw_text: Optional[str] = None

    if file is not None:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=400, detail="File too large.")

        mime_type = get_mime_type(file_bytes)
        filename = (file.filename or "").lower()

        try:
            if "pdf" in mime_type or filename.endswith(".pdf"):
                raw_text = extract_pdf_text(file_bytes)
            elif "wordprocessingml" in mime_type or filename.endswith(".docx"):
                raw_text = extract_docx_text(file_bytes)
            elif "text" in mime_type or filename.endswith(".txt"):
                raw_text = extract_txt_text(file_bytes)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported file format ({mime_type}).")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error processing uploaded file")
            raise HTTPException(status_code=500, detail="Failed to process uploaded file.")
    elif text is not None:
        raw_text = text.strip()
        if len(raw_text) > MAX_TEXT_INPUT_CHARS:
             raise HTTPException(status_code=400, detail="Text input too long.")
    else:
        raise HTTPException(status_code=400, detail="No text or file provided.")

    if not raw_text or not raw_text.strip():
        raise HTTPException(status_code=400, detail="Provided content is empty or unreadable.")

    chunks = chunk_text(raw_text)
    if not chunks:
        raise HTTPException(status_code=400, detail="Text is too short to analyze.")

    if scan_mode_normalized == "quick":
        if len(chunks) > MAX_CHUNKS_QUICK_SCAN:
            chunks = chunks[:MAX_CHUNKS_QUICK_SCAN]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    # Enforce SSL using secure default context
    ssl_context = ssl.create_default_context()

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = [process_chunk(chunk, idx, session, semaphore) for idx, chunk in enumerate(chunks)]
        try:
            results: List[List[Dict[str, Any]]] = await asyncio.gather(*tasks)
        except Exception as e:
            logger.exception("Unexpected error during chunk processing")
            raise HTTPException(status_code=500, detail="Error while processing text.")

    all_matches: List[Dict[str, Any]] = [match for chunk_matches in results for match in chunk_matches]

    if all_matches:
        citation_safe_indices = {m["chunk_index"] for m in all_matches if m.get("citation_safe")}
        plagiarized_chunk_indices = {
            m["chunk_index"] for m in all_matches
            if not m.get("citation_safe") and m.get("similarity", 0.0) >= SIMILARITY_THRESHOLD
        }
        plagiarized_chunk_indices -= citation_safe_indices
        plagiarism_percent = round((len(plagiarized_chunk_indices) / len(chunks)) * 100.0, 2)
    else:
        plagiarism_percent = 0.0

    all_matches.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
    seen_sources = set()
    unique_matches = []

    for match in all_matches:
        source = match.get("source", "")
        if match.get("citation_safe"):
            unique_matches.append(match)
            continue
        if source in seen_sources:
            continue
        seen_sources.add(source)
        unique_matches.append(match)

    unique_matches = unique_matches[:MAX_MATCHES_RETURNED]

    summary = {
        "total_chunks_analyzed": len(chunks),
        "chunks_with_matches": len({
            m["chunk_index"] for m in unique_matches
            if not m.get("citation_safe") and m.get("similarity", 0.0) >= SIMILARITY_THRESHOLD
        }),
        "citation_safe_chunks": len({m["chunk_index"] for m in unique_matches if m.get("citation_safe")}),
    }

    return {
        "scan_mode": scan_mode_normalized,
        "plagiarism_percent": plagiarism_percent,
        "summary": summary,
        "matches": unique_matches,
        "warnings": [],
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=9002, reload=True)
