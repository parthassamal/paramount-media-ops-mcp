"""Governance policy for action risk classification and review requirements."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Tuple

from mcp.decision.models import ActionRiskTier, DecisionActionType
from mcp.models.governance_models import ReviewRiskTier


HIGH_RISK_ACTIONS = {
    DecisionActionType.RESTART_CANDIDATE.value,
    DecisionActionType.ROLLBACK_CANDIDATE.value,
}

MEDIUM_RISK_ACTIONS = {
    DecisionActionType.VALIDATE_FIX.value,
    DecisionActionType.GENERATE_TESTS.value,
}


def classify_action_risk(action_type: str, confidence: float) -> ReviewRiskTier:
    """
    Classify action risk according to deterministic governance policy.
    """
    if action_type in HIGH_RISK_ACTIONS:
        return ReviewRiskTier.HIGH
    if action_type in MEDIUM_RISK_ACTIONS:
        return ReviewRiskTier.MEDIUM
    if confidence < 0.45:
        return ReviewRiskTier.MEDIUM
    return ReviewRiskTier.LOW


def requires_human_approval(risk_tier: ReviewRiskTier) -> bool:
    """
    Approval rules:
    - low: auto-allowed
    - medium: notify + allow
    - high: explicit human approval required
    """
    return risk_tier == ReviewRiskTier.HIGH


def default_expiration(risk_tier: ReviewRiskTier) -> datetime:
    """
    Default SLA windows for action review.
    """
    hours = 24 if risk_tier == ReviewRiskTier.HIGH else 12
    return datetime.utcnow() + timedelta(hours=hours)


def map_decision_risk(risk_tier: ActionRiskTier) -> ReviewRiskTier:
    if risk_tier == ActionRiskTier.HIGH:
        return ReviewRiskTier.HIGH
    if risk_tier == ActionRiskTier.MEDIUM:
        return ReviewRiskTier.MEDIUM
    return ReviewRiskTier.LOW


def classify_and_require(action_type: str, confidence: float) -> Tuple[ReviewRiskTier, bool]:
    risk = classify_action_risk(action_type=action_type, confidence=confidence)
    return risk, requires_human_approval(risk)
