# PlagiarismAI Threat Model Countermeasures Checklist

This checklist cross-references the vulnerabilities and countermeasures identified in the **PlagiarismAI Threat Modeling Report** against the actual implementations in the refactored codebase.

## Authentication & Access Control

- [x] **V-01: No Authentication on `/check` (CWE-306)**
  - *Report Recommendation:* Implement API key or JWT bearer token authentication using FastAPI Dependencies.
  - *Implementation:* Implemented `APIKeyHeader` in `backend/security/auth.py`. Integrated via `Depends(get_api_key)` in `main.py`. The `X-API-Key` header is now strictly required.

- [x] **V-03: Wildcard CORS (CWE-942)**
  - *Report Recommendation:* Restrict CORS to specific frontend domains.
  - *Implementation:* `CORSMiddleware` in `main.py` now uses `ALLOWED_ORIGINS` from `config.py` instead of wildcard `["*"]`.

## Transport & Network Security

- [x] **V-02: SSL Disabled (`ssl=False`) (CWE-295)**
  - *Report Recommendation:* Remove `ssl=False`; use `ssl.create_default_context()`.
  - *Implementation:* Enforced TLS validation across outbound connections. `aiohttp.TCPConnector` now uses `ssl.create_default_context()` in `main.py` and `scraper.py`.

- [x] **V-05: SSRF (Metadata Bypass) (CWE-918)**
  - *Report Recommendation:* Block `169.254.x.x`, use DNS resolution to block private IP ranges, disable redirects.
  - *Implementation:* Implemented comprehensive `is_safe_url` in `backend/security/ssrf.py`. It performs DNS resolution, blocks private/loopback/cloud-metadata IPs, and prevents DNS rebinding. Redirects are disabled in `aiohttp`.

## Denial of Service Protections

- [x] **V-04: No Rate Limiting (CWE-770)**
  - *Report Recommendation:* Add SlowAPI with per-IP rate limits.
  - *Implementation:* Integrated `slowapi` in `backend/security/rate_limiter.py`. Endpoints are throttled dynamically (e.g., 5 req/min for quick scans, 1 req/min for deep scans) in `main.py`.

- [x] **V-06: Zip Bomb / DOCX Decompression (CWE-409)**
  - *Report Recommendation:* Add raw text limits after extraction.
  - *Implementation:* `main.py` enforces a `MAX_FILE_SIZE_BYTES` limit. Post-extraction bounds and maximum chunk limits are enforced in `backend/services/text_extraction.py`.

- [x] **V-07: ReDoS in Citation Regex (CWE-1333)**
  - *Report Recommendation:* Use `re2` or set timeouts; simplify patterns.
  - *Implementation:* Handled via optimized/pre-compiled safe regex patterns in `backend/services/citation.py` preventing catastrophic backtracking.

- [x] **V-12: No Text Input Length Limit (CWE-400)**
  - *Report Recommendation:* Add explicit length constraints.
  - *Implementation:* Added `len(raw_text) > MAX_TEXT_INPUT_CHARS` checks in `main.py` preventing massive payload submissions.

## Data Security & Input Validation

- [x] **V-08: XSS via `matched_content` (CWE-79)**
  - *Report Recommendation:* Sanitise `matched_content` server-side with `bleach`; enforce strict CSP on frontend.
  - *Implementation:* Integrated `bleach` via `sanitize_html` in `backend/security/sanitizer.py`. All outbound HTML matching snippets are stripped before returning to the frontend. Added CSP headers to `index.html`.

- [x] **V-10: No Security Headers (Frontend) (CWE-693)**
  - *Report Recommendation:* Add HSTS, X-Frame-Options, CSP, etc.
  - *Implementation:* Added `SecurityHeadersMiddleware` in `backend/security/headers.py` (HSTS, nosniff, DENY framing).

- [ ] **V-11: Document Privacy via SerpAPI Queries (CWE-359)**
  - *Report Recommendation:* Anonymise queries; use hash-based deduplication.
  - *Implementation:* Chunk sizes are limited, minimizing the context sent to SerpAPI. *Note: Advanced anonymization (e.g., local TF-IDF keyword extraction) may be partially handled or deferred depending on chunk construction strategy.*

- [x] **V-13: Error Message Leakage (CWE-209)**
  - *Report Recommendation:* Global exception handler returning generic 500 messages; internal logging.
  - *Implementation:* `main.py` wraps critical operations in `try-except` blocks, logging the full stack trace securely via `logger.exception()` and raising generic `HTTPException(status_code=500)` details to the user, preventing system data leakage.

## System Architecture & Supply Chain

- [x] **V-09: Global Mutable State (CWE-362)**
  - *Report Recommendation:* Use `asyncio.Lock` for `SEARCH_CACHE` writes.
  - *Implementation:* Implemented thread-safe caching using `asyncio.Lock` in `backend/services/search.py`, eliminating race conditions across concurrent async requests.

- [x] **T-REP-1 & T-REP-2: No Audit Trail / Request Attribution**
  - *Report Recommendation:* Implement structured JSON logging capturing request IDs, IPs, and scan modes.
  - *Implementation:* Created `AuditLoggingMiddleware` in `backend/middleware/logging_middleware.py` which structures traceability logs efficiently.

- [x] **V-14: Dependency Vulnerabilities**
  - *Report Recommendation:* Pin versions in `requirements.txt`.
  - *Implementation:* Dependencies updated and safely pinned in `backend/requirements.txt` to mitigate supply chain risks.
