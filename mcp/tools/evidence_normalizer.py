"""
Evidence Normalizer -- merges raw New Relic and Datadog payloads into a single
EvidenceBundle. This abstraction makes the rest of the pipeline source-agnostic.
"""

import uuid
from datetime import datetime
from typing import Optional

from config import settings
from mcp.models.evidence_models import EvidenceBundle, ServiceMapNode
from mcp.utils.logger import get_logger

logger = get_logger(__name__)


def normalize_evidence(
    service_name: str,
    nr_snapshot: Optional[dict] = None,
    dd_snapshot: Optional[dict] = None
) -> EvidenceBundle:
    """
    Merge New Relic and/or Datadog snapshots into a unified EvidenceBundle.
    Handles missing sources gracefully -- either or both can be None.
    """
    sources = []
    error_rate = None
    p99_latency = None
    stack_trace = None
    error_message = None
    log_lines = []
    affected_endpoints = []
    service_map = []

    # Extract from New Relic
    if nr_snapshot:
        sources.append("newrelic")
        apm = (nr_snapshot.get("apm", {}).get("actor", {})
               .get("entity", {}).get("apmSummary", {}))
        if apm:
            error_rate = apm.get("errorRate")
            p99_latency = apm.get("responseTimeAverage")

        if nr_snapshot.get("stack_trace"):
            stack_trace = nr_snapshot["stack_trace"]

        # Service map from entity relationships
        related = (nr_snapshot.get("service_map", {}).get("actor", {})
                   .get("entity", {}).get("relatedEntities", {}).get("results", []))
        for rel in related:
            target_name = rel.get("target", {}).get("entity", {}).get("name")
            rel_type = rel.get("type")
            if target_name:
                node = ServiceMapNode(service_name=target_name)
                if rel_type == "CALLS":
                    node.downstream_of.append(service_name)
                elif rel_type == "CALLED_BY":
                    node.upstream_of.append(service_name)
                service_map.append(node)

    # Extract from Datadog
    if dd_snapshot:
        sources.append("datadog")

        dd_logs = dd_snapshot.get("error_logs", [])
        log_lines = [l.get("message", "") for l in dd_logs if l.get("message")]
        if not stack_trace and log_lines:
            stack_trace = "\n".join(log_lines[:10])

        dd_incidents = dd_snapshot.get("incidents", [])
        if dd_incidents:
            error_message = dd_incidents[0].get("title")

        for monitor in dd_snapshot.get("triggered_monitors", []):
            if monitor.get("name"):
                affected_endpoints.append(monitor["name"])

    # Deduplicate service map nodes
    seen = set()
    deduped_map = []
    for node in service_map:
        if node.service_name not in seen:
            seen.add(node.service_name)
            deduped_map.append(node)

    bundle = EvidenceBundle(
        bundle_id=str(uuid.uuid4()),
        captured_at=datetime.utcnow(),
        sources=sources,
        service_name=service_name,
        error_rate=error_rate,
        p99_latency_ms=p99_latency,
        stack_trace=stack_trace,
        error_message=error_message,
        log_lines=log_lines[:20],
        affected_endpoints=affected_endpoints,
        service_map=deduped_map,
        raw_newrelic=nr_snapshot,
        raw_datadog=dd_snapshot
    )

    logger.info(
        "Evidence normalized",
        bundle_id=bundle.bundle_id,
        sources=sources,
        has_stack_trace=bool(stack_trace),
        service_map_nodes=len(deduped_map)
    )
    return bundle
