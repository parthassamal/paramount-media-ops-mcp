"""
JIRA REST API Endpoints with comprehensive Swagger documentation.

Provides production issue tracking, project management, and analytics.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime

from mcp.integrations import JiraConnector
from config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/jira", tags=["JIRA Production Tracking"])

# Initialize JIRA connector
jira = JiraConnector(mock_mode=settings.mock_mode)


# Pydantic Models
class JiraIssue(BaseModel):
    """JIRA Issue model for API responses."""
    id: str = Field(..., description="JIRA issue ID")
    key: str = Field(..., description="JIRA issue key (e.g., PROD-123)")
    summary: str = Field(..., description="Issue summary/title")
    status: str = Field(..., description="Current status")
    severity: str = Field(..., description="Issue severity level")
    show_name: Optional[str] = Field(None, description="Related show/content name")
    cost_impact: Optional[float] = Field(None, description="Estimated cost impact in USD")
    delay_days: Optional[int] = Field(None, description="Days of delay caused")
    created: str = Field(..., description="Creation timestamp")
    updated: str = Field(..., description="Last updated timestamp")
    assignee: Optional[str] = Field(None, description="Assigned team member")
    url: str = Field(..., description="JIRA issue URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "10001",
                "key": "PROD-123",
                "summary": "Color grading delays for Yellowstone S5",
                "status": "In Progress",
                "severity": "Critical",
                "show_name": "Yellowstone",
                "cost_impact": 50000.0,
                "delay_days": 3,
                "created": "2025-12-15T10:00:00Z",
                "updated": "2025-12-18T14:30:00Z",
                "assignee": "Jane Smith",
                "url": "https://paramounthackathon.atlassian.net/browse/PROD-123"
            }
        }


class CreateIssueRequest(BaseModel):
    """Request model for creating a new JIRA issue."""
    project_key: str = Field(..., description="JIRA project key (e.g., PROD)")
    summary: str = Field(..., description="Issue summary/title")
    description: str = Field(..., description="Detailed issue description")
    issue_type: str = Field(default="Bug", description="Issue type (Bug, Task, Story, etc.)")
    severity: Optional[str] = Field(None, description="Severity level")
    show_name: Optional[str] = Field(None, description="Related show/content name")
    cost_impact: Optional[float] = Field(None, description="Estimated cost impact in USD")
    delay_days: Optional[int] = Field(None, description="Expected days of delay")

    class Config:
        json_schema_extra = {
            "example": {
                "project_key": "PROD",
                "summary": "Audio sync issue in final render",
                "description": "Audio is out of sync by 200ms in episode 3 final cut",
                "issue_type": "Bug",
                "severity": "High",
                "show_name": "1923",
                "cost_impact": 25000.0,
                "delay_days": 2
            }
        }


class JiraStats(BaseModel):
    """JIRA statistics and analytics."""
    total_issues: int = Field(..., description="Total number of issues")
    by_status: Dict[str, int] = Field(..., description="Issue count by status")
    by_severity: Dict[str, int] = Field(..., description="Issue count by severity")
    total_cost_impact: float = Field(..., description="Total estimated cost impact")
    average_delay_days: float = Field(..., description="Average delay in days")
    critical_count: int = Field(..., description="Number of critical issues")


# API Endpoints

@router.get(
    "/issues",
    response_model=List[JiraIssue],
    summary="Get Production Issues",
    description="""
    Retrieve production issues from JIRA with optional filtering.
    
    **Filters:**
    - `status`: Filter by issue status (e.g., "Open", "In Progress", "Resolved")
    - `severity`: Filter by severity level (e.g., "Critical", "High", "Medium", "Low")
    - `show_name`: Filter by show/content name
    - `days_since_created`: Only issues created within last N days
    - `limit`: Maximum number of issues to return
    
    **Response:** List of JIRA issues with full details including cost impact and delays.
    """,
    responses={
        200: {"description": "Successfully retrieved issues"},
        500: {"description": "Failed to fetch issues from JIRA"}
    }
)
async def get_production_issues(
    status: Optional[str] = Query(None, description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    show_name: Optional[str] = Query(None, description="Filter by show name"),
    days_since_created: Optional[int] = Query(None, description="Issues from last N days"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum issues to return")
) -> List[JiraIssue]:
    """Get production issues with optional filters."""
    try:
        logger.info(
            "jira_issues_request",
            status=status,
            severity=severity,
            show_name=show_name,
            days_since_created=days_since_created
        )
        
        issues = jira.get_production_issues(
            status=status,
            severity=severity,
            show_name=show_name,
            days_since_created=days_since_created
        )
        
        # Map integration fields to API model fields
        mapped_issues = []
        for issue in issues[:limit]:
            mapped_issues.append(JiraIssue(
                id=issue.get("issue_id", ""),
                key=issue.get("issue_id", ""),
                summary=issue.get("title", ""),
                status=issue.get("status", ""),
                severity=issue.get("severity", ""),
                show_name=issue.get("show", ""),
                cost_impact=issue.get("cost_overrun", 0),
                delay_days=issue.get("delay_days", 0),
                created=issue.get("created", datetime.now().isoformat()),
                updated=issue.get("updated", datetime.now().isoformat()),
                assignee=issue.get("assignee", None),
                url=f"{settings.jira_api_url}/browse/{issue.get('issue_id', '')}"
            ))
        
        return mapped_issues
        
    except Exception as e:
        logger.error("jira_issues_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch JIRA issues: {str(e)}")


@router.get(
    "/issues/{issue_key}",
    response_model=JiraIssue,
    summary="Get Issue by Key",
    description="""
    Retrieve a specific JIRA issue by its key (e.g., PROD-123).
    
    **Path Parameter:**
    - `issue_key`: JIRA issue key (format: PROJECT-NUMBER)
    
    **Response:** Full issue details including all custom fields.
    """
)
async def get_issue(issue_key: str) -> JiraIssue:
    """Get a specific JIRA issue by key."""
    try:
        issue = jira.get_issue_by_id(issue_key)
        if not issue:
            raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
        
        # Map integration fields to API model
        return JiraIssue(
            id=issue.get("issue_id", ""),
            key=issue.get("issue_id", ""),
            summary=issue.get("title", ""),
            status=issue.get("status", ""),
            severity=issue.get("severity", ""),
            show_name=issue.get("show", ""),
            cost_impact=issue.get("cost_overrun", 0),
            delay_days=issue.get("delay_days", 0),
            created=issue.get("created", datetime.now().isoformat()),
            updated=issue.get("updated", datetime.now().isoformat()),
            assignee=issue.get("assignee", None),
            url=f"{settings.jira_api_url}/browse/{issue.get('issue_id', '')}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("jira_get_issue_failed", issue_key=issue_key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch issue: {str(e)}")


@router.post(
    "/issues",
    response_model=JiraIssue,
    status_code=201,
    summary="Create Production Issue",
    description="""
    Create a new production issue in JIRA.
    
    **Required Fields:**
    - `project_key`: Target JIRA project
    - `summary`: Brief description
    - `description`: Detailed explanation
    
    **Optional Fields:**
    - `issue_type`: Type of issue (default: Bug)
    - `severity`: Severity level
    - `show_name`: Related show/content
    - `cost_impact`: Estimated cost in USD
    - `delay_days`: Expected delay
    
    **Response:** Created issue with generated JIRA key and URL.
    """
)
async def create_issue(request: CreateIssueRequest = Body(...)) -> JiraIssue:
    """Create a new production issue in JIRA."""
    try:
        logger.info("jira_create_issue", project=request.project_key, summary=request.summary)
        
        issue = jira.create_issue(
            project_key=request.project_key,
            summary=request.summary,
            description=request.description,
            issue_type=request.issue_type,
            severity=request.severity,
            show_name=request.show_name,
            cost_impact=request.cost_impact,
            delay_days=request.delay_days
        )
        
        # Map integration fields to API model
        return JiraIssue(
            id=issue.get("issue_id", ""),
            key=issue.get("issue_id", ""),
            summary=issue.get("title", ""),
            status=issue.get("status", ""),
            severity=issue.get("severity", ""),
            show_name=issue.get("show", ""),
            cost_impact=issue.get("cost_overrun", 0),
            delay_days=issue.get("delay_days", 0),
            created=issue.get("created", datetime.now().isoformat()),
            updated=issue.get("updated", datetime.now().isoformat()),
            assignee=issue.get("assignee", None),
            url=f"{settings.jira_api_url}/browse/{issue.get('issue_id', '')}"
        )
        
    except Exception as e:
        logger.error("jira_create_issue_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create issue: {str(e)}")


@router.get(
    "/shows/{show_name}/issues",
    response_model=List[JiraIssue],
    summary="Get Issues by Show",
    description="""
    Retrieve all production issues for a specific show/content.
    
    **Use Case:** Track production problems for Yellowstone, 1923, etc.
    
    **Path Parameter:**
    - `show_name`: Name of the show (e.g., "Yellowstone")
    
    **Response:** List of issues related to the show, sorted by severity.
    """
)
async def get_issues_by_show(show_name: str) -> List[JiraIssue]:
    """Get all issues for a specific show."""
    try:
        issues = jira.get_issues_by_show(show_name)
        mapped_issues = []
        for issue in issues:
            mapped_issues.append(JiraIssue(
                id=issue.get("issue_id", ""),
                key=issue.get("issue_id", ""),
                summary=issue.get("title", ""),
                status=issue.get("status", ""),
                severity=issue.get("severity", ""),
                show_name=issue.get("show", ""),
                cost_impact=issue.get("cost_overrun", 0),
                delay_days=issue.get("delay_days", 0),
                created=issue.get("created", datetime.now().isoformat()),
                updated=issue.get("updated", datetime.now().isoformat()),
                assignee=issue.get("assignee", None),
                url=f"{settings.jira_api_url}/browse/{issue.get('issue_id', '')}"
            ))
        return mapped_issues
    except Exception as e:
        logger.error("jira_show_issues_failed", show_name=show_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch show issues: {str(e)}")


@router.get(
    "/issues/critical",
    response_model=List[JiraIssue],
    summary="Get Critical Issues",
    description="""
    Retrieve all critical severity issues requiring immediate attention.
    
    **Use Case:** Executive dashboard, incident response, escalation workflows.
    
    **Response:** List of critical issues sorted by cost impact (highest first).
    """
)
async def get_critical_issues() -> List[JiraIssue]:
    """Get all critical severity issues."""
    try:
        issues = jira.get_critical_issues()
        mapped_issues = []
        for issue in issues:
            mapped_issues.append(JiraIssue(
                id=issue.get("issue_id", ""),
                key=issue.get("issue_id", ""),
                summary=issue.get("title", ""),
                status=issue.get("status", ""),
                severity=issue.get("severity", ""),
                show_name=issue.get("show", ""),
                cost_impact=issue.get("cost_overrun", 0),
                delay_days=issue.get("delay_days", 0),
                created=issue.get("created", datetime.now().isoformat()),
                updated=issue.get("updated", datetime.now().isoformat()),
                assignee=issue.get("assignee", None),
                url=f"{settings.jira_api_url}/browse/{issue.get('issue_id', '')}"
            ))
        return mapped_issues
    except Exception as e:
        logger.error("jira_critical_issues_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch critical issues: {str(e)}")


@router.get(
    "/analytics/cost-summary",
    response_model=Dict[str, Any],
    summary="Get Cost Impact Summary",
    description="""
    Get aggregated cost impact analysis across all production issues.
    
    **Returns:**
    - Total cost impact
    - Breakdown by show
    - Breakdown by severity
    - Pareto analysis (80/20 shows causing most cost)
    
    **Use Case:** Executive reporting, budget tracking, risk assessment.
    """
)
async def get_cost_summary() -> Dict[str, Any]:
    """Get cost impact summary across all issues."""
    try:
        return jira.get_cost_summary()
    except Exception as e:
        logger.error("jira_cost_summary_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate cost summary: {str(e)}")


@router.get(
    "/analytics/stats",
    response_model=JiraStats,
    summary="Get JIRA Statistics",
    description="""
    Get comprehensive statistics and analytics for production issues.
    
    **Metrics:**
    - Total issue count
    - Distribution by status (Open, In Progress, Resolved, etc.)
    - Distribution by severity (Critical, High, Medium, Low)
    - Total cost impact across all issues
    - Average delay days
    - Critical issue count
    
    **Use Case:** Dashboard KPIs, trend analysis, capacity planning.
    """
)
async def get_jira_stats() -> JiraStats:
    """Get comprehensive JIRA statistics."""
    try:
        issues = jira.get_production_issues()
        
        # Calculate stats
        by_status: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        total_cost = 0.0
        total_delay = 0
        delay_count = 0
        critical_count = 0
        
        for issue in issues:
            # Status count
            status = issue.get("status", "Unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            # Severity count
            severity = issue.get("severity", "Unknown")
            by_severity[severity] = by_severity.get(severity, 0) + 1
            
            if severity == "Critical":
                critical_count += 1
            
            # Cost impact
            if issue.get("cost_impact"):
                total_cost += issue["cost_impact"]
            
            # Delay days
            if issue.get("delay_days"):
                total_delay += issue["delay_days"]
                delay_count += 1
        
        return JiraStats(
            total_issues=len(issues),
            by_status=by_status,
            by_severity=by_severity,
            total_cost_impact=total_cost,
            average_delay_days=total_delay / delay_count if delay_count > 0 else 0,
            critical_count=critical_count
        )
        
    except Exception as e:
        logger.error("jira_stats_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to calculate stats: {str(e)}")


@router.get(
    "/health",
    summary="JIRA Health Check",
    description="Check JIRA API connectivity and configuration status."
)
async def jira_health_check():
    """Check JIRA integration health."""
    return {
        "status": "healthy" if settings.jira_enabled else "disabled",
        "mock_mode": settings.mock_mode,
        "jira_force_live": settings.jira_force_live,
        "cloud_url": settings.jira_cloud_url if settings.jira_enabled else None,
        "timestamp": datetime.now().isoformat()
    }

