"""Governance API -- action review CRUD, approval workflow, and audit trail."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from mcp.governance.review_engine import ReviewEngine
from mcp.governance.audit import GovernanceAuditLog
from mcp.models.governance_models import ActionReview, ReviewRiskTier, ReviewStatus


router = APIRouter(prefix="/api/governance", tags=["Governance"])

_audit_log = GovernanceAuditLog()
_review_engine = ReviewEngine(audit_log=_audit_log)


def get_review_engine() -> ReviewEngine:
    return _review_engine


class ReviewActionRequest(BaseModel):
    reviewer: str = Field(..., min_length=1)
    comment: Optional[str] = None


class GovernanceStats(BaseModel):
    total: int = 0
    awaiting_review: int = 0
    approved: int = 0
    rejected: int = 0
    expired: int = 0
    executed: int = 0
    failed: int = 0
    overdue: int = 0


@router.get("/reviews", response_model=List[ActionReview])
async def list_reviews(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    incident_id: Optional[str] = Query(default=None),
):
    """List governance reviews, optionally filtered by status or incident."""
    status_filter = ReviewStatus(status) if status else None
    reviews = _review_engine.list_reviews(status=status_filter)
    if incident_id:
        reviews = [r for r in reviews if r.incident_id == incident_id]
    return reviews


@router.get("/reviews/{review_id}", response_model=ActionReview)
async def get_review(review_id: str):
    """Get a single review by ID."""
    try:
        return _review_engine.get(review_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")


@router.post("/reviews/{review_id}/approve", response_model=ActionReview)
async def approve_review(review_id: str, body: ReviewActionRequest):
    """Approve a pending action review."""
    try:
        review = _review_engine.get(review_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")

    if review.status != ReviewStatus.AWAITING_REVIEW:
        raise HTTPException(
            status_code=409,
            detail=f"Review is in '{review.status.value}' state and cannot be approved",
        )

    return _review_engine.transition(
        review_id=review_id,
        new_status=ReviewStatus.APPROVED,
        actor=body.reviewer,
        reviewer_comment=body.comment,
    )


@router.post("/reviews/{review_id}/reject", response_model=ActionReview)
async def reject_review(review_id: str, body: ReviewActionRequest):
    """Reject a pending action review."""
    try:
        review = _review_engine.get(review_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Review {review_id} not found")

    if review.status not in (ReviewStatus.AWAITING_REVIEW, ReviewStatus.APPROVED):
        raise HTTPException(
            status_code=409,
            detail=f"Review is in '{review.status.value}' state and cannot be rejected",
        )

    return _review_engine.transition(
        review_id=review_id,
        new_status=ReviewStatus.REJECTED,
        actor=body.reviewer,
        reviewer_comment=body.comment,
    )


@router.get("/audit/{review_id}")
async def get_audit_trail(review_id: str):
    """Get the full audit trail for a review."""
    entries = _audit_log.list_for_review(review_id)
    if not entries:
        raise HTTPException(status_code=404, detail=f"No audit entries for {review_id}")
    return entries


@router.get("/stats", response_model=GovernanceStats)
async def get_governance_stats():
    """Aggregate governance statistics."""
    from datetime import datetime

    all_reviews = _review_engine.list_reviews()
    now = datetime.utcnow()
    overdue = sum(
        1
        for r in all_reviews
        if r.status == ReviewStatus.AWAITING_REVIEW
        and r.expires_at
        and r.expires_at < now
    )

    def _count(s: ReviewStatus) -> int:
        return sum(1 for r in all_reviews if r.status == s)

    return GovernanceStats(
        total=len(all_reviews),
        awaiting_review=_count(ReviewStatus.AWAITING_REVIEW),
        approved=_count(ReviewStatus.APPROVED),
        rejected=_count(ReviewStatus.REJECTED),
        expired=_count(ReviewStatus.EXPIRED),
        executed=_count(ReviewStatus.EXECUTED),
        failed=_count(ReviewStatus.FAILED),
        overdue=overdue,
    )
