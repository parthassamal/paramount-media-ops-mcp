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
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from config import settings
from mcp.pipeline.orchestrator import RCAPipeline
from mcp.tools.newrelic_tool import capture_newrelic_snapshot, run_nrql
from mcp.tools.datadog_tool import (
    capture_datadog_snapshot, fetch_dd_incidents, fetch_triggered_monitors
)
from mcp.tools.evidence_normalizer import normalize_evidence
from mcp.tools.testrail_tool import get_suites, get_sections
from mcp.db.rca_store import get_rca, get_recent_rcas, get_rcas_by_stage, upsert_rca
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
    query: str = Field(..., min_length=1, description="NRQL query string")

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query cannot be empty")
        return value


class ResumeFromStageRequest(BaseModel):
    """Request to resume a failed pipeline from a specific stage."""
    rca_id: str = Field(..., description="RCA record ID to resume")
    stage: Optional[str] = Field(None, description="Stage to resume from (defaults to last failed stage)")


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


@router.get("/pipeline/{rca_id}/verify", summary="Verify artifact integrity")
async def verify_artifact(rca_id: str):
    """
    Verify the integrity of an RCA artifact using its SHA-256 hash.
    
    For governance and compliance, this confirms the artifact has not been
    modified since the Jira ticket was closed.
    """
    record = get_rca(rca_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"RCA {rca_id} not found")
    
    if record.stage != PipelineStage.COMPLETED:
        return {
            "rca_id": rca_id,
            "verified": None,
            "message": "RCA is not completed - no artifact hash available",
            "stage": record.stage.value
        }
    
    if not record.artifact_hash:
        return {
            "rca_id": rca_id,
            "verified": None,
            "message": "No artifact hash stored (legacy record)",
            "stage": record.stage.value
        }
    
    is_valid = record.verify_artifact_integrity()
    
    return {
        "rca_id": rca_id,
        "verified": is_valid,
        "stored_hash": record.artifact_hash,
        "computed_hash": record.compute_artifact_hash(),
        "message": "Artifact integrity verified" if is_valid else "TAMPER DETECTED - artifact modified after close",
        "closed_at": record.closed_at.isoformat() if record.closed_at else None
    }


@router.get("/pipeline/{rca_id}/metrics", summary="Get RCA cycle time metrics")
async def get_rca_metrics(rca_id: str):
    """
    Get detailed cycle time metrics for an RCA.
    
    For incident-level SLA tracking and engineering leadership reporting.
    """
    record = get_rca(rca_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"RCA {rca_id} not found")
    
    return {
        "rca_id": rca_id,
        "jira_ticket_id": record.jira_ticket_id,
        "stage": record.stage.value,
        "created_at": record.created_at.isoformat(),
        "closed_at": record.closed_at.isoformat() if record.closed_at else None,
        "cycle_time": {
            "total_hours": record.cycle_time_hours,
            "time_to_review_hours": record.time_to_review_hours,
            "review_wait_hours": record.review_wait_hours
        },
        "stage_timestamps": record.stage_timestamps,
        "retry_count": record.retry_count,
        "integrity": {
            "hash_present": bool(record.artifact_hash),
            "verified": record.verify_artifact_integrity() if record.artifact_hash else None
        }
    }


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


