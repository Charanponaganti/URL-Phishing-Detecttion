"""
PhishGuard — Scan Router
POST /api/scan — Full URL threat analysis pipeline.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.schemas import ScanRequest, ScanResponse
from app.models.database import save_scan
from app.services.ml_predictor import predict_url
from app.services.cti_lookup import perform_cti_lookup
from app.services.dns_whois import perform_dns_whois
from app.services.obfuscation import analyze_obfuscation
from app.services.typosquatting import detect_typosquatting

router = APIRouter(prefix="/api", tags=["scan"])


def _compute_aggregate_risk(ml_result: dict, cti: dict, dns_whois: dict,
                             obfuscation: dict, typosquat: dict) -> tuple[int, str]:
    """Compute aggregate risk score (0-100) and risk level."""
    score = ml_result["risk_score"]

    # CTI adjustments
    vt = cti.get("virustotal") or {}
    if vt.get("status") == "found":
        malicious = vt.get("malicious", 0)
        if malicious > 5:
            score = min(score + 30, 100)
        elif malicious > 0:
            score = min(score + 15, 100)

    uh = cti.get("urlhaus") or {}
    if uh.get("status") == "found":
        score = min(score + 25, 100)

    # DNS/WHOIS adjustments
    if dns_whois.get("newly_registered"):
        score = min(score + 15, 100)

    # Obfuscation adjustments
    techniques = obfuscation.get("techniques_detected", [])
    score = min(score + len(techniques) * 5, 100)

    # Typosquatting adjustments
    if typosquat.get("is_typosquatting"):
        best_sim = 0
        for d in typosquat.get("similar_domains", []):
            best_sim = max(best_sim, d.get("similarity", 0))
        if best_sim > 0.9:
            score = min(score + 20, 100)
        elif best_sim > 0.8:
            score = min(score + 10, 100)

    # Determine risk level
    if score >= 70:
        level = "malicious"
    elif score >= 40:
        level = "suspicious"
    else:
        level = "safe"

    return score, level


def _generate_summary(ml: dict, cti: dict, obfuscation: dict,
                       typosquat: dict, risk_level: str) -> str:
    """Generate a human-readable threat summary."""
    parts = []

    if risk_level == "malicious":
        parts.append("HIGH RISK: This URL is likely malicious.")
    elif risk_level == "suspicious":
        parts.append("SUSPICIOUS: This URL shows concerning indicators.")
    else:
        parts.append("LOW RISK: This URL appears safe.")

    parts.append(f"ML model classifies as {ml['label']} ({ml['confidence']:.1%} confidence).")

    vt = cti.get("virustotal") or {}
    if vt.get("status") == "found" and vt.get("malicious", 0) > 0:
        parts.append(f"VirusTotal: {vt['malicious']} engines flagged this URL.")

    uh = cti.get("urlhaus") or {}
    if uh.get("status") == "found":
        parts.append(f"URLhaus: Known threat — {uh.get('threat', 'malware')}.")

    techs = obfuscation.get("techniques_detected", [])
    if techs:
        parts.append(f"Obfuscation detected: {', '.join(techs)}.")

    if typosquat.get("is_typosquatting"):
        parts.append(f"Possible typosquatting of: {typosquat['closest_match']}.")

    return " ".join(parts)


@router.post("/scan", response_model=ScanResponse)
async def scan_url(request: ScanRequest):
    """Analyze a URL through the full PhishGuard pipeline."""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    scan_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()

    # 1. Obfuscation analysis
    obfuscation = analyze_obfuscation(url)

    # Use decoded URL for further analysis
    analysis_url = obfuscation["decoded_url"]

    # 2. ML prediction
    ml_result = predict_url(analysis_url)

    # 3. CTI lookups
    cti_result = perform_cti_lookup(url)

    # 4. DNS/WHOIS
    dns_whois = perform_dns_whois(analysis_url)

    # 5. Typosquatting
    typosquat = detect_typosquatting(analysis_url)

    # 6. Aggregate risk
    risk_score, risk_level = _compute_aggregate_risk(
        ml_result, cti_result, dns_whois, obfuscation, typosquat
    )

    # 7. Summary
    summary = _generate_summary(ml_result, cti_result, obfuscation, typosquat, risk_level)

    # Build response
    result = {
        "scan_id": scan_id,
        "url": url,
        "timestamp": timestamp,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "ml_prediction": ml_result,
        "cti_result": cti_result,
        "dns_whois": dns_whois,
        "obfuscation": obfuscation,
        "typosquatting": typosquat,
        "summary": summary,
    }

    # 8. Save to database
    try:
        save_scan(result)
    except Exception as e:
        print(f"[PhishGuard] Warning: Failed to save scan: {e}")

    return ScanResponse(**result)
