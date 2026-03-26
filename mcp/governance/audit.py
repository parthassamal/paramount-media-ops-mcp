"""Governance audit log persistence."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

class GovernanceAuditLog:
    """SQLite-backed audit log for governance transitions."""

    def __init__(self, db_path: str | None = None) -> None:
        configured_path = db_path or str(Path("data") / "governance_audit.db")
        self.db_path = configured_path
        self._initialize()

    def _initialize(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS governance_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id TEXT NOT NULL,
                    incident_id TEXT NOT NULL,
                    previous_status TEXT,
                    new_status TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    comment TEXT,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def write(
        self,
        review_id: str,
        incident_id: str,
        previous_status: str | None,
        new_status: str,
        actor: str,
        comment: str | None = None,
        metadata: str | None = None,
    ) -> None:
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO governance_audit_log (
                    review_id, incident_id, previous_status, new_status,
                    actor, comment, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    review_id,
                    incident_id,
                    previous_status,
                    new_status,
                    actor,
                    comment,
                    metadata,
                    timestamp,
                ),
            )
            conn.commit()

    def list_for_review(self, review_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT review_id, incident_id, previous_status, new_status,
                       actor, comment, metadata, created_at
                FROM governance_audit_log
                WHERE review_id = ?
                ORDER BY id ASC
                """,
                (review_id,),
            ).fetchall()
            return [dict(row) for row in rows]
