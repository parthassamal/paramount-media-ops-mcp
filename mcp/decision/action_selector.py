"""
Action ranking rules for the incident decision engine.
"""

from __future__ import annotations

from typing import List

from mcp.decision.models import (
    ActionRecommendation,
    ActionRiskTier,
    DecisionActionType,
    DecisionScoring,
    IncidentDecisionInput,
)


def _service_owner(incident: IncidentDecisionInput) -> str:
    if incident.team:
        return incident.team
    if incident.service:
        return f"{incident.service}-owners"
    return "platform-ops"


def _base_confidence(scoring: DecisionScoring) -> float:
    return max(0.2, min(0.99, scoring.confidence_score / 100.0))


def select_actions(
    incident: IncidentDecisionInput,
    scoring: DecisionScoring,
) -> List[ActionRecommendation]:
    """
    Select and rank recommended actions using deterministic policy rules.
    """
    actions: List[ActionRecommendation] = []
    owner = _service_owner(incident)
    confidence = _base_confidence(scoring)

    if scoring.operational_severity_score >= 85 and incident.has_recent_failures:
        actions.append(
            ActionRecommendation(
                action_type=DecisionActionType.ROLLBACK_CANDIDATE,
                rank=1,
                risk_tier=ActionRiskTier.HIGH,
                owner=owner,
                confidence=round(confidence, 2),
                expected_business_impact_usd=max(incident.cost_impact * 0.4, 100_000),
                rationale="High-severity incident with recent failed verifications indicates high regression risk.",
                explanation="Rollback can quickly reduce customer impact while preserving evidence for RCA follow-up.",
                evidence_refs=["jira", "verification_runs", "pipeline_stage"],
                validation_plan=[
                    "Confirm rollback window and dependency readiness.",
                    "Run smoke checks for impacted endpoints.",
                    "Create verification run for the rollback build.",
                ],
                escalation_path="Notify incident commander and release manager for final approval.",
            )
        )
    elif scoring.operational_severity_score >= 75:
        actions.append(
            ActionRecommendation(
                action_type=DecisionActionType.RESTART_CANDIDATE,
                rank=1,
                risk_tier=ActionRiskTier.HIGH,
                owner=owner,
                confidence=round(confidence, 2),
                expected_business_impact_usd=max(incident.cost_impact * 0.25, 50_000),
                rationale="High operational severity with constrained blast radius supports controlled restart.",
                explanation="Restart candidate is preferred when symptom profile suggests transient service instability.",
                evidence_refs=["alerts", "error_rate", "service_map"],
                validation_plan=[
                    "Capture pre-mitigation evidence bundle.",
                    "Restart target service with change ticket reference.",
                    "Run canary verification and monitor error budget.",
                ],
                escalation_path="SRE on-call -> service owner -> incident commander.",
            )
        )

    if incident.generated_tests_pending_review or incident.has_open_rca:
        actions.append(
            ActionRecommendation(
                action_type=DecisionActionType.VALIDATE_FIX,
                rank=len(actions) + 1,
                risk_tier=ActionRiskTier.MEDIUM,
                owner="qa-ops",
                confidence=round(min(confidence + 0.05, 0.99), 2),
                expected_business_impact_usd=max(incident.cost_impact * 0.15, 25_000),
                rationale="Open RCA context indicates validation should run before declaring recovery.",
                explanation="Validation protects against false recovery and ensures fixes are measurable.",
                evidence_refs=["testrail", "review_queue", "jira"],
                validation_plan=[
                    "Approve queued tests if required.",
                    "Create verification run in TestRail.",
                    "Attach verification summary to Jira artifact.",
                ],
                escalation_path="QA lead -> release manager.",
            )
        )

    actions.append(
        ActionRecommendation(
            action_type=DecisionActionType.GENERATE_TESTS,
            rank=len(actions) + 1,
            risk_tier=ActionRiskTier.MEDIUM,
            owner="qa-ops",
            confidence=round(max(confidence - 0.05, 0.3), 2),
            expected_business_impact_usd=max(incident.cost_impact * 0.1, 10_000),
            rationale="Test generation expands regression coverage for impacted services.",
            explanation="Generating targeted tests reduces repeat incidents and supports closure governance.",
            evidence_refs=["evidence_bundle", "service_map", "historical_rca"],
            validation_plan=[
                "Generate service-specific regression tests.",
                "Route high-risk cases to human review.",
                "Track true/false positive signal over time.",
            ],
            escalation_path="QA manager for medium/high-risk suites.",
        )
    )

    if scoring.business_risk_score >= 65:
        actions.append(
            ActionRecommendation(
                action_type=DecisionActionType.ESCALATE_TO_OWNER,
                rank=len(actions) + 1,
                risk_tier=ActionRiskTier.LOW,
                owner=owner,
                confidence=round(confidence, 2),
                expected_business_impact_usd=incident.revenue_at_risk,
                rationale="Business exposure exceeds threshold and requires accountable owner visibility.",
                explanation="Escalation aligns action execution with service accountability and SLA commitments.",
                evidence_refs=["business_risk", "jira", "pipeline_health"],
                validation_plan=[
                    "Assign owner in Jira.",
                    "Set response SLA and checkpoint cadence.",
                ],
                escalation_path="Director on-call if no acknowledgement in SLA window.",
            )
        )

    if incident.affected_subscribers >= 100_000:
        actions.append(
            ActionRecommendation(
                action_type=DecisionActionType.CREATE_RETENTION_CAMPAIGN,
                rank=len(actions) + 1,
                risk_tier=ActionRiskTier.LOW,
                owner="retention-ops",
                confidence=round(max(confidence - 0.1, 0.2), 2),
                expected_business_impact_usd=max(incident.revenue_at_risk * 0.2, 50_000),
                rationale="Large subscriber cohort may churn without mitigation communication.",
                explanation="Retention action should run in parallel with engineering remediation for high-impact incidents.",
                evidence_refs=["subscriber_impact", "churn_cohorts"],
                validation_plan=[
                    "Target impacted cohorts with proactive communication.",
                    "Track campaign conversion and churn movement.",
                ],
                escalation_path="Retention lead -> growth director.",
            )
        )

    # Re-rank actions to ensure contiguous ordering.
    for index, action in enumerate(actions, start=1):
        action.rank = index
    return actions
