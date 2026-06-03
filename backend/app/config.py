"""
PhishGuard — Application Configuration
Loads settings from environment variables / .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

# config.py is at backend/app/config.py, so parent.parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ML_ARTIFACTS = PROJECT_ROOT / "ml_pipeline" / "artifacts"


class Settings(BaseSettings):
    model_config = {
        "protected_namespaces": (),
        "env_file": str(PROJECT_ROOT / ".env"),
        "env_file_encoding": "utf-8",
    }

    # App
    app_name: str = "PhishGuard"
    debug: bool = True

    # API Keys (optional -- CTI features degrade gracefully without them)
    virustotal_api_key: str = ""
    urlhaus_enabled: bool = True

    # ML Model
    model_path: str = str(ML_ARTIFACTS / "xgboost_model.joblib")
    scaler_path: str = str(ML_ARTIFACTS / "feature_scaler.joblib")

    # Database
    database_url: str = str(PROJECT_ROOT / "backend" / "phishguard.db")

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://phishguard-dashboard.onrender.com",
        "chrome-extension://*",
    ]


settings = Settings()

