# PlagiarismAI Security Hardening — Implementation Plan

Transform the insecure AI plagiarism checker into a production-ready, OWASP-compliant system.

## Confirmed Vulnerabilities (from Threat Model)

| # | Vulnerability | Severity | Fix |
| --- | --- | --- | --- |
| 1 | No auth on `/check` | CRITICAL | API key middleware |
| 2 | `ssl=False` in aiohttp | CRITICAL | `ssl.create_default_context()` |
| 3 | No rate limiting | HIGH | slowapi (5/min quick, 1/min deep) |
| 4 | SSRF (169.254.x, private IPs) | CRITICAL | DNS resolution + IP block |
| 5 | CORS wildcard `*` | HIGH | Restrict to frontend origin |
| 6 | Zip bomb (DOCX/PDF) | HIGH | File size + extracted text limits |
| 7 | No input size limit | HIGH | 50k char text, 500k extracted, 500 chunks |
| 8 | ReDoS via regex | MEDIUM | Safe patterns (no catastrophic backtracking) |
| 9 | Global mutable state | MEDIUM | Class-based cache with asyncio.Lock |
| 10 | XSS via `matched_content` | HIGH | bleach.clean() server-side |
| 11 | No security headers | HIGH | CSP, HSTS, X-Frame-Options middleware |
| 12 | No logging/audit | MEDIUM | Structured JSON logging with request ID |
| 13 | Sensitive data to SerpAPI | MEDIUM | Keyword extraction only (already exists, validate) |
| 14 | Unpinned dependencies | MEDIUM | Pin all versions |
| 15 | No timeouts/concurrency | HIGH | aiohttp + model timeouts |

---

## Proposed Changes

### Backend — Refactored Architecture

The monolithic `main.py` (931 lines) will be refactored into a clean layered architecture:

```text
backend/
├── main.py                    # FastAPI app entry point (slim)
├── config.py                  # Configuration & constants
├── security/
│   ├── __init__.py
│   ├── auth.py                # API key authentication
│   ├── rate_limiter.py        # Rate limiting setup
│   ├── ssrf.py                # SSRF protection (DNS resolution)
│   ├── headers.py             # Security headers middleware
│   └── sanitizer.py           # Output sanitization (bleach)
├── services/
│   ├── __init__.py
│   ├── text_extraction.py     # PDF/DOCX/TXT extraction (with limits)
│   ├── search.py              # SerpAPI with thread-safe cache
│   ├── scraper.py             # Web page fetching (SSL enforced)
│   ├── similarity.py          # ML model + similarity computation
│   └── citation.py            # Citation detection (safe regex)
├── middleware/
│   ├── __init__.py
│   └── logging_middleware.py  # Structured audit logging
├── requirements.txt           # Pinned versions
└── .env.example               # Environment template
```

---

### Component 1: Configuration (`config.py`)

#### [NEW] [config.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/config.py)

- Centralize all constants and env vars
- Add new security-related config: `ALLOWED_ORIGINS`, `API_KEYS`, `MAX_TEXT_INPUT_CHARS=50000`, `MAX_EXTRACTED_TEXT_CHARS=500000`, `MAX_CHUNKS=500`
- Load from `.env` with validation

---

### Component 2: Authentication (`security/auth.py`)

#### [NEW] [auth.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/security/auth.py)

- API key-based authentication via `X-API-Key` header
- Keys loaded from `.env` (`API_KEYS` comma-separated)
- FastAPI dependency injection for protected routes
- `/health` remains public, `/check` requires auth

---

### Component 3: Rate Limiting (`security/rate_limiter.py`)

#### [NEW] [rate_limiter.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/security/rate_limiter.py)

- `slowapi` integration
- Quick scan: **5 requests/minute** per IP
- Deep scan: **1 request/minute** per IP
- Custom error handler returning 429

---

### Component 4: SSRF Protection (`security/ssrf.py`)

#### [NEW] [ssrf.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/security/ssrf.py)

- **DNS resolution before connection** — resolve hostname to IP, check IP against blocklist
- Block: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `::1`, `fe80::/10`, `fc00::/7`
- Only allow `http`/`https` schemes
- Disable redirects on aiohttp requests
- Validate URLs from SerpAPI results before fetching

---

### Component 5: Security Headers (`security/headers.py`)

#### [NEW] [headers.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/security/headers.py)

Add security headers middleware:

- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`

---

### Component 6: Output Sanitization (`security/sanitizer.py`)

#### [NEW] [sanitizer.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/security/sanitizer.py)

- Use `bleach.clean()` to strip ALL HTML from `matched_content`
- Applied to all output fields that contain user/web-sourced text

---

### Component 7: Text Extraction (`services/text_extraction.py`)

#### [NEW] [text_extraction.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/services/text_extraction.py)

- Extracted text capped at **500k characters**
- PDF page count limit (max 200 pages)
- DOCX paragraph count limit
- MIME type validation using `python-magic` (or `python-magic-bin` on Windows)
- Chunk count capped at **500**

---

### Component 8: Search Service (`services/search.py`)

#### [NEW] [search.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/services/search.py)

- Thread-safe `SearchCache` class using `asyncio.Lock` (no global mutable state)
- **Keyword extraction only** sent to SerpAPI (already uses `build_search_query` — validate no raw text leakage)
- SSL enforced: `ssl.create_default_context()`
- Request timeout: `aiohttp.ClientTimeout(total=15)`

---

### Component 9: Web Scraper (`services/scraper.py`)

#### [NEW] [scraper.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/services/scraper.py)

- SSL enforced via `ssl.create_default_context()`
- `allow_redirects=False` to prevent redirect-based SSRF
- SSRF check at DNS level before connecting
- Response size limit (10MB)
- Content-type validation

---

### Component 10: Citation Detection (`services/citation.py`)

#### [NEW] [citation.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/services/citation.py)

- All regex patterns audited for ReDoS safety
- Use `re.compile()` with pre-compiled patterns
- No catastrophic backtracking patterns

---

### Component 11: Similarity Engine (`services/similarity.py`)

#### [NEW] [similarity.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/services/similarity.py)

- Model inference timeout (30 seconds via `asyncio.wait_for`)
- Semaphore-bounded concurrency (max 2 concurrent embeddings)
- Model loaded at startup via lifespan

---

### Component 12: Audit Logging (`middleware/logging_middleware.py`)

#### [NEW] [logging_middleware.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/middleware/logging_middleware.py)

- Structured JSON logging
- Each request gets a unique `request_id` (UUID)
- Log: `request_id`, hashed IP (`sha256(ip)`), endpoint, method, response time, status code
- **No sensitive data** (no text content, no API keys in logs)

---

### Component 13: Main App (`main.py`)

#### [MODIFY] [main.py](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/main.py)

- Complete rewrite — slim orchestrator that imports from modules
- CORS restricted to `ALLOWED_ORIGINS` from config
- All middleware registered (security headers, logging, rate limiter)
- `/check` endpoint protected by API key dependency
- `/health` remains public
- Lifespan event for model loading
- Clean error handling

---

### Component 14: Dependencies

#### [MODIFY] [requirements.txt](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/requirements.txt)

All versions pinned. New additions:

- `slowapi` — rate limiting
- `bleach` — HTML sanitization
- `python-magic-bin` — MIME validation (Windows)

---

### Component 15: Environment Template

#### [NEW] [.env.example](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/.env.example)

```env
SERPAPI_KEY=your_serpapi_key_here
API_KEYS=your-secure-api-key-1,your-secure-api-key-2
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

#### [MODIFY] [.env](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/backend/.env)

- Add `API_KEYS` and `ALLOWED_ORIGINS`

---

### Frontend Changes

#### [MODIFY] [index.html](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/frontend/index.html)

- Add CSP meta tag
- Add security meta tags

#### [MODIFY] [App.jsx](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/frontend/src/App.jsx)

- Send `X-API-Key` header with requests
- Read key from `VITE_API_KEY` env var

#### [MODIFY] [Results.jsx](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/frontend/src/components/Results.jsx)

- Verify no `dangerouslySetInnerHTML` usage (✅ confirmed clean)
- Add client-side text escaping as defense-in-depth

#### [MODIFY] [UploadSection.jsx](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/frontend/src/components/UploadSection.jsx)

- Add client-side text length validation (50k char limit)
- Add file size validation (5MB)

#### [MODIFY] [.env](file:///c:/Users/Home/Desktop/FAST-NUCES/Ayaan_23k-2084/Semester_5/CY3006%20Digital%20Forensics/Project/PlagiarismAI/frontend/.env)

- Add `VITE_API_KEY` variable

---

## User Review Required

> [!IMPORTANT]
> **API Keys**: The implementation uses a simple API key scheme (`X-API-Key` header). For a production SaaS, you'd want JWT + user management. API key is appropriate for this academic project scope. Confirm this is acceptable.
>
> [!IMPORTANT]
> **python-magic on Windows**: The `python-magic-bin` package bundles libmagic for Windows. This is the simplest approach but adds ~5MB. Alternative: skip MIME validation on Windows dev, enable in prod (Linux). Which do you prefer?
>
> [!WARNING]
> **CORS Origins**: Currently set to `http://localhost:5173`. You'll need to update `ALLOWED_ORIGINS` in `.env` when deploying to production (e.g., your Render frontend URL).

---

## Verification Plan

### Automated Tests

1. `pip install -r requirements.txt` — verify all deps install
2. `uvicorn main:app --host 127.0.0.1 --port 9002` — verify server starts
3. Test auth: `curl http://localhost:9002/check` → expect `403`
4. Test rate limit: rapid-fire requests → expect `429`
5. Test health: `curl http://localhost:9002/health` → expect `200`
6. Frontend: `npm run dev` → verify UI loads and connects

### Manual Verification

- Submit a plagiarism check through the UI with API key configured
- Verify security headers in browser DevTools (Network tab)
- Verify structured logs in terminal output