@router.post("/pipeline/resume", summary="Resume failed pipeline from stage")
async def resume_pipeline(request: ResumeFromStageRequest):
    """
    Resume a failed pipeline from a specific stage.
    
    Use this to recover from transient errors (NR timeout, TestRail 429, etc.)
    without losing progress. The pipeline state is preserved in SQLite.
    
    **Requirements:**
    - RCA must be in FAILED state
    - Retry count must be < max_retries (default 3)
    
    **Stages:** intake, evidence_capture, summarization, testrail_match,
    test_generation, review_pending, blast_radius, jira_close
    """
    try:
        pipeline = RCAPipeline()
        
        # Parse stage if provided
        resume_stage = None
        if request.stage:
            try:
                resume_stage = PipelineStage(request.stage)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {request.stage}")
        
        record = pipeline.resume_from_stage(request.rca_id, resume_stage)
        return {
            "rca_id": record.rca_id,
            "stage": record.stage.value,
            "retry_count": record.retry_count,
            "message": f"Pipeline resumed successfully, now at {record.stage.value}"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception("Pipeline resume failed", error=str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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


@router.get("/health", summary="Pipeline health and metrics")
async def pipeline_health():
    """
    Pipeline observability endpoint - health status, metrics, and scheduler info.
    
    Use this for monitoring the pipeline itself (not just production).
    Includes dead-man switch status and cycle time metrics.
    """
    from mcp.db.rca_store import get_recent_rcas
    from datetime import datetime, timedelta
    
    # Get scheduler status
    try:
        from mcp.scheduler.background_tasks import scheduler
        scheduler_status = scheduler.get_job_status()
        scheduler_healthy = scheduler.is_healthy
        last_heartbeat = scheduler.last_heartbeat.isoformat()
    except Exception:
        scheduler_status = {"status": "unavailable"}
        scheduler_healthy = False
        last_heartbeat = None
    
    # Calculate pipeline metrics
    recent = get_recent_rcas(limit=100)
    
    completed = [r for r in recent if r.stage == PipelineStage.COMPLETED]
    failed = [r for r in recent if r.stage == PipelineStage.FAILED]
    pending_review = [r for r in recent if r.stage == PipelineStage.REVIEW_PENDING]
    
    # Cycle time stats
    cycle_times = [r.cycle_time_hours for r in completed if r.cycle_time_hours is not None]
    avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else None
    
    # Review wait times
    review_waits = [r.review_wait_hours for r in completed if r.review_wait_hours is not None]
    avg_review_wait = sum(review_waits) / len(review_waits) if review_waits else None
    
    # Failed pipelines that can be retried
    retriable = [r for r in failed if r.can_retry()]
    
    return {
        "status": "healthy" if scheduler_healthy else "degraded",
        "scheduler": scheduler_status,
        "last_heartbeat": last_heartbeat,
        "metrics": {
            "recent_pipelines": len(recent),
            "completed": len(completed),
            "failed": len(failed),
            "pending_review": len(pending_review),
            "retriable_failures": len(retriable),
            "success_rate_percent": round(len(completed) / len(recent) * 100, 1) if recent else 0,
            "avg_cycle_time_hours": round(avg_cycle_time, 2) if avg_cycle_time else None,
            "avg_review_wait_hours": round(avg_review_wait, 2) if avg_review_wait else None
        },
        "sla": {
            "review_sla_hours": settings.rca_review_sla_hours,
            "pending_reviews_count": len(pending_review)
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# RCA Artifact (Step 7 output)
# =============================================================================

# =============================================================================
# Pipeline Status by Jira Key (for Dashboard Integration)
# =============================================================================

@router.get("/status/by-jira/{jira_key}", summary="Get RCA status for a Jira ticket")
async def get_rca_status_by_jira(jira_key: str):
    """
    Check if a Jira ticket has an associated RCA pipeline record.
    Returns pipeline stage and key metadata for dashboard display.
    
    Used by the Production Issues Table to show pipeline stage badges.
    """
    from mcp.db.rca_store import get_rca_by_jira_key
    
    record = get_rca_by_jira_key(jira_key)
    if not record:
        return {
            "has_rca": False,
            "jira_key": jira_key,
            "stage": None,
            "rca_id": None
        }
    
    # Determine if review is needed/overdue
    is_review_pending = record.stage == PipelineStage.REVIEW_PENDING
    
    return {
        "has_rca": True,
        "jira_key": jira_key,
        "rca_id": record.rca_id,
        "stage": record.stage.value,
        "is_duplicate": record.is_duplicate,
        "is_review_pending": is_review_pending,
        "ai_summary": record.ai_summary[:200] if record.ai_summary else None,
        "match_confidence": record.testrail_match_confidence,
        "generated_cases_count": len(record.generated_test_cases) if record.generated_test_cases else 0,
        "created_at": record.created_at.isoformat() if record.created_at else None
    }


@router.get("/status/batch", summary="Get RCA status for multiple Jira tickets")
async def get_rca_status_batch(jira_keys: str):
    """
    Batch lookup of RCA status for multiple Jira tickets.
    Pass comma-separated keys: ?jira_keys=PROD-1,PROD-2,PROD-3
    
    Returns a dict mapping jira_key -> status for efficient dashboard rendering.
    """
    from mcp.db.rca_store import get_rca_by_jira_key
    
    keys = [k.strip() for k in jira_keys.split(",") if k.strip()]
    result = {}
    
    for key in keys:
        record = get_rca_by_jira_key(key)
        if record:
            result[key] = {
                "has_rca": True,
                "rca_id": record.rca_id,
                "stage": record.stage.value,
                "is_review_pending": record.stage == PipelineStage.REVIEW_PENDING
            }
        else:
            result[key] = {"has_rca": False}
    
    return {"statuses": result, "count": len(result)}


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
        },
        "verification": {
            "fix_verified": record.fix_verified,
            "verification_result": record.verification_result.model_dump() if record.verification_result else None,
            "verification_attempts": record.verification_attempts
        },
        "remediation_owners": [r.model_dump() for r in record.remediation_owners]
    }


class RemediationRequest(BaseModel):
    """Request to add a remediation action."""
    action: str = Field(..., description="Description of the remediation action")
    owner: str = Field(..., description="Person/team responsible")
    due_days: int = Field(default=7, description="Days until due date")


@router.post("/pipeline/{rca_id}/verify", summary="Trigger verification run check")
async def verify_rca(rca_id: str):
    """
    Check if the verification run has passed (post-deployment).
    
    This is the evidence-based verification that the fix works.
    If all test cases pass, fix_verified is set to True and Jira can close.
    If any fail, a mini-RCA is triggered.
    """
    try:
        pipeline = RCAPipeline()
        result = pipeline.verify_regression_results(rca_id)
        
        record = get_rca(rca_id)
        
        return {
            "rca_id": rca_id,
            "verification": result.model_dump(),
            "fix_verified": record.fix_verified if record else False,
            "can_close_jira": record.can_close_jira() if record else (False, "Record not found"),
            "message": "Verification passed - fix confirmed" if result.all_passed else f"Verification failed - {result.failed} cases failed"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Verification failed", rca_id=rca_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/{rca_id}/remediation", summary="Add remediation action")
async def add_remediation(rca_id: str, request: RemediationRequest):
    """
    Add a remediation action with owner and due date.
    
    At least one remediation action is REQUIRED before Jira can be closed.
    Each action must have an owner and due date.
    """
    record = get_rca(rca_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"RCA {rca_id} not found")
    
    from datetime import timedelta
    from mcp.models.rca_models import RemediationAction
    
    action = RemediationAction(
        action=request.action,
        owner=request.owner,
        due_date=datetime.utcnow() + timedelta(days=request.due_days)
    )
    
    record.remediation_owners.append(action)
    upsert_rca(record)
    
    return {
        "rca_id": rca_id,
        "remediation_added": action.model_dump(),
        "total_remediations": len(record.remediation_owners),
        "can_close_jira": record.can_close_jira()
    }


@router.get("/pipeline/{rca_id}/can-close", summary="Check if RCA can close Jira")
async def check_can_close(rca_id: str):
    """
    Check if all requirements are met to close the Jira ticket.
    
    Requirements:
    - root_cause present
    - timeline present
    - fix_verified = True (verification run passed)
    - remediation_owners has at least one action with owner/due_date
    """
    record = get_rca(rca_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"RCA {rca_id} not found")
    
    can_close, reason = record.can_close_jira()
    is_valid, missing = record.validate_artifact()
    
    return {
        "rca_id": rca_id,
        "can_close": can_close,
        "reason": reason,
        "validation": {
            "is_valid": is_valid,
            "missing_fields": missing
        },
        "current_state": {
            "stage": record.stage.value,
            "fix_verified": record.fix_verified,
            "has_root_cause": bool(record.ai_summary or record.root_cause),
            "has_timeline": bool(record.timeline or record.stage_timestamps),
            "remediation_count": len(record.remediation_owners),
            "verification_result": record.verification_result.model_dump() if record.verification_result else None
        }
    }
