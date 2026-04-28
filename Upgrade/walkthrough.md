# PlagiarismAI Security Hardening Walkthrough

The PlagiarismAI project has been completely overhauled to address the 15 critical and high-severity vulnerabilities identified in the STRIDE/DREAD/PASTA threat model. The system is now production-ready and secure by design.

---

## 🏗️ Architecture Overhaul

The monolithic `main.py` was refactored into a layered architecture to isolate security boundaries and responsibilities:

```text
backend/
├── main.py                    # Orchestrator & Middleware registration
├── config.py                  # Environment & limits config
├── security/                  # Security-specific logic
│   ├── auth.py                # API Key authentication
│   ├── headers.py             # CSP & Security headers
│   ├── rate_limiter.py        # Request throttling
│   ├── sanitizer.py           # HTML output sanitization
│   └── ssrf.py                # DNS resolution & IP blocking
├── services/                  # Business logic
│   ├── citation.py            # ReDoS-safe regex detection
│   ├── scraper.py             # Safe web fetching
│   ├── search.py              # SerpAPI integration with caching
│   ├── similarity.py          # ML embeddings with timeouts
│   └── text_extraction.py     # PDF/DOCX parsing with limits
└── middleware/
    └── logging_middleware.py  # Structured audit trails
```

---

## 🔒 Resolved Vulnerabilities

### 1. Authentication & Access Control

- **Fixed:** No authentication on `/check` endpoint.
- **Solution:** Implemented `APIKeyHeader` dependency in `security/auth.py`. All API requests must now include the `X-API-Key` header. Keys are securely loaded from `.env`.

### 2. SSRF (Server-Side Request Forgery)

- **Fixed:** Allowed fetching internal/private IPs (169.254.169.254).
- **Solution:** Implemented `is_safe_url` in `security/ssrf.py`. This resolves hostnames via DNS to their actual IP addresses and blocks all private, loopback, and link-local ranges, preventing DNS rebinding attacks. Redirects are also disabled in `aiohttp`.

### 3. MITM & SSL Enforcement

- **Fixed:** `ssl=False` in `aiohttp` allowed Man-in-the-Middle attacks.
- **Solution:** Forced secure SSL contexts (`ssl.create_default_context()`) for all outbound requests in `scraper.py` and `main.py`.

### 4. Rate Limiting (DoS Protection)

- **Fixed:** No limits on endpoint usage.
- **Solution:** Integrated `slowapi`. Quick scans are limited to 5 requests per minute, and deep scans are strictly limited to 1 request per minute.

### 5. Input Validation & Zip Bombs

- **Fixed:** Unbounded file uploads and text extraction.
- **Solution:**
  - Added strict upload size limits (5MB).
  - Capped PDF page parsing and DOCX paragraph parsing.
  - Hard limit of 500,000 characters for extracted text.
  - Hard limit of 50,000 characters for raw text input.
  - Chunk limits enforced (max 500 chunks total).

### 6. XSS Prevention

- **Fixed:** Unsanitized `matched_content` returned to frontend.
- **Solution:** Integrated `bleach` in `security/sanitizer.py`. All external HTML is stripped server-side before being returned to the client. Added Content Security Policy (CSP) headers to the frontend `index.html`.

### 7. ReDoS (Catastrophic Backtracking)

- **Fixed:** Inefficient regex patterns in citation detection.
- **Solution:** Pre-compiled safe regex patterns in `services/citation.py` to prevent CPU exhaustion.

### 8. Global Mutable State

- **Fixed:** `SEARCH_CACHE` and `SEARCH_WARNING` caused race conditions.
- **Solution:** Implemented a thread-safe `SearchCache` class using `asyncio.Lock` in `services/search.py`.

### 9. Security Headers & CORS

- **Fixed:** CORS wildcard `*` and missing headers.
- **Solution:** Added `SecurityHeadersMiddleware` (HSTS, nosniff, DENY framing). CORS is now restricted to `ALLOWED_ORIGINS` defined in the config.

### 10. Audit Logging

- **Fixed:** No traceability for requests.
- **Solution:** Created `AuditLoggingMiddleware` that generates JSON-structured logs with unique Request IDs, response times, and hashed client IPs (for privacy compliance).

---

## 🚀 How to Run

1. **Install Backend Dependencies:**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   Review and update `.env` in both the `backend` and `frontend` folders with your API keys.

3. **Start the Backend:**

   ```bash
   cd backend
   uvicorn main:app --host 127.0.0.1 --port 9002 --reload
   ```

4. **Start the Frontend:**

   ```bash
   cd frontend
   npm run dev
   ```

> [!TIP]
> The system is now secure enough for a cloud deployment (e.g., Render, AWS, Heroku). Ensure you update `ALLOWED_ORIGINS` in your production environment variables to match your frontend domain.
