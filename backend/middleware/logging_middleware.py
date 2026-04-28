import time
import uuid
import logging
import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Setup structured logger
logger = logging.getLogger("plagiarism-checker.audit")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}')
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Hash IP address
        client_ip = request.client.host if request.client else "unknown"
        hashed_ip = hashlib.sha256(client_ip.encode('utf-8')).hexdigest()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        log_data = (
            f'{{"request_id": "{request_id}", '
            f'"ip_hash": "{hashed_ip}", '
            f'"method": "{request.method}", '
            f'"url": "{request.url.path}", '
            f'"status": {response.status_code}, '
            f'"process_time_sec": {process_time:.4f}}}'
        )
        
        logger.info(log_data)
        
        return response
