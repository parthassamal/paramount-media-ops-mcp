"""
SQLite-backed RCA audit store.

Every stage transition is persisted for traceability.
Uses a single table with JSON columns for complex fields.
"""

import sqlite3
from typing import Optional, List
from datetime import datetime
from pathlib import Path

from mcp.models.rca_models import RCARecord, PipelineStage
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "rca_audit.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_rca_db():
    """Create the RCA table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rca_records (
            rca_id TEXT PRIMARY KEY,
            jira_ticket_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            stage TEXT NOT NULL DEFAULT 'intake',
            data JSON NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rca_jira ON rca_records(jira_ticket_id)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rca_stage ON rca_records(stage)
    """)
    conn.commit()
    conn.close()
    logger.info("RCA database initialized", db_path=str(DB_PATH))


def upsert_rca(record: RCARecord):
    """Insert or update an RCA record. Every call persists the full state."""
    record.updated_at = datetime.utcnow()
    conn = _get_conn()
    conn.execute(
        """INSERT INTO rca_records (rca_id, jira_ticket_id, created_at, updated_at, stage, data)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(rca_id) DO UPDATE SET
               updated_at = excluded.updated_at,
               stage = excluded.stage,
               data = excluded.data""",
        (
            record.rca_id,
            record.jira_ticket_id,
            record.created_at.isoformat(),
            record.updated_at.isoformat(),
            record.stage.value,
            record.model_dump_json()
        )
    )
    conn.commit()
    conn.close()
    logger.debug("RCA upserted", rca_id=record.rca_id, stage=record.stage.value)


def get_rca(rca_id: str) -> Optional[RCARecord]:
    """Fetch a single RCA record by ID."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM rca_records WHERE rca_id = ?", (rca_id,)
    ).fetchone()
    conn.close()

    if row:
        return RCARecord.model_validate_json(row["data"])
    return None


def get_rcas_by_stage(stage: PipelineStage) -> List[RCARecord]:
    """Fetch all RCA records at a given pipeline stage."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT data FROM rca_records WHERE stage = ? ORDER BY updated_at DESC",
        (stage.value,)
    ).fetchall()
    conn.close()
    return [RCARecord.model_validate_json(row["data"]) for row in rows]


def get_rcas_by_jira(jira_ticket_id: str) -> List[RCARecord]:
    """Fetch all RCA records for a Jira ticket."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT data FROM rca_records WHERE jira_ticket_id = ? ORDER BY created_at DESC",
        (jira_ticket_id,)
    ).fetchall()
    conn.close()
    return [RCARecord.model_validate_json(row["data"]) for row in rows]


def get_rca_by_jira_key(jira_key: str) -> Optional[RCARecord]:
    """
    Fetch the most recent RCA record for a Jira ticket key.
    Used by dashboard to show pipeline stage badges.
    """
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM rca_records WHERE jira_ticket_id = ? ORDER BY created_at DESC LIMIT 1",
        (jira_key,)
    ).fetchone()
    conn.close()
    
    if row:
        return RCARecord.model_validate_json(row["data"])
    return None


def get_recent_rcas(limit: int = 50) -> List[RCARecord]:
    """Fetch recent RCA records."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT data FROM rca_records ORDER BY updated_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [RCARecord.model_validate_json(row["data"]) for row in rows]


def check_for_duplicates(summary: str, window_days: int = 90) -> Optional[dict]:
    """
    Check for duplicate incidents within the configured window.
    Uses basic text matching against recent summaries.
    """
    from difflib import SequenceMatcher

    conn = _get_conn()
    cutoff = datetime.utcnow().isoformat()
    rows = conn.execute(
        "SELECT rca_id, jira_ticket_id, data FROM rca_records WHERE created_at > date(?, '-' || ? || ' days') ORDER BY created_at DESC LIMIT 100",
        (cutoff, window_days)
    ).fetchall()
    conn.close()

    for row in rows:
        record = RCARecord.model_validate_json(row["data"])
        if record.ai_summary:
            similarity = SequenceMatcher(None, summary.lower(), record.ai_summary.lower()).ratio()
            if similarity > 0.8:
                return {
                    "duplicate_of": record.rca_id,
                    "jira_ticket_id": record.jira_ticket_id,
                    "similarity": similarity
                }
    return None


# Initialize on import
init_rca_db()
