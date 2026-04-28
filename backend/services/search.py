import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from collections import OrderedDict
import aiohttp

from config import SERPAPI_KEY, MAX_RESULTS_PER_CHUNK, HTTP_TIMEOUT_SECONDS, MAX_SEARCH_CACHE_SIZE
from security.ssrf import is_safe_url

logger = logging.getLogger("plagiarism-checker.services.search")

class SearchCache:
    """Thread-safe search cache to replace global mutable state."""
    def __init__(self, max_size: int = MAX_SEARCH_CACHE_SIZE):
        self._cache: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        async with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key]
            return None

    async def set(self, key: str, value: List[Dict[str, Any]]):
        async with self._lock:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
            self._cache[key] = value
            self._cache.move_to_end(key)

search_cache = SearchCache()

def build_search_query(chunk: str) -> str:
    """
    Build a cleaner search query by extracting important words.
    Removes punctuation, short words, and common stopwords.
    This also ensures we don't send large raw text chunks to third-party APIs.
    """
    cleaned = re.sub(r"[^\w\s]", " ", chunk)
    words = cleaned.split()

    stopwords = {
        "the", "is", "are", "was", "were", "and", "or", "in", "of",
        "to", "for", "a", "an", "on", "by", "with", "as", "at", "from",
    }

    keywords = [w for w in words if len(w) > 3 and w.lower() not in stopwords]

    if not keywords:
        return chunk[:120]

    return " ".join(keywords[:6])

async def serp_search_async(
    query: str,
    session: aiohttp.ClientSession,
    lang: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Async Google search using SerpAPI.
    """
    if not SERPAPI_KEY:
        logger.warning("SERPAPI_KEY not configured. Skipping web search.")
        return []

    cache_key = f"{lang or 'any'}::{query}"
    cached_result = await search_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": MAX_RESULTS_PER_CHUNK,
    }

    if lang and len(lang) == 2:
        params["hl"] = lang
        params["lr"] = f"lang_{lang}"

    try:
        async with session.get(url, params=params, timeout=HTTP_TIMEOUT_SECONDS) as response:
            if response.status in {403, 429}:
                logger.warning("SerpAPI quota/auth issue (status %s).", response.status)
                return []

            if response.status != 200:
                logger.warning("SerpAPI returned non-200 status: %s", response.status)
                return []

            data = await response.json()
            results = data.get("organic_results", []) or []

            cleaned: List[Dict[str, Any]] = []
            for result in results[:MAX_RESULTS_PER_CHUNK]:
                link = result.get("link")
                snippet = result.get("snippet", "") or ""
                # Validate URL before trusting it
                if link and is_safe_url(link):
                    cleaned.append({"url": link, "snippet": snippet})

            await search_cache.set(cache_key, cleaned)
            return cleaned

    except asyncio.TimeoutError:
        logger.warning("SerpAPI request timed out for query: %s", query)
        return []
    except Exception as e:
        logger.exception("Error during SerpAPI search: %s", e)
        return []
