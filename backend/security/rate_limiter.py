from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Limiter with IP address as key
limiter = Limiter(key_func=get_remote_address)
