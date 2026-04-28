import asyncio
import io
import logging
from typing import List
import aiohttp
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

from config import HTTP_TIMEOUT_SECONDS, MAX_PAGE_TEXT_CHARS
from security.ssrf import is_safe_url

logger = logging.getLogger("plagiarism-checker.services.scraper")

async def fetch_page_async(url: str, session: aiohttp.ClientSession) -> str:
    """
    Async fetch of page content, including PDF extraction.
    With SSRF checks and content-length limits.
    """
    if not is_safe_url(url):
        logger.warning("Blocked unsafe URL: %s", url)
        return ""

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT_SECONDS)
        # allow_redirects=False to prevent redirect-based SSRF rebinding to localhost
        async with session.get(url, headers=headers, timeout=timeout, allow_redirects=False) as response:
            if response.status != 200:
                return ""

            content_type = (response.headers.get("Content-Type") or "").lower()
            content_length = response.headers.get("Content-Length")

            if content_length is not None:
                try:
                    if int(content_length) > 10 * 1024 * 1024:  # 10 MB limit
                        logger.info("Skipping large response from %s", url)
                        return ""
                except ValueError:
                    pass

            # PDF Handling
            if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                try:
                    pdf_bytes = await response.read()
                    reader = PdfReader(io.BytesIO(pdf_bytes))

                    text_parts: List[str] = []
                    # Limit pages
                    for page_idx in range(min(len(reader.pages), 50)):
                        try:
                            t = reader.pages[page_idx].extract_text() or ""
                            if t.strip():
                                text_parts.append(t)
                        except Exception as e:
                            logger.warning("Error extracting PDF page from %s: %s", url, e)

                    full_text = "\n".join(text_parts)
                    return full_text[:MAX_PAGE_TEXT_CHARS]
                except Exception as e:
                    logger.warning("Error extracting PDF from %s: %s", url, e)
                    return ""

            # HTML / Text Handling
            if "text/html" in content_type or "text/plain" in content_type:
                try:
                    raw = await response.text(errors="ignore")
                except TypeError:
                    raw = await response.text()

                soup = BeautifulSoup(raw, "html.parser")

                for tag in soup(["script", "style", "meta", "noscript", "header", "footer", "nav"]):
                    tag.extract()

                text = soup.get_text(separator=" ", strip=True)
                return text[:MAX_PAGE_TEXT_CHARS]

            return ""

    except asyncio.TimeoutError:
        logger.info("Timeout fetching URL %s", url)
        return ""
    except Exception as e:
        logger.warning("Error fetching %s: %s", url, e)
        return ""
