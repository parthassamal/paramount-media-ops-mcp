"""
Human review queue model with SLA enforcement.

Generated test cases must pass human review before being written to TestRail.
This model tracks review items and enforces a 24-hour SLA.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"  # SLA breached


class ReviewItem(BaseModel):
    """Single item in the human review queue."""
    review_id: str
    rca_id: str
    jira_ticket_id: str
    created_at: datetime
    sla_deadline: datetime  # 24 hours from created_at
    status: ReviewStatus = ReviewStatus.PENDING

    # What's being reviewed
    generated_cases: List[Dict[str, Any]] = []
    ai_summary: Optional[str] = None
    match_confidence: Optional[str] = None

    # Review outcome
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    approved_case_indices: Optional[List[int]] = None  # Which cases were approved

    @property
    def is_overdue(self) -> bool:
        return datetime.utcnow() > self.sla_deadline and self.status == ReviewStatus.PENDING
