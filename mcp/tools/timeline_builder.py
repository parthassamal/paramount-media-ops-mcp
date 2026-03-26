"""
Build a normalized incident timeline from heterogeneous sources.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from mcp.models.timeline_models import EvidenceReference, IncidentTimeline, TimelineEvent


def _coerce_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _parse_event(event: Dict[str, Any], fallback_source: str) -> Optional[TimelineEvent]:
    timestamp = _coerce_datetime(event.get("timestamp") or event.get("created_at") or event.get("time"))
    if not timestamp:
        return None
    refs: List[EvidenceReference] = []
    for ref in event.get("references", []):
        if not isinstance(ref, dict):
            continue
        refs.append(
            EvidenceReference(
                source=str(ref.get("source", fallback_source)),
                ref_id=str(ref.get("ref_id", "")),
                url=ref.get("url"),
            )
        )
    return TimelineEvent(
        timestamp=timestamp,
        source=str(event.get("source", fallback_source)),
        event_type=str(event.get("event_type", "observation")),
        summary=str(event.get("summary", "event")),
        details=event.get("details"),
        severity=event.get("severity"),
        references=refs,
    )


def _completeness_score(events: List[TimelineEvent], required_sources: Iterable[str]) -> float:
    required = {s for s in required_sources if s}
    if not required:
        return 0.0
    seen = {event.source for event in events}
    return round(min(len(required.intersection(seen)) / len(required), 1.0), 2)


def build_incident_timeline(
    incident_id: str,
    service: str,
    jira_issue: Dict[str, Any],
    newrelic_events: Optional[List[Dict[str, Any]]] = None,
    datadog_events: Optional[List[Dict[str, Any]]] = None,
    pipeline_events: Optional[List[Dict[str, Any]]] = None,
    impacted_services: Optional[List[str]] = None,
    affected_endpoints: Optional[List[str]] = None,
    impacted_user_cohorts: Optional[List[str]] = None,
) -> IncidentTimeline:
    """
    Construct an ordered incident timeline across Jira, alerts, and pipeline events.
    """
    events: List[TimelineEvent] = []

    # Add canonical Jira events.
    created_at = _coerce_datetime(jira_issue.get("created"))
    if created_at:
        events.append(
            TimelineEvent(
                timestamp=created_at,
                source="jira",
                event_type="ticket_created",
                summary=f"Incident {incident_id} created",
                details=jira_issue.get("summary"),
                severity=jira_issue.get("severity"),
                references=[
                    EvidenceReference(
                        source="jira",
                        ref_id=incident_id,
                        url=jira_issue.get("url"),
                    )
                ],
            )
        )

    updated_at = _coerce_datetime(jira_issue.get("updated"))
    if updated_at:
        events.append(
            TimelineEvent(
                timestamp=updated_at,
                source="jira",
                event_type="ticket_updated",
                summary=f"Incident {incident_id} updated",
                details=f"Current status: {jira_issue.get('status', 'unknown')}",
                severity=jira_issue.get("severity"),
            )
        )

    for item in newrelic_events or []:
        event = _parse_event(item, fallback_source="newrelic")
        if event:
            events.append(event)
    for item in datadog_events or []:
        event = _parse_event(item, fallback_source="datadog")
        if event:
            events.append(event)
    for item in pipeline_events or []:
        event = _parse_event(item, fallback_source="pipeline")
        if event:
            events.append(event)

    events.sort(key=lambda item: item.timestamp)
    start_time = events[0].timestamp if events else None
    end_time = events[-1].timestamp if events else None

    severity = str(jira_issue.get("severity", "medium")).lower()
    recommended_severity = "high" if severity == "critical" else severity

    required_sources = {"jira", "newrelic", "datadog", "pipeline"}
    completeness = _completeness_score(events, required_sources)

    return IncidentTimeline(
        incident_id=incident_id,
        service=service,
        start_time=start_time,
        end_time=end_time,
        recommended_severity=recommended_severity,
        impacted_services=impacted_services or [],
        affected_endpoints=affected_endpoints or [],
        impacted_user_cohorts=impacted_user_cohorts or [],
        evidence_completeness_score=completeness,
        events=events,
    )
