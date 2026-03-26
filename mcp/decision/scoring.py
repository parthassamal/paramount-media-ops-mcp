"""
Deterministic scoring model for incident priority and business risk.

Critical control-plane decisions should not rely on non-deterministic models.
"""

from __future__ import annotations

from mcp.decision.models import DecisionScoring, IncidentDecisionInput


SEVERITY_WEIGHTS = {
    "critical": 100.0,
    "high": 75.0,
    "medium": 45.0,
    "low": 25.0,
}


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_operational_severity(incident: IncidentDecisionInput) -> float:
    """
    Score incident operational severity based on severity class and blast radius.
    """
    base = SEVERITY_WEIGHTS.get(incident.severity.lower(), 40.0)
    blast_boost = incident.blast_radius_score * 20.0
    delay_boost = min(incident.delay_days * 2.0, 10.0)
    return _clamp(base + blast_boost + delay_boost)


def score_subscriber_impact(incident: IncidentDecisionInput) -> float:
    """
    Score subscriber impact using affected users and churn-aligned risk proxies.
    """
    # 1M+ affected subscribers saturates this dimension.
    subscribers_score = min((incident.affected_subscribers / 1_000_000) * 100.0, 100.0)
    delay_penalty = min(incident.delay_days * 3.0, 15.0)
    return _clamp(subscribers_score + delay_penalty)


def score_business_risk(incident: IncidentDecisionInput) -> float:
    """
    Score business impact from direct cost + revenue at risk.
    """
    # 5M cost and 10M revenue-at-risk are used as saturation caps.
    cost_score = min((incident.cost_impact / 5_000_000) * 100.0, 100.0)
    revenue_score = min((incident.revenue_at_risk / 10_000_000) * 100.0, 100.0)
    return _clamp((cost_score * 0.45) + (revenue_score * 0.55))


def score_confidence(incident: IncidentDecisionInput) -> float:
    """
    Score confidence based on evidence completeness and existing RCA context.
    """
    completeness = incident.evidence_completeness_score * 100.0
    pipeline_bonus = 10.0 if incident.has_open_rca else 0.0
    review_penalty = 10.0 if incident.generated_tests_pending_review else 0.0
    return _clamp(completeness + pipeline_bonus - review_penalty)


def score_incident(incident: IncidentDecisionInput) -> DecisionScoring:
    """
    Produce all scoring dimensions and an aggregate priority score.
    """
    operational = score_operational_severity(incident)
    subscriber = score_subscriber_impact(incident)
    business = score_business_risk(incident)
    confidence = score_confidence(incident)

    # Priority emphasizes operational severity and business impact.
    priority = _clamp(
        (operational * 0.35)
        + (subscriber * 0.20)
        + (business * 0.30)
        + (confidence * 0.15)
    )

    return DecisionScoring(
        operational_severity_score=round(operational, 2),
        subscriber_impact_score=round(subscriber, 2),
        business_risk_score=round(business, 2),
        confidence_score=round(confidence, 2),
        priority_score=round(priority, 2),
    )
