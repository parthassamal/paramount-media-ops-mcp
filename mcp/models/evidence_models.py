"""
Unified evidence model for dual-source observability (New Relic + Datadog).

EvidenceBundle is the single normalized schema consumed by all downstream
pipeline stages. It never knows or cares whether the data came from
New Relic or Datadog.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class SourceType:
    NEW_RELIC = "newrelic"
    DATADOG = "datadog"
    BOTH = "both"


class ServiceMapNode(BaseModel):
    """A node in the service dependency graph."""
    service_name: str
    upstream_of: List[str] = Field(default_factory=list)
    downstream_of: List[str] = Field(default_factory=list)
    criticality: Optional[str] = None  # P1 / P2 / P3


class EvidenceBundle(BaseModel):
    """
    Unified evidence record normalized from New Relic, Datadog, or both.
    Downstream pipeline stages consume only this model.
    """
    bundle_id: str
    captured_at: datetime
    sources: List[Literal["newrelic", "datadog"]]

    # Incident identity
    service_name: str
    environment: str = "production"
    incident_time: Optional[str] = None

    # Error signal
    error_rate: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    affected_endpoints: List[str] = Field(default_factory=list)
    stack_trace: Optional[str] = None
    error_message: Optional[str] = None
    log_lines: List[str] = Field(default_factory=list)

    # Infrastructure
    cpu_anomaly: Optional[bool] = None
    memory_anomaly: Optional[bool] = None
    infra_notes: Optional[str] = None

    # Distributed trace
    trace_id: Optional[str] = None
    trace_summary: Optional[str] = None

    # Service dependency map
    service_map: List[ServiceMapNode] = Field(default_factory=list)

    # Mission-control enrichment fields
    event_timeline: List[dict] = Field(default_factory=list)
    impacted_services: List[str] = Field(default_factory=list)
    impacted_user_cohorts: List[str] = Field(default_factory=list)
    recommended_severity: Optional[str] = None
    evidence_completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    source_references: List[dict] = Field(default_factory=list)

    # Raw payloads (audit trail only)
    raw_newrelic: Optional[dict] = None
    raw_datadog: Optional[dict] = None
