"""Mission Control API for operator-focused incident intelligence."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from config import settings
from mcp.db.rca_store import get_rca_by_jira_key
from mcp.db.review_store import get_pending_reviews
from mcp.decision import DecisionEngine, IncidentDecisionInput
from mcp.governance.policy import classify_action_risk, requires_human_approval
from mcp.integrations.jira_connector import JiraConnector
from mcp.tools.timeline_builder import build_incident_timeline

_log = logging.getLogger(__name__)


router = APIRouter(prefix="/api/mission-control", tags=["Mission Control"])
_jira = JiraConnector(mock_mode=settings.mock_mode)
_decision_engine = DecisionEngine()


class SystemMode(BaseModel):
    mode: str = Field(description="mock | hybrid | live")


class IncidentCard(BaseModel):
    incident_id: str
    summary: str
    service: str
    severity: str
    status: str
    team: Optional[str] = None
    cost_impact: float = 0.0
    delay_days: int = 0
    pipeline_stage: Optional[str] = None
    priority_score: float = 0.0
    confidence_score: float = 0.0
    top_action: Optional[str] = None
    top_action_confidence: Optional[float] = None


class MissionControlSummary(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    system_mode: SystemMode
    highest_priority_incident: Optional[IncidentCard] = None
    open_action_queue: int = 0
    pending_approvals: int = 0
    open_incidents: int = 0
    decision_summary: str


def _detect_system_mode() -> str:
    if getattr(settings, "jira_force_live", False) and settings.mock_mode:
        return "hybrid"
    if settings.mock_mode:
        return "mock"
    return "live"


def _to_incident_input(issue: dict) -> IncidentDecisionInput:
    incident_id = str(issue.get("issue_id") or issue.get("key") or "")
    summary = str(issue.get("title") or issue.get("summary") or "")
    service = str(issue.get("service_name") or issue.get("show") or issue.get("team") or "")
    severity = str(issue.get("severity") or "medium")
    status = str(issue.get("status") or "open")
    team = issue.get("team")
    cost_impact = float(issue.get("cost_overrun") or issue.get("cost_impact") or 0.0)
    revenue_at_risk = float(issue.get("revenue_at_risk") or (cost_impact * 1.5))
    delay_days = int(issue.get("delay_days") or 0)

    rca = get_rca_by_jira_key(incident_id)
    evidence_completeness = 0.8 if (rca and rca.evidence_bundle_id) else _derive_evidence_completeness()
    blast_radius_score = min((len(rca.impacted_components or []) / 10), 1.0) if rca else 0.2
    affected_subscribers = _derive_affected_subscribers(severity, cost_impact)

    return IncidentDecisionInput(
        incident_id=incident_id,
        summary=summary,
        service=service,
        status=status,
        severity=severity,
        team=team,
        cost_impact=cost_impact,
        revenue_at_risk=revenue_at_risk,
        affected_subscribers=affected_subscribers,
        delay_days=delay_days,
        evidence_completeness_score=evidence_completeness,
        blast_radius_score=blast_radius_score,
        has_open_rca=bool(rca and not rca.jira_closed),
        has_recent_failures=bool(rca and rca.verification_result and not rca.verification_result.all_passed),
        generated_tests_pending_review=bool(rca and rca.stage.value == "review_pending"),
    )


def _derive_evidence_completeness() -> float:
    """Heuristic: if NR or DD integrations are configured, assume partial evidence is available."""
    score = 0.25
    if getattr(settings, "newrelic_enabled", False):
        score += 0.15
    if getattr(settings, "datadog_enabled", False):
        score += 0.15
    return min(score, 1.0)


def _derive_affected_subscribers(severity: str, cost_impact: float) -> int:
    """Estimate subscriber impact from severity and cost when no direct telemetry exists."""
    base_map = {"critical": 50000, "high": 15000, "medium": 3000, "low": 500}
    base = base_map.get(severity, 1000)
    cost_factor = min(int(cost_impact / 100), 20000)
    return base + cost_factor


def _to_incident_card(issue: dict, incident: IncidentDecisionInput) -> IncidentCard:
    result = _decision_engine.evaluate(incident)
    rca = get_rca_by_jira_key(incident.incident_id)
    top = result.recommended_actions[0] if result.recommended_actions else None
    return IncidentCard(
        incident_id=incident.incident_id,
        summary=incident.summary,
        service=incident.service,
        severity=incident.severity,
        status=incident.status,
        team=incident.team,
        cost_impact=incident.cost_impact,
        delay_days=incident.delay_days,
        pipeline_stage=rca.stage.value if rca else None,
        priority_score=result.scoring.priority_score,
        confidence_score=result.scoring.confidence_score,
        top_action=top.action_type.value if top else None,
        top_action_confidence=top.confidence if top else None,
    )


@router.get("/summary", response_model=MissionControlSummary)
async def get_mission_control_summary(
    limit: int = Query(default=25, ge=1, le=200),
) -> MissionControlSummary:
    """
    Return a command-center summary with highest-priority incident and queue stats.
    """
    try:
        issues = _jira.get_production_issues(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to fetch incidents: {exc}") from exc

    incident_inputs = [_to_incident_input(issue) for issue in issues]
    ranked = _decision_engine.rank_incidents(incident_inputs)
    cards = []
    for issue, incident in zip(issues, incident_inputs):
        cards.append(_to_incident_card(issue, incident))
    cards.sort(key=lambda item: item.priority_score, reverse=True)

    pending_reviews = get_pending_reviews()
    high_priority = cards[0] if cards else None
    top_decision = ranked[0].summary if ranked else "No open incidents."

    return MissionControlSummary(
        system_mode=SystemMode(mode=_detect_system_mode()),
        highest_priority_incident=high_priority,
        open_action_queue=sum(1 for c in cards if c.top_action is not None),
        pending_approvals=sum(1 for r in pending_reviews if r.status.value == "pending"),
        open_incidents=len(cards),
        decision_summary=top_decision,
    )


@router.get("/incidents", response_model=List[IncidentCard])
async def list_prioritized_incidents(
    limit: int = Query(default=50, ge=1, le=200),
) -> List[IncidentCard]:
    """Return prioritized incidents for the mission-control queue."""
    try:
        issues = _jira.get_production_issues(limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to fetch incidents: {exc}") from exc

    cards = [_to_incident_card(issue, _to_incident_input(issue)) for issue in issues]
    cards.sort(key=lambda item: item.priority_score, reverse=True)
    return cards


@router.get("/incident/{incident_id}")
async def get_incident_detail(incident_id: str):
    """Return incident details with timeline, decision, governance reviews, and verification."""
    try:
        issues = _jira.get_production_issues(limit=200)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Unable to fetch incidents: {exc}") from exc

    incident_issue = None
    for issue in issues:
        key = str(issue.get("issue_id") or issue.get("key") or "")
        if key == incident_id:
            incident_issue = issue
            break
    if not incident_issue:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")

    incident_input = _to_incident_input(incident_issue)
    decision = _decision_engine.evaluate(incident_input)
    rca = get_rca_by_jira_key(incident_id)

    # --- C3: auto-create governance reviews for high-risk actions ---
    governance_reviews = []
    try:
        from mcp.api.governance import get_review_engine
        review_engine = get_review_engine()
        for action in decision.recommended_actions:
            risk = classify_action_risk(action.action_type.value, action.confidence)
            if requires_human_approval(risk):
                existing = [
                    r for r in review_engine.list_reviews()
                    if r.incident_id == incident_id and r.action_type == action.action_type.value
                ]
                if not existing:
                    review = review_engine.create_review(
                        incident_id=incident_id,
                        action_type=action.action_type.value,
                        risk_tier=risk,
                        owner=action.owner,
                        rationale=action.rationale,
                    )
                    governance_reviews.append(review.model_dump(mode="json"))
                else:
                    governance_reviews.append(existing[0].model_dump(mode="json"))
            else:
                governance_reviews.append({
                    "action_type": action.action_type.value,
                    "risk_tier": risk.value,
                    "status": "auto_approved",
                    "owner": action.owner,
                })
    except Exception as exc:
        _log.warning("governance_review_creation_failed: %s", exc)

    # --- D1: fetch NR/DD events for timeline enrichment ---
    newrelic_events: list = []
    datadog_events: list = []
    try:
        from mcp.integrations.newrelic_tool import NewRelicTool
        nr = NewRelicTool()
        nr_incidents = nr.get_incidents() if hasattr(nr, "get_incidents") else []
        for nri in (nr_incidents or [])[:20]:
            newrelic_events.append({
                "timestamp": nri.get("openedAt") or nri.get("timestamp") or datetime.utcnow().isoformat(),
                "source": "newrelic",
                "event_type": "alert",
                "summary": nri.get("title") or nri.get("description") or "New Relic alert",
                "severity": nri.get("priority", "medium"),
            })
    except Exception:
        pass
    try:
        from mcp.integrations.datadog_tool import DatadogTool
        dd = DatadogTool()
        dd_incidents = dd.get_incidents() if hasattr(dd, "get_incidents") else []
        for ddi in (dd_incidents or [])[:20]:
            datadog_events.append({
                "timestamp": ddi.get("created") or ddi.get("timestamp") or datetime.utcnow().isoformat(),
                "source": "datadog",
                "event_type": "incident",
                "summary": ddi.get("title") or ddi.get("name") or "Datadog incident",
                "severity": ddi.get("severity", "medium"),
            })
    except Exception:
        pass

    pipeline_events = []
    if rca and rca.stage_timestamps:
        for stage_name, timestamp in rca.stage_timestamps.items():
            pipeline_events.append({
                "timestamp": timestamp,
                "source": "pipeline",
                "event_type": "stage_transition",
                "summary": f"RCA stage: {stage_name}",
            })

    timeline = build_incident_timeline(
        incident_id=incident_id,
        service=incident_input.service,
        jira_issue={
            "created": incident_issue.get("created"),
            "updated": incident_issue.get("updated"),
            "summary": incident_input.summary,
            "severity": incident_input.severity,
            "status": incident_input.status,
            "url": incident_issue.get("jira_url") or incident_issue.get("url"),
        },
        newrelic_events=newrelic_events,
        datadog_events=datadog_events,
        pipeline_events=pipeline_events,
        impacted_services=rca.impacted_components if rca else [],
        affected_endpoints=[],
        impacted_user_cohorts=[],
    )

    return {
        "incident": _to_incident_card(incident_issue, incident_input).model_dump(mode="json"),
        "decision": decision.model_dump(mode="json"),
        "timeline": timeline.model_dump(mode="json"),
        "governance_reviews": governance_reviews,
        "rca_id": rca.rca_id if rca else None,
        "verification": rca.verification_result.model_dump(mode="json")
        if (rca and rca.verification_result)
        else None,
    }
