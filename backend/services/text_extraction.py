import io
import re
import logging
from typing import List

import docx
from PyPDF2 import PdfReader
from fastapi import HTTPException
import magic

from config import CHUNK_SIZE, MAX_EXTRACTED_TEXT_CHARS, MAX_CHUNKS

logger = logging.getLogger("plagiarism-checker.services.text_extraction")

def get_mime_type(file_bytes: bytes) -> str:
    """Uses libmagic to determine true MIME type."""
    try:
        return magic.from_buffer(file_bytes, mime=True)
    except Exception as e:
        logger.warning("Magic MIME detection failed: %s", e)
        return "application/octet-stream"

def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from a PDF file with limits."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text_parts: List[str] = []
    
    # Cap pages to prevent zip-bomb / DoS
    max_pages = min(len(reader.pages), 200)

    for page_idx in range(max_pages):
        try:
            page_text = reader.pages[page_idx].extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
                
            # Early exit if we exceed max chars
            if sum(len(p) for p in text_parts) > MAX_EXTRACTED_TEXT_CHARS:
                break
        except Exception as e:
            logger.warning("Error extracting text from PDF page %d: %s", page_idx, e)

    return "\n".join(text_parts)[:MAX_EXTRACTED_TEXT_CHARS]

def extract_docx_text(file_bytes: bytes) -> str:
    """Extract text from a DOCX file with limits."""
    document = docx.Document(io.BytesIO(file_bytes))
    text_parts: List[str] = []
    current_length = 0
    
    # Cap paragraphs
    for para in document.paragraphs[:5000]:
        t = para.text.strip()
        if t:
            text_parts.append(t)
            current_length += len(t)
            if current_length > MAX_EXTRACTED_TEXT_CHARS:
                break
                
    return "\n".join(text_parts)[:MAX_EXTRACTED_TEXT_CHARS]

def extract_txt_text(file_bytes: bytes) -> str:
    """Extract text from a TXT file with limits."""
    return file_bytes.decode("utf-8", errors="ignore")[:MAX_EXTRACTED_TEXT_CHARS]

def chunk_text(text: str, size: int = CHUNK_SIZE) -> List[str]:
    """
    Sentence-based chunking for better semantic integrity.
    Falls back to raw character chunking.
    Capped at MAX_CHUNKS.
    """
    text = text.strip()
    if not text:
        return []

    # Sentence split based on punctuation
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue

        if len(current) + len(s) + 1 <= size:
            if current:
                current += " " + s
            else:
                current = s
        else:
            if current.strip():
                chunks.append(current.strip())
                if len(chunks) >= MAX_CHUNKS:
                    return chunks
            current = s

    if current.strip() and len(chunks) < MAX_CHUNKS:
        chunks.append(current.strip())

    if not chunks:
        for i in range(0, len(text), size):
            chunk = text[i: i + size].strip()
            if chunk:
                chunks.append(chunk)
                if len(chunks) >= MAX_CHUNKS:
                    break

    return chunks
