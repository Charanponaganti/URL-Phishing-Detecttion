"""
PhishGuard — Pydantic Schemas
Request/response models for the API.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ─── Requests ───────────────────────────────────────────

class ScanRequest(BaseModel):
    url: str = Field(..., description="URL to analyze", examples=["https://example.com/login"])


# ─── Sub-models ─────────────────────────────────────────

class MLPrediction(BaseModel):
    label: str  # "phishing" or "legitimate"
    confidence: float  # 0.0 - 1.0
    risk_score: int  # 0 - 100
    feature_importances: dict[str, float] = {}


class CTIResult(BaseModel):
    virustotal: Optional[dict] = None
    urlhaus: Optional[dict] = None
    sources_checked: int = 0


class DNSWhoisResult(BaseModel):
    dns_records: dict = {}
    whois_info: dict = {}
    domain_age_days: Optional[int] = None
    registrar: Optional[str] = None
    newly_registered: bool = False


class ObfuscationResult(BaseModel):
    original_url: str
    decoded_url: str
    techniques_detected: list[str] = []
    is_shortened: bool = False
    resolved_url: Optional[str] = None


class TyposquattingResult(BaseModel):
    is_typosquatting: bool = False
    similar_domains: list[dict] = []  # [{domain, similarity, rank}]
    closest_match: Optional[str] = None


# ─── Response ───────────────────────────────────────────

class ScanResponse(BaseModel):
    scan_id: str
    url: str
    timestamp: str
    risk_score: int  # 0-100 aggregate
    risk_level: str  # "safe", "suspicious", "malicious"
    ml_prediction: MLPrediction
    cti_result: CTIResult
    dns_whois: DNSWhoisResult
    obfuscation: ObfuscationResult
    typosquatting: TyposquattingResult
    summary: str  # Human-readable threat summary


class ScanHistoryItem(BaseModel):
    scan_id: str
    url: str
    timestamp: str
    risk_score: int
    risk_level: str
    ml_label: str


class HistoryStatsResponse(BaseModel):
    total_scans: int
    phishing_count: int
    legitimate_count: int
    suspicious_count: int
    avg_risk_score: float
    scans_today: int


class ExportResponse(BaseModel):
    format: str
    data: list[dict]
    total_records: int
    exported_at: str
