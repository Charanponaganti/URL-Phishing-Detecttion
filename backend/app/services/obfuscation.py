"""
PhishGuard — URL Obfuscation Detection & Decoding Service
Detects and decodes various URL obfuscation techniques.
"""

import re
import struct
import socket
from urllib.parse import urlparse, unquote

_SHORTENERS = {
    "bit.ly", "goo.gl", "tinyurl.com", "ow.ly", "t.co",
    "buff.ly", "rebrand.ly", "cutt.ly", "is.gd", "bl.ink",
    "short.io", "tiny.cc", "lc.chat", "soo.gd", "s2r.co",
    "rb.gy", "shorturl.at", "v.gd", "clck.ru",
}


def _decode_percent_encoding(url):
    decoded = unquote(url)
    return decoded, decoded != url


def _decode_punycode(domain):
    try:
        if domain.startswith("xn--") or ".xn--" in domain:
            decoded = domain.encode("ascii").decode("idna")
            return decoded, True
    except Exception:
        pass
    return domain, False


def _decode_hex_ip(url):
    if not url.startswith(("http://", "https://")):
        url_check = "http://" + url
    else:
        url_check = url
    parsed = urlparse(url_check)
    host = parsed.hostname or ""

    hex_match = re.match(r"^0x([0-9a-fA-F]+)$", host)
    if hex_match:
        try:
            ip_int = int(hex_match.group(1), 16)
            ip = socket.inet_ntoa(struct.pack("!I", ip_int))
            return url.replace(host, ip), True
        except Exception:
            pass

    dec_match = re.match(r"^(\d{8,10})$", host)
    if dec_match:
        try:
            ip_int = int(dec_match.group(1))
            ip = socket.inet_ntoa(struct.pack("!I", ip_int))
            return url.replace(host, ip), True
        except Exception:
            pass

    return url, False


def _detect_at_sign_trick(url):
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    return "@" in (parsed.netloc or "")


def _is_shortened(url):
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    return domain.lower() in _SHORTENERS


def analyze_obfuscation(url):
    """Analyze a URL for obfuscation techniques."""
    techniques = []
    decoded_url = url
    original = url

    # 1. Percent encoding
    decoded, changed = _decode_percent_encoding(decoded_url)
    if changed:
        techniques.append("percent_encoding")
        decoded_url = decoded

    # 2. Double percent encoding
    decoded2, changed2 = _decode_percent_encoding(decoded_url)
    if changed2:
        techniques.append("double_percent_encoding")
        decoded_url = decoded2

    # 3. Punycode domain
    if not decoded_url.startswith(("http://", "https://")):
        check_url = "http://" + decoded_url
    else:
        check_url = decoded_url
    parsed = urlparse(check_url)
    domain = parsed.hostname or ""
    puny_decoded, puny_changed = _decode_punycode(domain)
    if puny_changed:
        techniques.append("punycode_domain")
        decoded_url = decoded_url.replace(domain, puny_decoded)

    # 4. Hex/Decimal IP
    hex_decoded, hex_changed = _decode_hex_ip(decoded_url)
    if hex_changed:
        techniques.append("ip_obfuscation")
        decoded_url = hex_decoded

    # 5. @ sign trick
    if _detect_at_sign_trick(decoded_url):
        techniques.append("at_sign_redirect")

    # 6. URL shortener
    is_short = _is_shortened(decoded_url)
    if is_short:
        techniques.append("url_shortener")

    # 7. Excessive subdomains
    if domain.count(".") > 3:
        techniques.append("excessive_subdomains")

    # 8. IP address as host
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain):
        techniques.append("ip_address_host")

    return {
        "original_url": original,
        "decoded_url": decoded_url,
        "techniques_detected": techniques,
        "is_shortened": is_short,
        "resolved_url": None,
    }
