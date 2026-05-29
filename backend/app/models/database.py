"""
PhishGuard — SQLite Database
Stores scan history for the analyst dashboard.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

from app.config import settings

DB_PATH = settings.database_url


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                scan_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                ml_label TEXT NOT NULL,
                ml_confidence REAL NOT NULL,
                full_report TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans(timestamp DESC)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_risk ON scans(risk_level)
        """)
        conn.commit()


@contextmanager
def get_db():
    """Database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_scan(scan_data: dict):
    """Save a scan result to the database."""
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO scans
               (scan_id, url, timestamp, risk_score, risk_level, ml_label, ml_confidence, full_report)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scan_data["scan_id"],
                scan_data["url"],
                scan_data["timestamp"],
                scan_data["risk_score"],
                scan_data["risk_level"],
                scan_data["ml_prediction"]["label"],
                scan_data["ml_prediction"]["confidence"],
                json.dumps(scan_data),
            )
        )
        conn.commit()


def get_scan(scan_id: str) -> dict | None:
    """Get a single scan by ID."""
    with get_db() as conn:
        row = conn.execute("SELECT full_report FROM scans WHERE scan_id = ?", (scan_id,)).fetchone()
        if row:
            return json.loads(row["full_report"])
    return None


def get_history(limit: int = 50, offset: int = 0) -> list[dict]:
    """Get paginated scan history."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT scan_id, url, timestamp, risk_score, risk_level, ml_label
               FROM scans ORDER BY timestamp DESC LIMIT ? OFFSET ?""",
            (limit, offset)
        ).fetchall()
        return [dict(r) for r in rows]


def get_stats() -> dict:
    """Get aggregate scan statistics."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM scans").fetchone()["c"]
        phishing = conn.execute("SELECT COUNT(*) as c FROM scans WHERE ml_label = 'phishing'").fetchone()["c"]
        legit = conn.execute("SELECT COUNT(*) as c FROM scans WHERE ml_label = 'legitimate'").fetchone()["c"]
        suspicious = conn.execute("SELECT COUNT(*) as c FROM scans WHERE risk_level = 'suspicious'").fetchone()["c"]
        avg_risk = conn.execute("SELECT COALESCE(AVG(risk_score), 0) as a FROM scans").fetchone()["a"]

        today = datetime.now().strftime("%Y-%m-%d")
        today_count = conn.execute(
            "SELECT COUNT(*) as c FROM scans WHERE timestamp LIKE ?", (f"{today}%",)
        ).fetchone()["c"]

        return {
            "total_scans": total,
            "phishing_count": phishing,
            "legitimate_count": legit,
            "suspicious_count": suspicious,
            "avg_risk_score": round(avg_risk, 1),
            "scans_today": today_count,
        }


def get_all_scans() -> list[dict]:
    """Get all scans for export."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT full_report FROM scans ORDER BY timestamp DESC"
        ).fetchall()
        return [json.loads(r["full_report"]) for r in rows]
