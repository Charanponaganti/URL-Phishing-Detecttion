"""
PhishGuard — Cyber Threat Intelligence Lookup Service
Queries VirusTotal and URLhaus for threat data.
Degrades gracefully if APIs are unavailable.
"""

import requests
import hashlib
import base64
from urllib.parse import quote

from app.config import settings

VT_API_BASE = "https://www.virustotal.com/api/v3"
URLHAUS_API_BASE = "https://urlhaus-api.abuse.ch/v1"

TIMEOUT = 10  # seconds


def lookup_virustotal(url: str) -> dict | None:
    """
    Query VirusTotal API v3 for URL reputation.
    Returns detection stats or None if unavailable.
    """
    api_key = settings.virustotal_api_key
    if not api_key:
        return {"status": "no_api_key", "message": "VirusTotal API key not configured"}

    try:
        # VT uses base64-encoded URL (without padding) as the identifier
        url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")

        headers = {"x-apikey": api_key}

        # First, try to get existing analysis
        resp = requests.get(
            f"{VT_API_BASE}/urls/{url_id}",
            headers=headers,
            timeout=TIMEOUT
        )

        if resp.status_code == 200:
            data = resp.json().get("data", {}).get("attributes", {})
            stats = data.get("last_analysis_stats", {})
            return {
                "status": "found",
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
                "undetected": stats.get("undetected", 0),
                "total_engines": sum(stats.values()) if stats else 0,
                "reputation": data.get("reputation", 0),
                "categories": data.get("categories", {}),
                "last_analysis_date": data.get("last_analysis_date"),
            }
        elif resp.status_code == 404:
            # URL not previously scanned — submit for scanning
            resp2 = requests.post(
                f"{VT_API_BASE}/urls",
                headers=headers,
                data={"url": url},
                timeout=TIMEOUT
            )
            if resp2.status_code == 200:
                return {"status": "submitted", "message": "URL submitted for analysis"}
            return {"status": "not_found", "message": "URL not in VirusTotal database"}
        else:
            return {"status": "error", "message": f"API returned {resp.status_code}"}

    except requests.exceptions.Timeout:
        return {"status": "timeout", "message": "VirusTotal API timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def lookup_urlhaus(url: str) -> dict | None:
    """
    Query URLhaus (abuse.ch) for known malicious URL data.
    Free API, no key required.
    """
    try:
        resp = requests.post(
            f"{URLHAUS_API_BASE}/url/",
            data={"url": url},
            timeout=TIMEOUT
        )

        if resp.status_code == 200:
            data = resp.json()
            query_status = data.get("query_status", "")

            if query_status == "ok":
                return {
                    "status": "found",
                    "threat": data.get("threat", "unknown"),
                    "url_status": data.get("url_status", "unknown"),
                    "date_added": data.get("date_added"),
                    "tags": data.get("tags", []),
                    "reporter": data.get("reporter"),
                    "payloads": [
                        {
                            "filename": p.get("filename"),
                            "file_type": p.get("file_type"),
                            "signature": p.get("signature"),
                        }
                        for p in (data.get("payloads") or [])[:3]
                    ],
                }
            elif query_status == "no_results":
                return {"status": "clean", "message": "URL not found in URLhaus database"}
            else:
                return {"status": "unknown", "message": query_status}

        return {"status": "error", "message": f"API returned {resp.status_code}"}

    except requests.exceptions.Timeout:
        return {"status": "timeout", "message": "URLhaus API timed out"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def perform_cti_lookup(url: str) -> dict:
    """
    Run all CTI lookups and aggregate results.
    """
    vt = lookup_virustotal(url)
    uh = lookup_urlhaus(url)

    sources_checked = 0
    if vt and vt.get("status") not in ("error", "timeout", "no_api_key"):
        sources_checked += 1
    if uh and uh.get("status") not in ("error", "timeout"):
        sources_checked += 1

    return {
        "virustotal": vt,
        "urlhaus": uh,
        "sources_checked": sources_checked,
    }
