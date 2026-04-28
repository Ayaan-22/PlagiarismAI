import bleach

def sanitize_html(text: str) -> str:
    """
    Sanitizes HTML content to prevent XSS.
    Strips all HTML tags.
    """
    if not text:
        return ""
    return bleach.clean(text, tags=[], attributes={}, strip=True)
