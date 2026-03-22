"""
Test case generator with LLM-as-judge scoring.

Generates structured test cases from incident evidence and
scores each case on a 0-5 scale using a second LLM pass.
"""

import json
import httpx
from typing import List, Dict, Any, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import settings
from mcp.models.rca_models import RCARecord
from mcp.models.evidence_models import EvidenceBundle
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

PROMPT_DIR = Path(__file__).parent.parent.parent / "prompts"

_jinja_env = Environment(
    loader=FileSystemLoader(str(PROMPT_DIR)),
    trim_blocks=True,
    lstrip_blocks=True
)


def _call_local_llm(prompt: str, max_tokens: int = 4096) -> Optional[str]:
    """Call local LLM. Returns None if unavailable."""
    if not settings.local_llm_url:
        return None

    try:
        resp = httpx.post(
            settings.local_llm_url,
            json={
                "model": settings.local_llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.3}
            },
            timeout=180
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        logger.warning("Local LLM call failed", error=str(e))
        return None


def generate_test_cases(record: RCARecord, evidence: EvidenceBundle) -> List[Dict[str, Any]]:
    """
    Generate test cases from incident evidence.
    Uses LLM if available, otherwise generates structured templates.
    """
    template = _jinja_env.get_template("generate_test_cases.j2")
    rendered_prompt = template.render(
        summary=record.ai_summary or record.jira_ticket_id,
        service=evidence.service_name,
        error_message=evidence.error_message,
        stack_trace=evidence.stack_trace,
        affected_endpoints=evidence.affected_endpoints,
        error_rate=evidence.error_rate,
        p99_latency=evidence.p99_latency_ms,
        log_lines=evidence.log_lines[:10]
    )

    llm_response = _call_local_llm(rendered_prompt)
    if llm_response:
        try:
            cases = json.loads(llm_response)
            if isinstance(cases, list):
                scored = _score_cases(cases, evidence)
                logger.info("Test cases generated via LLM", count=len(scored))
                return scored
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON, using template fallback")

    # Template-based fallback
    cases = _generate_template_cases(record, evidence)
    scored = _score_cases(cases, evidence)
    logger.info("Test cases generated via template", count=len(scored))
    return scored


def _generate_template_cases(record: RCARecord, evidence: EvidenceBundle) -> List[Dict[str, Any]]:
    """Generate structured test cases without LLM."""
    cases = []

    # Verification test: reproduce the original issue
    cases.append({
        "title": f"Verify fix for: {record.jira_ticket_id} - {evidence.service_name} error",
        "type": "verification",
        "priority": "high",
        "preconditions": f"Service {evidence.service_name} is deployed with the fix",
        "steps": [
            {
                "action": f"Deploy the fix for {record.jira_ticket_id} to staging",
                "expected": "Deployment succeeds without errors"
            },
            {
                "action": f"Reproduce the original scenario that caused: {evidence.error_message or 'the incident'}",
                "expected": "The error no longer occurs"
            },
            {
                "action": "Check error rate metrics in monitoring",
                "expected": f"Error rate is below threshold ({evidence.error_rate or 'N/A'} was the incident rate)"
            }
        ]
    })

    # Regression test: ensure related functionality still works
    if evidence.affected_endpoints:
        for endpoint in evidence.affected_endpoints[:3]:
            cases.append({
                "title": f"Regression: {endpoint} operates normally after {record.jira_ticket_id} fix",
                "type": "regression",
                "priority": "medium",
                "preconditions": f"Fix for {record.jira_ticket_id} deployed",
                "steps": [
                    {
                        "action": f"Send valid request to {endpoint}",
                        "expected": "Response returns 200 within SLA"
                    },
                    {
                        "action": f"Send edge-case request to {endpoint}",
                        "expected": "Graceful error handling, no 500"
                    }
                ]
            })

    # Smoke test: service health after fix
    cases.append({
        "title": f"Smoke: {evidence.service_name} health check after {record.jira_ticket_id}",
        "type": "smoke",
        "priority": "high",
        "preconditions": "Fix deployed to environment",
        "steps": [
            {
                "action": f"Hit {evidence.service_name} health endpoint",
                "expected": "Returns 200 OK"
            },
            {
                "action": "Verify downstream dependencies are reachable",
                "expected": "All dependency checks pass"
            },
            {
                "action": f"Check p99 latency is within SLA",
                "expected": f"P99 latency < {(evidence.p99_latency_ms or 1000) * 1.2:.0f}ms"
            }
        ]
    })

    return cases


def _score_cases(cases: List[Dict[str, Any]], evidence: EvidenceBundle) -> List[Dict[str, Any]]:
    """
    LLM-as-judge scoring. Score each case 0-5 on:
    - Relevance to the incident
    - Completeness of steps
    - Testability (clear pass/fail criteria)
    Falls back to heuristic scoring when LLM unavailable.
    """
    for case in cases:
        # Try LLM scoring
        score_prompt = (
            f"Score this test case 0-5 for a {evidence.service_name} incident.\n"
            f"Incident: {evidence.error_message}\n"
            f"Test case: {json.dumps(case, indent=2)}\n"
            f"Respond with only a JSON object: {{\"score\": N, \"reason\": \"...\"}}"
        )
        llm_score = _call_local_llm(score_prompt, max_tokens=200)
        if llm_score:
            try:
                score_data = json.loads(llm_score)
                case["judge_score"] = score_data.get("score", 3)
                case["judge_reason"] = score_data.get("reason", "")
                case["judge_passed"] = case["judge_score"] >= 3
                continue
            except (json.JSONDecodeError, KeyError):
                pass

        # Heuristic scoring fallback
        score = 3  # Base score
        if case.get("steps") and len(case["steps"]) >= 2:
            score += 1
        if case.get("preconditions"):
            score += 0.5
        if case.get("type") == "verification":
            score += 0.5

        case["judge_score"] = min(score, 5)
        case["judge_reason"] = "Heuristic scoring (LLM unavailable)"
        case["judge_passed"] = case["judge_score"] >= 3

    return cases
