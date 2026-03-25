"""
Phase 2 — AI-Augmented QA Intelligence API Routes

Exposes all seven Phase 2 capabilities via REST endpoints.
"""

from typing import List, Optional
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from mcp.tools.phase2.test_impact import analyze_test_impact
from mcp.tools.phase2.failure_triage import triage_run
from mcp.tools.phase2.suite_hygiene import run_hygiene_check, get_hygiene_report
from mcp.tools.phase2.deployment_risk import score_deployment_risk
from mcp.tools.phase2.pattern_detection import detect_patterns, get_patterns
from mcp.tools.phase2.alert_tests import analyze_alert_coverage, generate_from_alerts
from mcp.tools.phase2.effectiveness import (
    calculate_effectiveness, get_case_effectiveness, get_effectiveness_trends
)
from mcp.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/phase2", tags=["Phase 2 - QA Intelligence"])


# ============================================================================
# 2.1 Test Impact Analysis
# ============================================================================

class TestImpactRequest(BaseModel):
    changed_services: List[str]
    deployment_id: Optional[str] = None
    create_run: bool = True


@router.post("/test-impact/analyze")
async def api_test_impact_analyze(request: TestImpactRequest):
    """
    2.1 Test Impact Analysis
    
    Before a deployment, analyze changed services and create prioritized test run.
    """
    try:
        result = analyze_test_impact(
            changed_services=request.changed_services,
            deployment_id=request.deployment_id,
            create_run=request.create_run
        )
        return result
    except Exception as e:
        logger.error("test_impact_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2.2 Automated Failure Triage
# ============================================================================

class TriageRequest(BaseModel):
    run_id: int
    auto_action: bool = False


@router.post("/triage/run")
async def api_triage_run(request: TriageRequest):
    """
    2.2 Automated Failure Triage
    
    Classify failures in a TestRail run: genuine regression, flaky, env issue, etc.
    """
    try:
        result = triage_run(
            run_id=request.run_id,
            auto_action=request.auto_action
        )
        return result
    except requests.exceptions.HTTPError as e:
        status_code = getattr(getattr(e, "response", None), "status_code", None)
        if status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"TestRail run {request.run_id} not found"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Failed to triage run {request.run_id}: {str(e)}"
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"TestRail communication error: {str(e)}"
        )
    except Exception as e:
        logger.error("triage_run_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2.3 Suite Hygiene
# ============================================================================

@router.post("/suite-hygiene/run")
async def api_suite_hygiene_run(suite_id: Optional[int] = None):
    """
    2.3 Suite Hygiene Check
    
    Scan suite for stale, flaky, duplicate, orphaned, unverified, and coverage gaps.
    """
    try:
        result = run_hygiene_check(suite_id)
        return result
    except Exception as e:
        logger.error("suite_hygiene_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suite-hygiene/report/{report_id}")
async def api_get_hygiene_report(report_id: str):
    """Get a specific hygiene report."""
    result = get_hygiene_report(report_id=report_id)
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return result


@router.get("/suite-hygiene/latest")
async def api_get_latest_hygiene_report(suite_id: Optional[int] = None):
    """Get the most recent hygiene report."""
    result = get_hygiene_report(suite_id=suite_id)
    if not result:
        raise HTTPException(status_code=404, detail="No reports found")
    return result


# ============================================================================
# 2.4 Deployment Risk Score
# ============================================================================

class DeploymentRiskRequest(BaseModel):
    changed_services: List[str]
    deployment_id: Optional[str] = None


@router.post("/deployment-risk/score")
async def api_deployment_risk_score(request: DeploymentRiskRequest):
    """
    2.4 Deployment Risk Score
    
    Compute composite risk score for deployment gating.
    Returns score 0-100 with tier (Low/Medium/High/Hold).
    """
    try:
        result = score_deployment_risk(
            changed_services=request.changed_services,
            deployment_id=request.deployment_id
        )
        return result
    except Exception as e:
        logger.error("deployment_risk_scoring_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2.5 Cross-RCA Pattern Detection
# ============================================================================

@router.post("/patterns/detect")
async def api_detect_patterns():
    """
    2.5 Cross-RCA Pattern Detection
    
    Mine RCA history for structural patterns: temporal, deployment correlation,
    service co-failure, recurring root causes, MTTR trends.
    """
    try:
        result = detect_patterns()
        return result
    except Exception as e:
        logger.error("pattern_detection_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns")
async def api_get_patterns(
    pattern_type: Optional[str] = None,
    service: Optional[str] = None
):
    """Get stored patterns, optionally filtered by type or service."""
    return get_patterns(pattern_type, service)


# ============================================================================
# 2.6 Alert-Driven Test Generation
# ============================================================================

@router.get("/alert-tests/coverage")
async def api_alert_coverage():
    """
    2.6 Alert Coverage Analysis
    
    Analyze which alerts have corresponding test cases and which have gaps.
    """
    try:
        result = analyze_alert_coverage()
        return result
    except Exception as e:
        logger.error("alert_coverage_analysis_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


class AlertTestGenRequest(BaseModel):
    alert_ids: Optional[List[str]] = None
    auto_queue: bool = True


@router.post("/alert-tests/generate")
async def api_generate_alert_tests(request: AlertTestGenRequest):
    """
    2.6 Generate Tests from Alerts
    
    Generate test cases from alert definitions for coverage gaps.
    """
    try:
        result = generate_from_alerts(
            alert_ids=request.alert_ids,
            auto_queue=request.auto_queue
        )
        return result
    except Exception as e:
        logger.error("alert_test_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 2.7 Test Effectiveness Scoring
# ============================================================================

@router.post("/effectiveness/calculate")
async def api_calculate_effectiveness(
    suite_id: Optional[int] = None,
    recalculate: bool = False
):
    """
    2.7 Calculate Test Effectiveness
    
    Score tests on their ability to detect real regressions vs false positives.
    """
    try:
        result = calculate_effectiveness(suite_id, recalculate)
        return result
    except Exception as e:
        logger.error("effectiveness_calculation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/effectiveness/case/{case_id}")
async def api_get_case_effectiveness(case_id: int):
    """Get detailed effectiveness metrics for a specific test case."""
    result = get_case_effectiveness(case_id)
    if not result:
        raise HTTPException(status_code=404, detail="Case not found")
    return result


@router.get("/effectiveness/trends")
async def api_get_effectiveness_trends(
    case_id: Optional[int] = None,
    days: int = 30
):
    """Get effectiveness trends over time."""
    return get_effectiveness_trends(case_id, days)


# ============================================================================
# Summary / Dashboard Endpoint
# ============================================================================

@router.get("/summary")
async def api_phase2_summary():
    """
    Get summary of all Phase 2 capabilities for dashboard.
    """
    try:
        summary = {
            "capabilities": [
                {
                    "id": "test-impact",
                    "name": "Test Impact Analysis",
                    "status": "active",
                    "endpoint": "/api/phase2/test-impact/analyze"
                },
                {
                    "id": "failure-triage",
                    "name": "Automated Failure Triage",
                    "status": "active",
                    "endpoint": "/api/phase2/triage/run"
                },
                {
                    "id": "suite-hygiene",
                    "name": "Suite Hygiene",
                    "status": "active",
                    "endpoint": "/api/phase2/suite-hygiene/run"
                },
                {
                    "id": "deployment-risk",
                    "name": "Deployment Risk Score",
                    "status": "active",
                    "endpoint": "/api/phase2/deployment-risk/score"
                },
                {
                    "id": "pattern-detection",
                    "name": "Pattern Detection",
                    "status": "active",
                    "endpoint": "/api/phase2/patterns/detect"
                },
                {
                    "id": "alert-tests",
                    "name": "Alert-Driven Test Generation",
                    "status": "active",
                    "endpoint": "/api/phase2/alert-tests/generate"
                },
                {
                    "id": "effectiveness",
                    "name": "Test Effectiveness Scoring",
                    "status": "active",
                    "endpoint": "/api/phase2/effectiveness/calculate"
                }
            ],
            "total_capabilities": 7,
            "all_active": True
        }
        
        # Try to get quick metrics
        try:
            latest_hygiene = get_hygiene_report()
            if latest_hygiene:
                summary["hygiene_flags"] = latest_hygiene.get("total_issues", 0)
        except Exception:
            pass
        
        try:
            patterns = get_patterns()
            summary["patterns_detected"] = len(patterns)
        except Exception:
            pass
        
        return summary
    except Exception as e:
        logger.error("phase2_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
