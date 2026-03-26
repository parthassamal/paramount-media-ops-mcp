"""
Decision engine contracts for incident intelligence and next-best-action planning.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class DecisionActionType(str, Enum):
    """Supported next-best-action types."""

    RESTART_CANDIDATE = "restart_candidate"
    ROLLBACK_CANDIDATE = "rollback_candidate"
    VALIDATE_FIX = "validate_fix"
    GENERATE_TESTS = "generate_tests"
    ESCALATE_TO_OWNER = "escalate_to_owner"
    CREATE_RETENTION_CAMPAIGN = "create_retention_campaign"


class ActionRiskTier(str, Enum):
    """Action risk classes used by governance policy."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionSignal(BaseModel):
    """Evidence signal used to explain a decision."""

    signal_key: str
    signal_value: str
    source: str
    weight: float = Field(default=0.0, ge=0.0, le=1.0)


class IncidentDecisionInput(BaseModel):
    """Normalized incident input for the decision engine."""

    incident_id: str
    summary: str
    service: str = ""
    status: str = "open"
    severity: str = "medium"
    team: Optional[str] = None
    cost_impact: float = 0.0
    revenue_at_risk: float = 0.0
    affected_subscribers: int = 0
    delay_days: int = 0
    evidence_completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    blast_radius_score: float = Field(default=0.0, ge=0.0, le=1.0)
    has_open_rca: bool = False
    has_recent_failures: bool = False
    generated_tests_pending_review: bool = False
    created_at: Optional[datetime] = None


class DecisionScoring(BaseModel):
    """Decision scoring dimensions and aggregate priority score."""

    operational_severity_score: float = Field(ge=0.0, le=100.0)
    subscriber_impact_score: float = Field(ge=0.0, le=100.0)
    business_risk_score: float = Field(ge=0.0, le=100.0)
    confidence_score: float = Field(ge=0.0, le=100.0)
    priority_score: float = Field(ge=0.0, le=100.0)


class ActionRecommendation(BaseModel):
    """Ranked action recommendation for operators."""

    action_type: DecisionActionType
    rank: int = Field(ge=1)
    risk_tier: ActionRiskTier
    owner: str
    confidence: float = Field(ge=0.0, le=1.0)
    expected_business_impact_usd: float = 0.0
    rationale: str
    explanation: str
    evidence_refs: List[str] = Field(default_factory=list)
    validation_plan: List[str] = Field(default_factory=list)
    escalation_path: Optional[str] = None
    status: str = "proposed"


class DecisionResult(BaseModel):
    """Top-level decision result for an incident."""

    incident_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    scoring: DecisionScoring
    signals: List[DecisionSignal] = Field(default_factory=list)
    recommended_actions: List[ActionRecommendation] = Field(default_factory=list)
    summary: str
