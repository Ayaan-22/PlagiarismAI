import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

# API Keys
SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")
API_KEYS: List[str] = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

# CORS
ALLOWED_ORIGINS: List[str] = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]

# Limits
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
MAX_TEXT_INPUT_CHARS: int = 50_000
MAX_EXTRACTED_TEXT_CHARS: int = 500_000
MAX_CHUNKS: int = 500
CHUNK_SIZE: int = 700
MAX_PAGE_CHUNKS_PER_SOURCE: int = 20
MIN_PAGE_CHUNK_LENGTH: int = 50

# Tuned thresholds
SIMILARITY_THRESHOLD: float = 45.0
HIGH_SIMILARITY_THRESHOLD: float = 65.0

MAX_CHUNKS_QUICK_SCAN: int = 15
HTTP_TIMEOUT_SECONDS: int = 10
MAX_CONCURRENT_REQUESTS: int = 5
MAX_RESULTS_PER_CHUNK: int = 5
MAX_MATCHES_RETURNED: int = 20
MAX_PAGE_TEXT_CHARS: int = 35_000
EMBEDDING_MAX_CONCURRENCY: int = 2
MAX_SEARCH_CACHE_SIZE: int = 500
