"""
PhishGuard — ML Predictor Service
Loads the serialized XGBoost model and performs inference.
"""

import numpy as np
import joblib
from pathlib import Path

from app.config import settings
from app.services.feature_extractor import extract_features, FEATURE_NAMES

_model = None
_scaler = None


def _load_model():
    """Lazy-load model and scaler."""
    global _model, _scaler
    model_path = Path(settings.model_path)
    scaler_path = Path(settings.scaler_path)

    if model_path.exists() and scaler_path.exists():
        _model = joblib.load(str(model_path))
        _scaler = joblib.load(str(scaler_path))
        print(f"[PhishGuard] ML model loaded from {model_path}")
    else:
        print(f"[PhishGuard] WARNING: Model files not found. ML predictions will use fallback heuristics.")
        _model = None
        _scaler = None


def predict_url(url: str) -> dict:
    """
    Run ML inference on a single URL.
    Returns prediction label, confidence, risk score, and feature importances.
    """
    global _model, _scaler

    # Lazy load
    if _model is None and _scaler is None:
        _load_model()

    features = extract_features(url)

    if _model is not None and _scaler is not None:
        features_scaled = _scaler.transform(features.reshape(1, -1))
        prediction = _model.predict(features_scaled)[0]
        probabilities = _model.predict_proba(features_scaled)[0]

        # Label mapping (from existing Traditional_ML: 0=phishing, 1=legitimate)
        if prediction == 0:
            label = "phishing"
            confidence = float(probabilities[0])
        else:
            label = "legitimate"
            confidence = float(probabilities[1])

        # Risk score: 0 (safe) to 100 (dangerous)
        phishing_prob = float(probabilities[0])
        risk_score = int(round(phishing_prob * 100))

        # Top feature importances
        importances = {}
        if hasattr(_model, "feature_importances_"):
            fi = _model.feature_importances_
            top_indices = np.argsort(fi)[::-1][:10]
            for idx in top_indices:
                if idx < len(FEATURE_NAMES):
                    importances[FEATURE_NAMES[idx]] = round(float(fi[idx]), 4)

    else:
        # Fallback heuristic when no model is loaded
        risk_score = _heuristic_risk(features)
        if risk_score >= 60:
            label = "phishing"
            confidence = min(0.5 + (risk_score - 60) / 80, 0.95)
        else:
            label = "legitimate"
            confidence = min(0.5 + (60 - risk_score) / 80, 0.95)
        importances = {}

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "risk_score": risk_score,
        "feature_importances": importances,
    }


def _heuristic_risk(features: np.ndarray) -> int:
    """Simple heuristic risk scoring when no ML model is available."""
    score = 30  # baseline
    url_len = features[0]
    has_ip = features[20]
    has_at = features[24]
    is_shortened = features[27]
    subdomain_count = features[3]
    entropy = features[18]

    if url_len > 75:
        score += 15
    if has_ip:
        score += 25
    if has_at:
        score += 20
    if is_shortened:
        score += 10
    if subdomain_count > 3:
        score += 15
    if entropy > 4.5:
        score += 10

    return min(score, 100)


def is_model_loaded() -> bool:
    """Check if the ML model is loaded."""
    return _model is not None
