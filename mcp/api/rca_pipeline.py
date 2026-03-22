"""
RCA Pipeline API endpoints -- v2 MCP tool registration.

Exposes the full pipeline:
- Evidence capture (dual-source)
- Pipeline execution
- Human review gate + TestRail write
- TestRail browsing (suites/sections)
- Datadog + New Relic direct queries
- Review queue management
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from config import settings
from mcp.pipeline.orchestrator import RCAPipeline
from mcp.tools.newrelic_tool import capture_newrelic_snapshot, run_nrql
from mcp.tools.datadog_tool import (
    capture_datadog_snapshot, fetch_dd_incidents, fetch_triggered_monitors
)
from mcp.tools.evidence_normalizer import normalize_evidence
from mcp.tools.testrail_tool import get_suites, get_sections
from mcp.db.rca_store import get_rca, get_recent_rcas, get_rcas_by_stage
from mcp.db.review_store import get_pending_reviews, reject_review
from mcp.models.rca_models import PipelineStage
from mcp.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/rca",
    tags=["RCA Pipeline"],
    responses={500: {"description": "Internal server error"}}
)


# =============================================================================
# Request/Response Models
# =============================================================================

class RunPipelineRequest(BaseModel):
    """Request to start the full RCA pipeline for a Jira ticket."""
    id: str = Field(..., description="Jira ticket ID (e.g., PROD-1234)")
    summary: str = Field(..., description="Ticket summary/title")
    service: str = Field(default="", description="Affected service name")
    priority: str = Field(default="Medium", description="Ticket priority")
    description: str = Field(default="", description="Full ticket description")
    reproduction_steps: List[str] = Field(default_factory=list)
    incident_time: Optional[str] = Field(default=None, description="ISO timestamp of incident")
    reporter: Optional[str] = None


class CaptureEvidenceRequest(BaseModel):
    """Request to capture pre-mitigation evidence from observability tools."""
    service_name: str = Field(..., description="Service to capture evidence for")
    incident_time: Optional[str] = Field(default=None, description="ISO timestamp")


class ApproveReviewRequest(BaseModel):
    """Request to approve generated test cases after human review."""
    rca_id: str = Field(..., description="RCA record ID")
    reviewer_id: str = Field(..., description="Reviewer's user ID")
    notes: str = Field(default="", description="Review notes")
    approved_case_indices: Optional[List[int]] = Field(
        default=None,
        description="Indices of cases to approve (None = approve all passing)"
    )


class RejectReviewRequest(BaseModel):
    """Request to reject generated test cases."""
    review_id: str
    reviewer_id: str
    notes: str = ""


class NRQLRequest(BaseModel):
    """NRQL query for New Relic."""
    query: str = Field(..., description="NRQL query string")


# =============================================================================
# Pipeline Endpoints
# =============================================================================

@router.post("/pipeline/run", summary="Run full RCA pipeline")
async def run_pipeline(request: RunPipelineRequest):
    """
    Execute the full RCA pipeline for a production incident.

    Flow: Intake -> Evidence Capture -> AI Summary -> TestRail Match ->
    [Test Generation -> Human Review] -> Blast Radius -> Close

    Pipeline pauses at REVIEW_PENDING if new test cases need human approval.
    """
    try:
        pipeline = RCAPipeline()
        record = pipeline.run(request.model_dump())
        return {
            "rca_id": record.rca_id,
            "stage": record.stage.value,
            "is_duplicate": record.is_duplicate,
            "evidence_sources": record.error_metrics.get("sources", []) if record.error_metrics else [],
            "match_confidence": record.testrail_match_confidence,
            "match_score": record.match_score,
            "generated_cases_count": len(record.generated_test_cases) if record.generated_test_cases else 0,
            "ai_summary": record.ai_summary
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.exception("Pipeline execution failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/pipeline/{rca_id}", summary="Get RCA pipeline state")
async def get_pipeline_state(rca_id: str):
    """Fetch the current state of an RCA pipeline run."""
    record = get_rca(rca_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"RCA {rca_id} not found")
    return record.model_dump()


@router.get("/pipeline", summary="List recent RCA records")
async def list_pipelines(limit: int = 50, stage: Optional[str] = None):
    """List recent RCA pipeline records, optionally filtered by stage."""
    if stage:
        try:
            pipeline_stage = PipelineStage(stage)
            records = get_rcas_by_stage(pipeline_stage)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    else:
        records = get_recent_rcas(limit)

    return {
        "records": [r.model_dump() for r in records],
        "count": len(records)
    }


# =============================================================================
# Evidence Capture
# =============================================================================

@router.post("/evidence/capture", summary="Capture pre-mitigation evidence")
async def capture_evidence(request: CaptureEvidenceRequest):
    """
    Capture pre-mitigation evidence from configured observability sources.
    MUST be called BEFORE any restart or rollback -- state is lost after mitigation.

    Source determined by OBSERVABILITY_SOURCE config (newrelic | datadog | both).
    """
    nr_snapshot, dd_snapshot = None, None

    if settings.observability_source in ("newrelic", "both"):
        try:
            nr_snapshot = capture_newrelic_snapshot(
                request.service_name, request.incident_time
            )
        except Exception as e:
            logger.error("New Relic capture failed", error=str(e))

    if settings.observability_source in ("datadog", "both"):
        try:
            dd_snapshot = capture_datadog_snapshot(request.service_name)
        except Exception as e:
            logger.error("Datadog capture failed", error=str(e))

    bundle = normalize_evidence(request.service_name, nr_snapshot, dd_snapshot)
    return {
        "bundle_id": bundle.bundle_id,
        "sources": bundle.sources,
        "service_name": bundle.service_name,
        "error_rate": bundle.error_rate,
        "p99_latency_ms": bundle.p99_latency_ms,
        "has_stack_trace": bool(bundle.stack_trace),
        "service_map_size": len(bundle.service_map),
        "log_lines_count": len(bundle.log_lines)
    }


# =============================================================================
# Human Review Gate + TestRail Write
# =============================================================================

@router.post("/review/approve", summary="Approve and write to TestRail")
async def approve_and_write(request: ApproveReviewRequest):
    """
    Human review gate + TestRail write in one call.
    Approves generated cases, writes them to TestRail, creates verification run.
    """
    try:
        pipeline = RCAPipeline()
        record = pipeline.resume_after_review(
            request.rca_id, request.reviewer_id, request.notes
        )
        return {
            "stage": record.stage.value,
            "testrail_cases_created": record.testrail_created_case_ids,
            "verification_run_id": record.testrail_verification_run_id,
            "regression_scope": record.regression_scope,
            "impacted_components": record.impacted_components
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Review approval failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/review/reject", summary="Reject generated test cases")
async def reject_review_endpoint(request: RejectReviewRequest):
    """Reject generated test cases. RCA will be marked as review_rejected."""
    try:
        item = reject_review(request.review_id, request.reviewer_id, request.notes)
        return {"review_id": item.review_id, "status": item.status.value}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/review/pending", summary="Get pending reviews")
async def list_pending_reviews():
    """List all review items pending human approval. Marks overdue items as expired."""
    items = get_pending_reviews()
    return {
        "pending": [
            {
                "review_id": i.review_id,
                "rca_id": i.rca_id,
                "jira_ticket_id": i.jira_ticket_id,
                "created_at": i.created_at.isoformat(),
                "sla_deadline": i.sla_deadline.isoformat(),
                "status": i.status.value,
                "cases_count": len(i.generated_cases),
                "is_overdue": i.is_overdue
            }
            for i in items
        ],
        "count": len(items)
    }


# =============================================================================
# TestRail Browse (for setup/configuration)
# =============================================================================

@router.get("/testrail/suites", summary="List TestRail suites")
async def list_testrail_suites():
    """List all TestRail suites. Use to find suite_id for config."""
    return get_suites()


@router.get("/testrail/sections/{suite_id}", summary="List TestRail sections")
async def list_testrail_sections(suite_id: int):
    """List sections within a TestRail suite. Use to find TESTRAIL_RCA_SECTION_ID."""
    return get_sections(suite_id)


# =============================================================================
# Direct Observability Queries
# =============================================================================

@router.get("/datadog/incidents/{service_name}", summary="Fetch Datadog incidents")
async def dd_incidents(service_name: str):
    """Pull recent incidents from Datadog for a specific service."""
    return fetch_dd_incidents(service_name)


@router.get("/datadog/monitors/{service_name}", summary="Fetch Datadog triggered monitors")
async def dd_monitors(service_name: str):
    """Pull currently triggered monitors from Datadog for a service."""
    return fetch_triggered_monitors(service_name)


@router.post("/newrelic/nrql", summary="Run NRQL query")
async def nrql_query(request: NRQLRequest):
    """Run an arbitrary NRQL query against New Relic."""
    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")
    return {"results": run_nrql(request.query)}


@router.get("/config/observability", summary="Get observability config")
async def get_observability_config():
    """Show current observability source configuration."""
    return {
        "observability_source": settings.observability_source,
        "newrelic_enabled": settings.newrelic_enabled,
        "newrelic_configured": bool(settings.newrelic_api_key),
        "datadog_enabled": settings.datadog_enabled,
        "datadog_configured": bool(settings.dd_api_key and settings.dd_app_key),
        "testrail_configured": bool(settings.testrail_url and settings.testrail_api_key),
        "local_llm_configured": bool(settings.local_llm_url)
    }


# =============================================================================
# RCA Artifact (Step 7 output)
# =============================================================================

@router.get("/artifact/{rca_id}", summary="Get full RCA artifact for Jira close-out")
async def get_rca_artifact(rca_id: str):
    """
    Returns the complete RCA artifact -- the structured payload
    that gets attached to the Jira ticket when the pipeline closes it.

    Includes: root cause, evidence sources, TestRail case/run IDs,
    blast radius, test scope, and remediation owners.
    """
    record = get_rca(rca_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"RCA {rca_id} not found")

    return {
        "rca_id": record.rca_id,
        "jira_ticket_id": record.jira_ticket_id,
        "stage": record.stage.value,
        "jira_closed": record.jira_closed,
        "root_cause_summary": record.ai_summary,
        "evidence": {
            "bundle_id": record.evidence_bundle_id,
            "sources": record.error_metrics.get("sources", []) if record.error_metrics else [],
            "error_rate": record.error_metrics.get("error_rate") if record.error_metrics else None,
            "p99_latency_ms": record.error_metrics.get("p99_latency_ms") if record.error_metrics else None,
            "stack_trace_available": bool(record.stack_trace)
        },
        "testrail_match": {
            "confidence": record.testrail_match_confidence,
            "score": record.match_score,
            "matched_case_id": record.matched_test_case_id,
            "automation_covered": record.automation_covered,
            "automation_gap_reason": record.automation_gap_reason
        },
        "testrail_write": {
            "created_case_ids": record.testrail_created_case_ids or [],
            "verification_run_id": record.testrail_verification_run_id,
            "regression_run_id": record.regression_run_id
        },
        "blast_radius": {
            "impacted_components": record.impacted_components or [],
            "smoke_scope": record.smoke_scope or [],
            "regression_scope": record.regression_scope or []
        },
        "review": {
            "reviewer_id": record.reviewer_id,
            "approved_at": record.human_review_approved_at.isoformat() if record.human_review_approved_at else None,
            "notes": record.review_notes
        },
        "duplicate_detection": {
            "is_duplicate": record.is_duplicate,
            "duplicate_of": record.duplicate_of,
            "severity_escalated": record.severity_escalated
        }
    }
