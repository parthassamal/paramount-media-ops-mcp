"""
Component blast radius analysis using service dependency graphs.

Determines which test suites need to run based on the service map
from the EvidenceBundle and a local component_map.json fallback.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from mcp.models.evidence_models import EvidenceBundle
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_local_component_map(service_name: str) -> dict:
    """Load local component_map.json as fallback when service map is empty."""
    map_path = DATA_DIR / "component_map.json"
    if not map_path.exists():
        logger.warning("component_map.json not found, returning empty map")
        return {"upstream": [], "downstream": [], "all_affected": []}

    with open(map_path) as f:
        full_map = json.load(f)

    service_data = full_map.get(service_name, {})
    return {
        "upstream": service_data.get("upstream", []),
        "downstream": service_data.get("downstream", []),
        "all_affected": service_data.get("dependencies", [])
    }


def compute_blast_radius(evidence: EvidenceBundle) -> dict:
    """
    Derive blast radius from the EvidenceBundle service map.
    Falls back to local component_map.json if the service map is empty.
    """
    service_name = evidence.service_name

    upstream = []
    downstream = []
    for node in evidence.service_map:
        if service_name in node.upstream_of:
            upstream.append(node.service_name)
        if service_name in node.downstream_of:
            downstream.append(node.service_name)

    all_affected = [n.service_name for n in evidence.service_map]

    if not all_affected:
        fallback = load_local_component_map(service_name)
        upstream = fallback["upstream"]
        downstream = fallback["downstream"]
        all_affected = fallback["all_affected"]
        logger.info("Using local component map fallback", service=service_name)

    return {
        "primary_service": service_name,
        "upstream": upstream,
        "downstream": downstream,
        "all_affected": all_affected,
        "total_blast_radius": len(all_affected),
        "risk_level": _classify_risk(len(all_affected))
    }


def _classify_risk(affected_count: int) -> str:
    if affected_count > 10:
        return "critical"
    elif affected_count > 5:
        return "high"
    elif affected_count > 2:
        return "moderate"
    return "low"


def resolve_test_scope(blast_radius: dict) -> dict:
    """
    Map blast radius to TestRail suite IDs.
    Returns smoke and regression suite IDs that need to be run.
    """
    smoke_suite_ids = []
    regression_suite_ids = []

    suite_map_path = DATA_DIR / "component_map.json"
    suite_map = {}
    if suite_map_path.exists():
        with open(suite_map_path) as f:
            suite_map = json.load(f)

    for service in blast_radius.get("all_affected", []):
        service_data = suite_map.get(service, {})
        if service_data.get("smoke_suite_id"):
            smoke_suite_ids.append(service_data["smoke_suite_id"])
        if service_data.get("regression_suite_id"):
            regression_suite_ids.append(service_data["regression_suite_id"])

    return {
        "smoke_suite_ids": list(set(smoke_suite_ids)),
        "regression_suite_ids": list(set(regression_suite_ids))
    }
