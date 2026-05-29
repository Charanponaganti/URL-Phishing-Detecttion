"""
PhishGuard — DNS & WHOIS Forensics Service
Performs passive DNS resolution and WHOIS lookups for domain intelligence.
"""

import socket
from datetime import datetime, timezone
from urllib.parse import urlparse

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False


def _extract_domain(url: str) -> str:
    """Extract domain from URL."""
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    return parsed.hostname or ""


def lookup_dns(domain: str) -> dict:
    """Resolve DNS records for a domain."""
    records = {}

    if not DNS_AVAILABLE:
        return {"error": "dnspython not installed"}

    record_types = ["A", "AAAA", "MX", "NS", "TXT"]

    for rtype in record_types:
        try:
            answers = dns.resolver.resolve(domain, rtype)
            records[rtype] = [str(r) for r in answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN,
                dns.resolver.NoNameservers, dns.resolver.Timeout):
            pass
        except Exception:
            pass

    # Reverse DNS for the first A record
    if "A" in records and records["A"]:
        try:
            ip = records["A"][0]
            reverse = socket.gethostbyaddr(ip)
            records["PTR"] = [reverse[0]]
        except Exception:
            pass

    return records


def lookup_whois(domain: str) -> dict:
    """Perform WHOIS lookup for domain registration information."""
    if not WHOIS_AVAILABLE:
        return {"error": "python-whois not installed"}

    try:
        w = whois.whois(domain)

        # Parse creation date
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        # Parse expiration date
        expiration_date = w.expiration_date
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]

        # Calculate domain age
        domain_age_days = None
        newly_registered = False
        if creation_date:
            try:
                if isinstance(creation_date, str):
                    from dateutil.parser import parse
                    creation_date = parse(creation_date)
                age = datetime.now() - creation_date
                domain_age_days = age.days
                newly_registered = domain_age_days < 30  # Less than 30 days = suspicious
            except Exception:
                pass

        return {
            "registrar": str(w.registrar) if w.registrar else None,
            "creation_date": str(creation_date) if creation_date else None,
            "expiration_date": str(expiration_date) if expiration_date else None,
            "name_servers": w.name_servers if w.name_servers else [],
            "org": str(w.org) if w.org else None,
            "country": str(w.country) if w.country else None,
            "domain_age_days": domain_age_days,
            "newly_registered": newly_registered,
        }

    except Exception as e:
        return {"error": f"WHOIS lookup failed: {str(e)}"}


def perform_dns_whois(url: str) -> dict:
    """Run full DNS + WHOIS analysis."""
    domain = _extract_domain(url)
    if not domain:
        return {
            "dns_records": {},
            "whois_info": {},
            "domain_age_days": None,
            "registrar": None,
            "newly_registered": False,
        }

    dns_records = lookup_dns(domain)
    whois_info = lookup_whois(domain)

    return {
        "dns_records": dns_records,
        "whois_info": whois_info,
        "domain_age_days": whois_info.get("domain_age_days"),
        "registrar": whois_info.get("registrar"),
        "newly_registered": whois_info.get("newly_registered", False),
    }
