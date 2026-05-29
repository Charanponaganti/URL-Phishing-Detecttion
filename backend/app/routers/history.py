"""
PhishGuard — History Router
Scan history endpoints with pagination and statistics.
"""

from fastapi import APIRouter, Query
from app.models.schemas import ScanHistoryItem, HistoryStatsResponse, ScanResponse
from app.models.database import get_history, get_scan, get_stats

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=list[ScanHistoryItem])
async def list_scans(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get paginated scan history."""
    return get_history(limit=limit, offset=offset)


@router.get("/stats", response_model=HistoryStatsResponse)
async def scan_stats():
    """Get aggregate scan statistics."""
    return get_stats()


@router.get("/{scan_id}")
async def get_scan_detail(scan_id: str):
    """Get full scan details by ID."""
    scan = get_scan(scan_id)
    if not scan:
        return {"error": "Scan not found"}
    return scan
