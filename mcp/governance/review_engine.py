"""Governance review workflow engine."""

from __future__ import annotations

from datetime import datetime
from typing import Dict
from uuid import uuid4

from mcp.governance.audit import GovernanceAuditLog
from mcp.governance.policy import default_expiration
from mcp.models.governance_models import ActionReview, ReviewRiskTier, ReviewStatus


class ReviewEngine:
    """
    In-memory review engine with durable transition audit.

    This intentionally keeps the first implementation deterministic and simple,
    while preserving the API surface for a future persistent review store.
    """

    def __init__(self, audit_log: GovernanceAuditLog | None = None) -> None:
        self._reviews: Dict[str, ActionReview] = {}
        self.audit_log = audit_log or GovernanceAuditLog()

    def create_review(
        self,
        incident_id: str,
        action_type: str,
        risk_tier: ReviewRiskTier,
        owner: str,
        rationale: str,
    ) -> ActionReview:
        review_id = f"ar-{uuid4().hex[:12]}"
        status = ReviewStatus.AWAITING_REVIEW if risk_tier == ReviewRiskTier.HIGH else ReviewStatus.APPROVED
        review = ActionReview(
            review_id=review_id,
            incident_id=incident_id,
            action_type=action_type,
            risk_tier=risk_tier,
            owner=owner,
            rationale=rationale,
            status=status,
            expires_at=default_expiration(risk_tier),
        )
        self._reviews[review_id] = review
        self.audit_log.write(
            review_id=review_id,
            incident_id=incident_id,
            previous_status=None,
            new_status=review.status.value,
            actor="review_engine",
            comment="Review created",
        )
        return review

    def transition(
        self,
        review_id: str,
        new_status: ReviewStatus,
        actor: str,
        reviewer_comment: str | None = None,
    ) -> ActionReview:
        review = self._reviews[review_id]
        previous = review.status
        review.status = new_status
        review.updated_at = datetime.utcnow()
        review.reviewer = actor
        review.reviewer_comment = reviewer_comment
        if new_status == ReviewStatus.EXECUTED:
            review.executed_at = datetime.utcnow()
        self.audit_log.write(
            review_id=review.review_id,
            incident_id=review.incident_id,
            previous_status=previous.value,
            new_status=new_status.value,
            actor=actor,
            comment=reviewer_comment,
        )
        return review

    def expire_overdue(self) -> int:
        now = datetime.utcnow()
        expired = 0
        for review in self._reviews.values():
            if (
                review.status == ReviewStatus.AWAITING_REVIEW
                and review.expires_at
                and review.expires_at < now
            ):
                self.transition(
                    review_id=review.review_id,
                    new_status=ReviewStatus.EXPIRED,
                    actor="review_engine",
                    reviewer_comment="SLA expired",
                )
                expired += 1
        return expired

    def get(self, review_id: str) -> ActionReview:
        return self._reviews[review_id]

    def list_reviews(self, status: ReviewStatus | None = None) -> list[ActionReview]:
        if status is None:
            return list(self._reviews.values())
        return [review for review in self._reviews.values() if review.status == status]
