"""
PhishGuard — Typosquatting Detection Service
Detects domain names that are visually similar to popular legitimate domains.
"""

import re
from urllib.parse import urlparse

# Top popular domains to check against (subset of Tranco Top 1M)
_POPULAR_DOMAINS = [
    "google.com", "youtube.com", "facebook.com", "amazon.com", "twitter.com",
    "instagram.com", "linkedin.com", "microsoft.com", "apple.com", "netflix.com",
    "reddit.com", "github.com", "stackoverflow.com", "wikipedia.org", "yahoo.com",
    "paypal.com", "ebay.com", "dropbox.com", "chase.com", "bankofamerica.com",
    "wellsfargo.com", "citibank.com", "usbank.com", "capitalone.com",
    "americanexpress.com", "outlook.com", "office.com", "live.com",
    "spotify.com", "twitch.tv", "discord.com", "zoom.us", "slack.com",
    "salesforce.com", "adobe.com", "shopify.com", "stripe.com",
    "binance.com", "coinbase.com", "blockchain.com", "metamask.io",
]

# Homoglyph mapping for visual similarity
_HOMOGLYPHS = {
    'a': ['@', '4', 'à', 'á', 'â', 'ã', 'ä'],
    'b': ['d', '6', '8'],
    'c': ['(', '{', '<'],
    'e': ['3', 'è', 'é', 'ê', 'ë'],
    'g': ['9', 'q'],
    'i': ['1', 'l', '!', '|', 'í', 'ì'],
    'l': ['1', 'i', '|'],
    'o': ['0', 'ò', 'ó', 'ô', 'õ', 'ö'],
    's': ['5', '$'],
    't': ['7', '+'],
    'z': ['2'],
}


def _levenshtein(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            subs = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, subs))
        prev_row = curr_row

    return prev_row[-1]


def _visual_similarity(domain: str, target: str) -> float:
    """Score visual similarity considering homoglyphs (0.0 to 1.0)."""
    if domain == target:
        return 1.0
    edit_dist = _levenshtein(domain, target)
    max_len = max(len(domain), len(target))
    if max_len == 0:
        return 0.0
    base_sim = 1.0 - (edit_dist / max_len)

    # Bonus for homoglyph substitutions
    homoglyph_bonus = 0
    if len(domain) == len(target):
        for c1, c2 in zip(domain, target):
            if c1 != c2:
                if c2 in _HOMOGLYPHS.get(c1, []) or c1 in _HOMOGLYPHS.get(c2, []):
                    homoglyph_bonus += 0.05

    return min(base_sim + homoglyph_bonus, 1.0)


def _extract_domain(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    return (parsed.hostname or "").lower()


def detect_typosquatting(url: str, threshold: float = 0.75) -> dict:
    """
    Check if a URL's domain is suspiciously similar to known popular domains.
    """
    domain = _extract_domain(url)
    if not domain:
        return {"is_typosquatting": False, "similar_domains": [], "closest_match": None}

    # Remove www prefix
    check_domain = domain.lstrip("www.")

    # Exact match = not typosquatting
    if check_domain in _POPULAR_DOMAINS:
        return {"is_typosquatting": False, "similar_domains": [], "closest_match": None}

    similar = []
    for i, pop_domain in enumerate(_POPULAR_DOMAINS):
        sim = _visual_similarity(check_domain, pop_domain)
        if sim >= threshold and sim < 1.0:
            similar.append({
                "domain": pop_domain,
                "similarity": round(sim, 3),
                "rank": i + 1,
            })

    similar.sort(key=lambda x: x["similarity"], reverse=True)
    top_matches = similar[:5]

    return {
        "is_typosquatting": len(top_matches) > 0,
        "similar_domains": top_matches,
        "closest_match": top_matches[0]["domain"] if top_matches else None,
    }
