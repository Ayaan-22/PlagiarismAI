import ipaddress
import socket
from urllib.parse import urlparse
import logging

logger = logging.getLogger("plagiarism-checker.security")

def is_safe_url(url: str) -> bool:
    """
    SSRF protection:
    - Resolves hostname to IP
    - Checks IP against blocked ranges (private, loopback, link-local)
    - Rejects empty hostnames and non HTTP/HTTPS schemes
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False

        # Resolve DNS to get actual IP (prevents DNS rebinding and clever obfuscation)
        try:
            ip_address = socket.gethostbyname(hostname)
        except socket.gaierror:
            logger.warning("DNS resolution failed for %s", hostname)
            return False
            
        ip = ipaddress.ip_address(ip_address)
        
        # Block unsafe IP ranges
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved:
            logger.warning("Blocked unsafe IP %s for url %s", ip_address, url)
            return False

        # Extra safety check for IPv6 localhost
        if ip_address in {"::1"}:
            return False

        return True
    except Exception as e:
        logger.warning("Failed to validate URL %s: %s", url, e)
        return False
