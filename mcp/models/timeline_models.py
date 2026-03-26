"""Timeline models for incident chronology rendering."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    """Source reference for timeline and evidence explainability."""

    source: str
    ref_id: str
    url: Optional[str] = None


class TimelineEvent(BaseModel):
    """Single event in an incident timeline."""

    timestamp: datetime
    source: str
    event_type: str
    summary: str
    details: Optional[str] = None
    severity: Optional[str] = None
    references: List[EvidenceReference] = Field(default_factory=list)


class IncidentTimeline(BaseModel):
    """Chronological incident timeline with completeness scoring."""

    incident_id: str
    service: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recommended_severity: Optional[str] = None
    impacted_services: List[str] = Field(default_factory=list)
    affected_endpoints: List[str] = Field(default_factory=list)
    impacted_user_cohorts: List[str] = Field(default_factory=list)
    evidence_completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    events: List[TimelineEvent] = Field(default_factory=list)
