# Security Hardening Tasks

## Backend Dependencies & Config

- [x] Update `backend/requirements.txt`
- [x] Update `backend/.env` and `backend/.env.example`
- [x] Create `backend/config.py`

## Security Modules

- [x] Create `backend/security/auth.py` (API Key)
- [x] Create `backend/security/rate_limiter.py` (slowapi)
- [x] Create `backend/security/ssrf.py` (DNS resolution)
- [x] Create `backend/security/headers.py` (CSP, HSTS)
- [x] Create `backend/security/sanitizer.py` (bleach)

## Services Layer

- [x] Create `backend/services/text_extraction.py` (limits & MIME)
- [x] Create `backend/services/search.py` (SerpAPI & Cache)
- [x] Create `backend/services/scraper.py` (SSL, SSRF)
- [x] Create `backend/services/citation.py` (Regex)
- [x] Create `backend/services/similarity.py` (ML & Timeout)

## Middleware & Main

- [x] Create `backend/middleware/logging_middleware.py` (Structured JSON)
- [x] Rewrite `backend/main.py` (Orchestration)

## Frontend Security

- [x] Update frontend `index.html` (CSP Meta)
- [x] Update frontend `App.jsx` (API Key Header)
- [x] Update frontend `Results.jsx` (Escaping)
- [x] Update frontend `UploadSection.jsx` (Validation)
- [x] Update frontend `.env` (API Key)
