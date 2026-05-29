"""
PhishGuard — Feature Extractor Service
Stateless feature extraction for real-time URL analysis.
Refactored from the existing Traditional_ML feature extractor.
"""

import re
import math
import numpy as np
from urllib.parse import urlparse, unquote

FEATURE_NAMES = [
    "url_length", "domain_length", "path_length", "subdomain_count", "path_depth",
    "count_dots", "count_hyphens", "count_underscores", "count_slashes",
    "count_at", "count_question", "count_equals", "count_ampersand",
    "count_percent", "count_digits",
    "digit_ratio", "letter_ratio", "special_char_ratio",
    "url_entropy", "domain_entropy",
    "has_ip_address", "has_port", "has_https", "has_http",
    "has_at_symbol", "has_double_slash", "has_dash_in_domain", "is_shortened",
]

_SHORTENERS = {
    "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co",
    "buff.ly", "rebrand.ly", "cutt.ly", "is.gd", "bl.ink",
    "short.io", "tiny.cc", "lc.chat", "soo.gd", "s2r.co",
}


def _entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((v / n) * math.log2(v / n) for v in freq.values())


def extract_features(url: str) -> np.ndarray:
    """
    Extract 28 hand-crafted features from a single URL.
    Returns a 1D numpy array of shape (28,).
    """
    # Normalize: strip protocol for feature extraction
    clean = url.lower().strip()
    if clean.startswith("https://"):
        has_https = 1
        has_http = 0
        bare = clean[8:]
    elif clean.startswith("http://"):
        has_https = 0
        has_http = 1
        bare = clean[7:]
    else:
        has_https = 0
        has_http = 0
        bare = clean

    # Parse the URL
    parse_url = "http://" + bare
    parsed = urlparse(parse_url)

    domain = parsed.hostname or ""
    path = parsed.path or ""
    full = bare

    length = len(full)
    domain_len = len(domain)
    path_len = len(path)

    subdomain_count = max(domain.count(".") - 1, 0)
    path_depth = path.count("/")

    count_dots = full.count(".")
    count_hyphens = full.count("-")
    count_underscores = full.count("_")
    count_slashes = full.count("/")
    count_at = full.count("@")
    count_question = full.count("?")
    count_equals = full.count("=")
    count_ampersand = full.count("&")
    count_percent = full.count("%")
    count_digits = sum(c.isdigit() for c in full)

    digit_ratio = count_digits / length if length else 0
    letter_ratio = sum(c.isalpha() for c in full) / length if length else 0
    special_ratio = sum(not c.isalnum() for c in full) / length if length else 0

    url_entropy = _entropy(full)
    domain_entropy = _entropy(domain)

    has_ip = int(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain)))
    has_port = int(parsed.port is not None)
    has_at = int("@" in full)
    has_double_slash = int("//" in path)
    has_dash_domain = int("-" in domain)
    is_shortened = int(domain in _SHORTENERS)

    features = [
        length, domain_len, path_len, subdomain_count, path_depth,
        count_dots, count_hyphens, count_underscores, count_slashes,
        count_at, count_question, count_equals, count_ampersand,
        count_percent, count_digits,
        digit_ratio, letter_ratio, special_ratio,
        url_entropy, domain_entropy,
        has_ip, has_port, has_https, has_http, has_at,
        has_double_slash, has_dash_domain, is_shortened,
    ]

    return np.array(features, dtype=np.float32)


def get_feature_names() -> list[str]:
    return FEATURE_NAMES
