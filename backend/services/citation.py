import re
from typing import Tuple, List

# Compiled regex patterns, simplified to prevent ReDoS (Catastrophic Backtracking)
CITATION_PATTERNS: List[re.Pattern] = [
    re.compile(r"\([A-Z][a-z]+,\s?\d{4}\)", re.IGNORECASE),          # (Smith, 2020)
    re.compile(r"\([A-Z][a-z]+\s\d{4}\)", re.IGNORECASE),            # (Smith 2020)
    re.compile(r"\[[0-9]{1,3}\]", re.IGNORECASE),                    # [1] / [12]
    re.compile(r"[A-Z][a-z]+\s\d{4},\s?\d+–\d+", re.IGNORECASE),     # Brown 1999, 17–19
    re.compile(r"\d+\s?[A-Z][a-z]+\s?\d{4}", re.IGNORECASE),         # 12 Smith 2020
    re.compile(r"\bet al\.\b", re.IGNORECASE),                       # et al.
    re.compile(r"\(\d{4}\)", re.IGNORECASE),                         # (2020)
]

def _infer_citation_style_from_pattern(pattern_str: str) -> str:
    if "[" in pattern_str and "]" in pattern_str:
        return "IEEE / Numeric"
    if "et al" in pattern_str.lower():
        return "Author + et al."
    if pattern_str == r"\d+\s?[A-Z][a-z]+\s?\d{4}":
        return "Footnote / Numeric"
    return "Author-Date (APA/MLA-like)"

def detect_citation(chunk: str) -> Tuple[bool, str]:
    if not chunk or len(chunk.strip()) < 20:
        return False, ""

    has_quotes = any(q in chunk for q in ['"', "“", "”", "'"])

    for pattern in CITATION_PATTERNS:
        if pattern.search(chunk):
            style = _infer_citation_style_from_pattern(pattern.pattern)
            if has_quotes:
                return True, f"Quoted + {style}"
            return True, style

    return False, ""
