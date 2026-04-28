from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import API_KEYS

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if not API_KEYS:
        # If no keys configured, allow (for easy development, though warn in logs)
        return "development_mode"
        
    if api_key_header in API_KEYS:
        return api_key_header
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate API KEY",
    )
