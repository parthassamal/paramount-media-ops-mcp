"""
SQLite-backed review queue for human-gated approvals.

Generated test cases must pass human review before being written to TestRail.
Enforces a 24-hour SLA with automatic expiration.
"""

import sqlite3
import uuid
from typing import Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from mcp.models.review_queue import ReviewItem, ReviewStatus
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "data" / "review_queue.db"


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_review_db():
    """Create the review queue table if it doesn't exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS review_queue (
            review_id TEXT PRIMARY KEY,
            rca_id TEXT NOT NULL,
            jira_ticket_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            sla_deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            data JSON NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_review_status ON review_queue(status)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_review_rca ON review_queue(rca_id)
    """)
    conn.commit()
    conn.close()
    logger.info("Review queue database initialized")


def create_review_item(
    rca_id: str,
    jira_ticket_id: str,
    generated_cases: list,
    ai_summary: str = None,
    match_confidence: str = None,
    sla_hours: int = 24
) -> ReviewItem:
    """Create a new review item in the queue."""
    now = datetime.utcnow()
    item = ReviewItem(
        review_id=str(uuid.uuid4()),
        rca_id=rca_id,
        jira_ticket_id=jira_ticket_id,
        created_at=now,
        sla_deadline=now + timedelta(hours=sla_hours),
        generated_cases=generated_cases,
        ai_summary=ai_summary,
        match_confidence=match_confidence
    )

    conn = _get_conn()
    conn.execute(
        """INSERT INTO review_queue
           (review_id, rca_id, jira_ticket_id, created_at, sla_deadline, status, data)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            item.review_id, item.rca_id, item.jira_ticket_id,
            item.created_at.isoformat(), item.sla_deadline.isoformat(),
            item.status.value, item.model_dump_json()
        )
    )
    conn.commit()
    conn.close()

    logger.info("Review item created", review_id=item.review_id, rca_id=rca_id)
    return item


def approve_review(
    review_id: str,
    reviewer_id: str,
    notes: str = "",
    approved_case_indices: list = None
) -> ReviewItem:
    """Approve a review item. Only approves if still PENDING."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM review_queue WHERE review_id = ?", (review_id,)
    ).fetchone()

    if not row:
        raise ValueError(f"Review item {review_id} not found")

    item = ReviewItem.model_validate_json(row["data"])
    if item.status != ReviewStatus.PENDING:
        raise ValueError(f"Review {review_id} is {item.status.value}, cannot approve")

    item.status = ReviewStatus.APPROVED
    item.reviewer_id = reviewer_id
    item.reviewed_at = datetime.utcnow()
    item.reviewer_notes = notes
    item.approved_case_indices = approved_case_indices

    conn.execute(
        "UPDATE review_queue SET status = ?, data = ? WHERE review_id = ?",
        (item.status.value, item.model_dump_json(), review_id)
    )
    conn.commit()
    conn.close()

    logger.info("Review approved", review_id=review_id, reviewer=reviewer_id)
    return item


def reject_review(review_id: str, reviewer_id: str, notes: str = "") -> ReviewItem:
    """Reject a review item."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM review_queue WHERE review_id = ?", (review_id,)
    ).fetchone()

    if not row:
        raise ValueError(f"Review item {review_id} not found")

    item = ReviewItem.model_validate_json(row["data"])
    item.status = ReviewStatus.REJECTED
    item.reviewer_id = reviewer_id
    item.reviewed_at = datetime.utcnow()
    item.reviewer_notes = notes

    conn.execute(
        "UPDATE review_queue SET status = ?, data = ? WHERE review_id = ?",
        (item.status.value, item.model_dump_json(), review_id)
    )
    conn.commit()
    conn.close()

    logger.info("Review rejected", review_id=review_id, reviewer=reviewer_id)
    return item


def get_pending_reviews() -> List[ReviewItem]:
    """Fetch all pending review items, marking expired ones."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT data FROM review_queue WHERE status = 'pending' ORDER BY created_at ASC"
    ).fetchall()

    items = []
    now = datetime.utcnow()
    for row in rows:
        item = ReviewItem.model_validate_json(row["data"])
        if item.is_overdue:
            item.status = ReviewStatus.EXPIRED
            conn.execute(
                "UPDATE review_queue SET status = ?, data = ? WHERE review_id = ?",
                (item.status.value, item.model_dump_json(), item.review_id)
            )
        items.append(item)

    conn.commit()
    conn.close()
    return items


def get_review_by_rca(rca_id: str) -> Optional[ReviewItem]:
    """Get the latest review item for an RCA."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM review_queue WHERE rca_id = ? ORDER BY created_at DESC LIMIT 1",
        (rca_id,)
    ).fetchone()
    conn.close()

    if row:
        return ReviewItem.model_validate_json(row["data"])
    return None


def mark_review_expired(review_id: str) -> Optional[ReviewItem]:
    """
    Mark a review item as expired due to SLA breach.
    Called by the scheduler when the 24-hour window passes.
    """
    conn = _get_conn()
    row = conn.execute(
        "SELECT data FROM review_queue WHERE review_id = ?", (review_id,)
    ).fetchone()

    if not row:
        conn.close()
        return None

    item = ReviewItem.model_validate_json(row["data"])
    
    if item.status != ReviewStatus.PENDING:
        conn.close()
        return item  # Already processed
    
    item.status = ReviewStatus.EXPIRED
    
    conn.execute(
        "UPDATE review_queue SET status = ?, data = ? WHERE review_id = ?",
        (item.status.value, item.model_dump_json(), review_id)
    )
    conn.commit()
    conn.close()

    logger.warning("Review marked expired due to SLA breach", review_id=review_id)
    return item


def get_review_stats() -> dict:
    """Get review queue statistics for monitoring."""
    conn = _get_conn()
    
    stats = {
        "pending": 0,
        "approved": 0,
        "rejected": 0,
        "expired": 0,
        "avg_review_time_hours": None
    }
    
    # Count by status
    rows = conn.execute(
        "SELECT status, COUNT(*) as count FROM review_queue GROUP BY status"
    ).fetchall()
    
    for row in rows:
        status = row["status"]
        if status in stats:
            stats[status] = row["count"]
    
    # Calculate average review time for approved items
    approved = conn.execute(
        "SELECT data FROM review_queue WHERE status = 'approved'"
    ).fetchall()
    
    review_times = []
    for row in approved:
        item = ReviewItem.model_validate_json(row["data"])
        if item.reviewed_at and item.created_at:
            delta = item.reviewed_at - item.created_at
            review_times.append(delta.total_seconds() / 3600)
    
    if review_times:
        stats["avg_review_time_hours"] = round(sum(review_times) / len(review_times), 2)
    
    conn.close()
    return stats


# Initialize on import
init_review_db()
