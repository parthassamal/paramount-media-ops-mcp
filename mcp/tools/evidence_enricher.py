"""
Evidence enrichment helpers to attach timeline, blast radius, and completeness.
"""

from __future__ import annotations

from typing import Dict, List

from mcp.models.evidence_models import EvidenceBundle
from mcp.models.timeline_models import IncidentTimeline


def enrich_evidence_bundle(
    bundle: EvidenceBundle,
    timeline: IncidentTimeline,
    impacted_user_cohorts: List[str] | None = None,
    source_references: List[Dict[str, str]] | None = None,
) -> EvidenceBundle:
    """
    Populate control-plane enrichment fields on an EvidenceBundle.
    """
    bundle.event_timeline = [event.model_dump(mode="json") for event in timeline.events]
    bundle.impacted_services = timeline.impacted_services
    bundle.affected_endpoints = timeline.affected_endpoints or bundle.affected_endpoints
    bundle.impacted_user_cohorts = impacted_user_cohorts or timeline.impacted_user_cohorts
    bundle.recommended_severity = timeline.recommended_severity
    bundle.evidence_completeness_score = timeline.evidence_completeness_score
    bundle.source_references = source_references or [
        reference.model_dump(mode="json")
        for event in timeline.events
        for reference in event.references
    ]
    return bundle
