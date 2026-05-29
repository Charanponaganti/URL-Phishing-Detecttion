"""
PhishGuard — Report Export Router
Export scan data as CSV or JSON IoC reports.
"""

import csv
import io
from datetime import datetime
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.models.database import get_all_scans

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/export")
async def export_report(format: str = Query("json", enum=["json", "csv"])):
    """Export all scan data as JSON or CSV."""
    scans = get_all_scans()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "scan_id", "url", "timestamp", "risk_score", "risk_level",
            "ml_label", "ml_confidence", "vt_malicious", "urlhaus_status",
            "domain_age_days", "is_typosquatting", "obfuscation_techniques"
        ])
        for s in scans:
            ml = s.get("ml_prediction", {})
            cti = s.get("cti_result", {})
            vt = cti.get("virustotal") or {}
            uh = cti.get("urlhaus") or {}
            dns = s.get("dns_whois", {})
            typo = s.get("typosquatting", {})
            obf = s.get("obfuscation", {})

            writer.writerow([
                s.get("scan_id", ""),
                s.get("url", ""),
                s.get("timestamp", ""),
                s.get("risk_score", 0),
                s.get("risk_level", ""),
                ml.get("label", ""),
                ml.get("confidence", 0),
                vt.get("malicious", "N/A"),
                uh.get("status", "N/A"),
                dns.get("domain_age_days", "N/A"),
                typo.get("is_typosquatting", False),
                "|".join(obf.get("techniques_detected", [])),
            ])

        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=phishguard_ioc_report_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    else:
        return {
            "format": "json",
            "exported_at": datetime.now().isoformat(),
            "total_records": len(scans),
            "data": scans,
        }
