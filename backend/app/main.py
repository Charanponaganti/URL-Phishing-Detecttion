"""
PhishGuard — FastAPI Application
Main entry point with CORS, lifespan, and router registration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.database import init_db
from app.services.ml_predictor import predict_url, is_model_loaded
from app.routers import scan, history, report


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB and preload ML model."""
    print(f"\n{'='*50}")
    print(f"  [*] PhishGuard API Starting...")
    print(f"{'='*50}")

    init_db()
    print("[PhishGuard] Database initialized")

    # Preload ML model by running a dummy prediction
    try:
        predict_url("https://example.com")
        if is_model_loaded():
            print("[PhishGuard] ML model preloaded [OK]")
        else:
            print("[PhishGuard] ML model not found -- using heuristic fallback")
    except Exception as e:
        print(f"[PhishGuard] ML model load warning: {e}")

    print(f"[PhishGuard] API ready at http://localhost:8000")
    print(f"[PhishGuard] Docs at http://localhost:8000/docs")
    print(f"{'='*50}\n")

    yield

    print("[PhishGuard] Shutting down...")


app = FastAPI(
    title="PhishGuard API",
    description="ML-Powered Phishing URL Detection with Cyber Threat Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(scan.router)
app.include_router(history.router)
app.include_router(report.router)


@app.get("/")
async def root():
    return {
        "name": "PhishGuard API",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": is_model_loaded(),
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": is_model_loaded()}
