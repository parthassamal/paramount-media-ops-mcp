"""Governance and approval workflow models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReviewRiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReviewStatus(str, Enum):
    PROPOSED = "proposed"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"
    FAILED = "failed"


class ActionReview(BaseModel):
    """Action review request tracked by the governance control plane."""

    review_id: str
    incident_id: str
    action_type: str
    risk_tier: ReviewRiskTier
    owner: str
    status: ReviewStatus = ReviewStatus.PROPOSED
    rationale: str
    requested_by: str = "decision_engine"
    reviewer: Optional[str] = None
    reviewer_comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
