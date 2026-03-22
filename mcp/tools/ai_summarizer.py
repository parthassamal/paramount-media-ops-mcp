"""
AI Summarizer using Jinja2 structured prompts + optional local LLM.

Generates structured incident summaries from EvidenceBundle + Jira fields.
When no LLM is available, falls back to template-based extraction.
"""

import json
import httpx
from typing import Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import settings
from mcp.models.evidence_models import EvidenceBundle
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"

_jinja_env = Environment(
    loader=FileSystemLoader(str(PROMPT_DIR)),
    trim_blocks=True,
    lstrip_blocks=True
)


def _call_local_llm(prompt: str, max_tokens: int = 2048) -> Optional[str]:
    """Call the local LLM endpoint (Ollama-compatible). Returns None if unavailable."""
    if not settings.local_llm_url:
        return None

    try:
        resp = httpx.post(
            settings.local_llm_url,
            json={
                "model": settings.local_llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens}
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        logger.warning("Local LLM call failed, using template fallback", error=str(e))
        return None


def summarize_incident(jira_ticket: dict, evidence: EvidenceBundle) -> str:
    """
    Generate a structured incident summary.
    Uses local LLM if available, otherwise falls back to template extraction.
    """
    template = _jinja_env.get_template("summarize_incident.j2")
    rendered_prompt = template.render(
        jira=jira_ticket,
        evidence=evidence.model_dump(),
        sources=", ".join(evidence.sources)
    )

    llm_response = _call_local_llm(rendered_prompt)
    if llm_response:
        logger.info("Summary generated via LLM", rca=jira_ticket.get("id"))
        return llm_response

    # Template-based fallback when no LLM is available
    summary_parts = [
        f"**Incident**: {jira_ticket.get('summary', 'Unknown')}",
        f"**Service**: {evidence.service_name}",
        f"**Sources**: {', '.join(evidence.sources)}",
    ]

    if evidence.error_rate is not None:
        summary_parts.append(f"**Error Rate**: {evidence.error_rate:.2%}")
    if evidence.p99_latency_ms is not None:
        summary_parts.append(f"**P99 Latency**: {evidence.p99_latency_ms:.0f}ms")
    if evidence.error_message:
        summary_parts.append(f"**Error**: {evidence.error_message}")
    if evidence.stack_trace:
        truncated = evidence.stack_trace[:500]
        summary_parts.append(f"**Stack Trace**:\n```\n{truncated}\n```")
    if evidence.affected_endpoints:
        summary_parts.append(f"**Affected**: {', '.join(evidence.affected_endpoints[:5])}")
    if evidence.service_map:
        deps = [n.service_name for n in evidence.service_map[:5]]
        summary_parts.append(f"**Dependencies**: {', '.join(deps)}")

    logger.info("Summary generated via template fallback", rca=jira_ticket.get("id"))
    return "\n".join(summary_parts)


def analyze_blast_radius(evidence: EvidenceBundle) -> dict:
    """Analyze blast radius from service map in the evidence bundle."""
    template = _jinja_env.get_template("analyze_blast_radius.j2")
    rendered_prompt = template.render(
        service_name=evidence.service_name,
        service_map=[n.model_dump() for n in evidence.service_map],
        affected_endpoints=evidence.affected_endpoints
    )

    llm_response = _call_local_llm(rendered_prompt)
    if llm_response:
        try:
            return json.loads(llm_response)
        except json.JSONDecodeError:
            pass

    # Fallback: derive from service map
    upstream = []
    downstream = []
    for node in evidence.service_map:
        if evidence.service_name in node.upstream_of:
            upstream.append(node.service_name)
        if evidence.service_name in node.downstream_of:
            downstream.append(node.service_name)

    return {
        "primary_service": evidence.service_name,
        "upstream_services": upstream,
        "downstream_services": downstream,
        "all_affected": [n.service_name for n in evidence.service_map],
        "total_blast_radius": len(evidence.service_map),
        "risk_level": "critical" if len(evidence.service_map) > 5 else "moderate"
    }
