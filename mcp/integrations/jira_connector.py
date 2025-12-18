"""
JIRA connector for production issues and costs.

Provides interface to JIRA API with real API support and mock mode fallback.
Implements Pareto analysis for identifying critical issues.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import base64
import structlog
import httpx

from config import settings
from mcp.mocks.generate_production_issues import ProductionIssueGenerator
from mcp.pareto import ParetoCalculator

logger = structlog.get_logger()


class JiraConnector:
    """
    Connector for JIRA API to fetch production issues and costs.
    
    In mock mode, returns generated data. In production, connects to real JIRA API.
    
    Supports:
    - Fetching production issues with filters
    - Cost impact analysis
    - Delay tracking
    - Pareto analysis for prioritization
    - Issue creation and updates
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize JIRA connector.
        
        Args:
            mock_mode: If True, use mock data. If None, use settings default.
        """
        # Support "hybrid demo" mode: keep analytics mocked, but run Jira live
        forced_live = bool(getattr(settings, "jira_force_live", False))
        self.mock_mode = False if forced_live else (mock_mode if mock_mode is not None else settings.mock_mode)
        self.api_url = settings.jira_api_url.rstrip('/')
        self.api_email = settings.jira_api_email
        self.api_token = settings.jira_api_token
        self.project_key = settings.jira_project_key
        self.content_project_key = settings.jira_content_project_key
        self.timeout = settings.jira_request_timeout
        
        # Custom field mappings
        self.cf_cost_impact = settings.jira_custom_field_cost_impact
        self.cf_delay_days = settings.jira_custom_field_delay_days
        self.cf_show_name = settings.jira_custom_field_show_name
        
        # Initialize Pareto calculator
        self.pareto = ParetoCalculator()
        
        if self.mock_mode:
            self.generator = ProductionIssueGenerator()
            logger.info("jira_connector_initialized", mode="mock")
        else:
            self._validate_credentials()
            logger.info("jira_connector_initialized", mode="live", url=self.api_url)

    def _sync_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make a synchronous request to Jira.

        We intentionally use sync HTTP here to keep the public API synchronous and
        avoid event-loop issues when called inside FastAPI request handlers.
        """
        url = f"{self.api_url}{endpoint}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method=method,
                url=url,
                headers=self._get_auth_header(),
                params=params,
                json=data,
            )
            response.raise_for_status()
            return response.json()
    
    def _validate_credentials(self):
        """Validate JIRA credentials are configured."""
        if not self.api_email or not self.api_token:
            logger.warning(
                "jira_credentials_missing",
                message="JIRA API credentials not configured. Set JIRA_API_EMAIL and JIRA_API_TOKEN."
            )
    
    def _get_auth_header(self) -> Dict[str, str]:
        """Generate Basic Auth header for JIRA API."""
        credentials = f"{self.api_email}:{self.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to JIRA API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/rest/api/3/search")
            params: Query parameters
            data: Request body for POST/PUT
        
        Returns:
            JSON response as dictionary
        """
        url = f"{self.api_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_auth_header(),
                    params=params,
                    json=data
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.HTTPStatusError as e:
                logger.error(
                    "jira_api_error",
                    status_code=e.response.status_code,
                    url=url,
                    error=str(e)
                )
                raise
            except httpx.RequestError as e:
                logger.error(
                    "jira_request_error",
                    url=url,
                    error=str(e)
                )
                raise
    
    def _build_jql(
        self,
        project: Optional[str] = None,
        status: Optional[List[str]] = None,
        severity: Optional[str] = None,
        show_name: Optional[str] = None,
        days_since_created: Optional[int] = None
    ) -> str:
        """
        Build JQL query string.
        
        Args:
            project: Project key
            status: List of statuses to filter
            severity: Priority/severity level
            show_name: Show name for content issues
            days_since_created: Filter issues created in last N days
        
        Returns:
            JQL query string
        """
        conditions = []
        
        if project:
            conditions.append(f'project = "{project}"')
        
        if status:
            status_list = ', '.join(f'"{s}"' for s in status)
            conditions.append(f'status IN ({status_list})')
        
        if severity:
            # Map severity to JIRA priority
            priority_map = {
                "critical": "Highest",
                "high": "High",
                "medium": "Medium",
                "low": "Low"
            }
            jira_priority = priority_map.get(severity.lower(), severity)
            conditions.append(f'priority = "{jira_priority}"')
        
        if show_name and self.cf_show_name:
            conditions.append(f'"{self.cf_show_name}" ~ "{show_name}"')
        
        if days_since_created:
            conditions.append(f'created >= -{days_since_created}d')
        
        return ' AND '.join(conditions) if conditions else ''
    
    def _parse_issue(self, jira_issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse JIRA issue into standardized format.
        
        Args:
            jira_issue: Raw JIRA issue from API
        
        Returns:
            Standardized issue dictionary
        """
        fields = jira_issue.get("fields", {})
        
        # Extract custom fields
        cost_overrun = 0
        delay_days = 0
        show_name = ""
        
        if self.cf_cost_impact and self.cf_cost_impact in fields:
            cost_overrun = fields.get(self.cf_cost_impact) or 0
        
        if self.cf_delay_days and self.cf_delay_days in fields:
            delay_days = fields.get(self.cf_delay_days) or 0
        
        if self.cf_show_name and self.cf_show_name in fields:
            show_name = fields.get(self.cf_show_name) or ""
        
        # Map JIRA priority to severity
        priority = fields.get("priority", {}).get("name", "Medium")
        severity_map = {
            "Highest": "critical",
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Lowest": "low"
        }
        severity = severity_map.get(priority, "medium")
        
        # Calculate days open
        created = fields.get("created", "")
        days_open = 0
        if created:
            try:
                created_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                days_open = (datetime.now(created_date.tzinfo) - created_date).days
            except (ValueError, TypeError):
                pass
        
        # Estimate revenue at risk (simplified model)
        revenue_at_risk = int(cost_overrun * 1.5 + delay_days * 50000)
        
        return {
            "issue_id": jira_issue.get("key", ""),
            "title": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "status": fields.get("status", {}).get("name", "Open"),
            "severity": severity,
            "priority": priority,
            "show": show_name,
            "cost_overrun": cost_overrun,
            "delay_days": delay_days,
            "revenue_at_risk": revenue_at_risk,
            "days_open": days_open,
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned") if fields.get("assignee") else "Unassigned",
            "reporter": fields.get("reporter", {}).get("displayName", "Unknown") if fields.get("reporter") else "Unknown",
            "created": created,
            "updated": fields.get("updated", ""),
            "labels": fields.get("labels", []),
            "components": [c.get("name", "") for c in fields.get("components", [])],
            "jira_url": f"{self.api_url}/browse/{jira_issue.get('key', '')}"
        }
    
    def get_production_issues(
        self,
        project: Optional[str] = None,
        status: Optional[List[str]] = None,
        severity: Optional[str] = None,
        show_name: Optional[str] = None,
        days_since_created: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch production issues from JIRA.
        
        Args:
            project: Project key (default: from settings)
            status: Filter by status (e.g., ["Open", "In Progress"])
            severity: Filter by severity (e.g., "critical", "high")
            show_name: Filter by show name
            days_since_created: Filter issues created in last N days
            limit: Maximum number of issues to return
        
        Returns:
            List of production issue dictionaries
        """
        if self.mock_mode:
            return self._get_mock_issues(status, severity, show_name, days_since_created, limit)
        
        return self._fetch_from_jira_sync(
            project or self.project_key,
            status,
            severity,
            show_name,
            days_since_created,
            limit
        )
    
    def _get_mock_issues(
        self,
        status: Optional[List[str]],
        severity: Optional[str],
        show_name: Optional[str],
        days_since_created: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get mock production issues."""
        issues = self.generator.generate(num_issues=20)
        
        # Apply filters
        if status:
            # Normalize status names for comparison
            status_lower = [s.lower().replace("_", " ") for s in status]
            issues = [
                i for i in issues 
                if i["status"].lower().replace("_", " ") in status_lower
            ]
        
        if severity:
            issues = [i for i in issues if i["severity"] == severity]
        
        # Filter by show name
        if show_name:
            issues = [
                i for i in issues 
                if show_name.lower() in i.get("show", "").lower()
            ]
        
        # Filter by days since created
        if days_since_created:
            cutoff_date = datetime.now() - timedelta(days=days_since_created)
            issues = [
                i for i in issues 
                if datetime.fromisoformat(i.get("created", datetime.now().isoformat())) >= cutoff_date
            ]
        
        return issues[:limit]
    
    def _fetch_from_jira_sync(
        self,
        project: str,
        status: Optional[List[str]],
        severity: Optional[str],
        show_name: Optional[str],
        days_since_created: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch from real JIRA API (synchronous)."""
        jql = self._build_jql(
            project=project,
            status=status,
            severity=severity,
            show_name=show_name,
            days_since_created=days_since_created,
        )

        logger.info("jira_search", jql=jql, limit=limit)

        try:
            # Jira Cloud deprecated /rest/api/3/search in some tenants;
            # use /rest/api/3/search/jql (POST).
            response = self._sync_request(
                method="POST",
                endpoint="/rest/api/3/search/jql",
                data={
                    "jql": jql,
                    "maxResults": limit,
                    "fields": [
                        "summary",
                        "description",
                        "status",
                        "priority",
                        "assignee",
                        "reporter",
                        "created",
                        "updated",
                        "labels",
                        "components",
                        self.cf_cost_impact,
                        self.cf_delay_days,
                        self.cf_show_name,
                    ],
                },
            )

            issues = [self._parse_issue(issue) for issue in response.get("issues", [])]
            logger.info("jira_search_complete", count=len(issues))
            return issues
        except Exception as e:
            logger.error("jira_fetch_failed", error=str(e))
            if settings.is_development:
                logger.warning("falling_back_to_mock_data")
                return self._get_mock_issues(status, severity, show_name, days_since_created, limit)
            raise
    
    async def _fetch_from_jira_async(
        self,
        project: str,
        status: Optional[List[str]],
        severity: Optional[str],
        show_name: Optional[str],
        days_since_created: Optional[int],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch from real JIRA API."""
        jql = self._build_jql(
            project=project,
            status=status,
            severity=severity,
            show_name=show_name,
            days_since_created=days_since_created
        )
        
        logger.info("jira_search", jql=jql, limit=limit)
        
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/rest/api/3/search",
                params={
                    "jql": jql,
                    "maxResults": limit,
                    "fields": ",".join([
                        "summary", "description", "status", "priority",
                        "assignee", "reporter", "created", "updated",
                        "labels", "components",
                        self.cf_cost_impact, self.cf_delay_days, self.cf_show_name
                    ])
                }
            )
            
            issues = [
                self._parse_issue(issue) 
                for issue in response.get("issues", [])
            ]
            
            logger.info("jira_search_complete", count=len(issues))
            return issues
            
        except Exception as e:
            logger.error("jira_fetch_failed", error=str(e))
            # Fall back to mock data on error
            if settings.is_development:
                logger.warning("falling_back_to_mock_data")
                return self._get_mock_issues(status, severity, limit)
            raise
    
    def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific issue by ID.
        
        Args:
            issue_id: JIRA issue ID (e.g., "PROD-0001")
        
        Returns:
            Issue dictionary or None if not found
        """
        if self.mock_mode:
            issues = self.get_production_issues()
            for issue in issues:
                if issue["issue_id"] == issue_id:
                    return issue
            return None
        
        try:
            response = self._sync_request(method="GET", endpoint=f"/rest/api/3/issue/{issue_id}")
            return self._parse_issue(response)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    async def _get_issue_by_id_async(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Fetch single issue from JIRA."""
        try:
            response = await self._make_request(
                method="GET",
                endpoint=f"/rest/api/3/issue/{issue_id}"
            )
            return self._parse_issue(response)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    def get_issues_by_show(self, show_name: str) -> List[Dict[str, Any]]:
        """
        Get all issues for a specific show.
        
        Args:
            show_name: Name of the show
        
        Returns:
            List of issues for that show
        """
        if self.mock_mode:
            issues = self.get_production_issues()
            return [i for i in issues if show_name.lower() in i.get("show", "").lower()]
        
        return self.get_production_issues(
            project=self.content_project_key,
            show_name=show_name
        )
    
    def get_critical_issues(self) -> Dict[str, Any]:
        """
        Get critical issues with Pareto analysis.
        
        Returns:
            Dictionary with critical issues and Pareto insights
        """
        issues = self.get_production_issues()
        
        # Filter critical/high severity
        critical_issues = [
            i for i in issues 
            if i["severity"] in ["critical", "high"]
        ]
        
        # Perform Pareto analysis on cost impact
        if len(critical_issues) >= 2:
            try:
                pareto_result = self.pareto.analyze(
                    critical_issues,
                    impact_field="cost_overrun",
                    id_field="issue_id"
                )
                pareto_data = pareto_result.to_dict()
            except ValueError:
                pareto_data = None
        else:
            pareto_data = None
        
        return {
            "total_critical": len(critical_issues),
            "issues": critical_issues,
            "pareto_analysis": pareto_data,
            "total_cost_at_risk": sum(i["cost_overrun"] for i in critical_issues),
            "total_delay_days": sum(i["delay_days"] for i in critical_issues)
        }
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get summary of production costs and overruns.
        
        Returns:
            Cost summary dictionary
        """
        issues = self.get_production_issues()
        
        total_cost_overrun = sum(i["cost_overrun"] for i in issues)
        total_delay_days = sum(i["delay_days"] for i in issues)
        total_revenue_at_risk = sum(i["revenue_at_risk"] for i in issues)
        
        # Group by severity
        by_severity = {}
        for issue in issues:
            severity = issue["severity"]
            if severity not in by_severity:
                by_severity[severity] = {
                    "count": 0,
                    "total_cost": 0,
                    "total_delay": 0
                }
            by_severity[severity]["count"] += 1
            by_severity[severity]["total_cost"] += issue["cost_overrun"]
            by_severity[severity]["total_delay"] += issue["delay_days"]
        
        # Group by show
        by_show = {}
        for issue in issues:
            show = issue.get("show", "Unknown")
            if show not in by_show:
                by_show[show] = {
                    "count": 0,
                    "total_cost": 0,
                    "total_delay": 0
                }
            by_show[show]["count"] += 1
            by_show[show]["total_cost"] += issue["cost_overrun"]
            by_show[show]["total_delay"] += issue["delay_days"]
        
        return {
            "total_issues": len(issues),
            "total_cost_overrun": total_cost_overrun,
            "total_delay_days": total_delay_days,
            "total_revenue_at_risk": total_revenue_at_risk,
            "by_severity": by_severity,
            "by_show": by_show,
            "critical_issues": [i for i in issues if i["severity"] == "critical"]
        }
    
    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Bug",
        priority: str = "High",
        show_name: Optional[str] = None,
        cost_impact: Optional[int] = None,
        delay_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new JIRA issue.
        
        Args:
            summary: Issue title
            description: Issue description
            issue_type: Type of issue (Bug, Task, Story, etc.)
            priority: Priority level
            show_name: Associated show name
            cost_impact: Estimated cost impact in USD
            delay_days: Estimated delay in days
        
        Returns:
            Created issue details
        """
        if self.mock_mode:
            return {
                "issue_id": f"PROD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "summary": summary,
                "status": "Open",
                "created": datetime.now().isoformat()
            }

        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }

        if show_name and self.cf_show_name:
            fields[self.cf_show_name] = show_name
        if cost_impact and self.cf_cost_impact:
            fields[self.cf_cost_impact] = cost_impact
        if delay_days and self.cf_delay_days:
            fields[self.cf_delay_days] = delay_days

        response = self._sync_request(method="POST", endpoint="/rest/api/3/issue", data={"fields": fields})

        return {
            "issue_id": response.get("key"),
            "issue_url": f"{self.api_url}/browse/{response.get('key')}",
            "created": True,
        }
    
    async def _create_issue_async(
        self,
        summary: str,
        description: str,
        issue_type: str,
        priority: str,
        show_name: Optional[str],
        cost_impact: Optional[int],
        delay_days: Optional[int]
    ) -> Dict[str, Any]:
        """Async implementation of create_issue."""
        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": priority}
        }
        
        # Add custom fields
        if show_name and self.cf_show_name:
            fields[self.cf_show_name] = show_name
        if cost_impact and self.cf_cost_impact:
            fields[self.cf_cost_impact] = cost_impact
        if delay_days and self.cf_delay_days:
            fields[self.cf_delay_days] = delay_days
        
        response = await self._make_request(
            method="POST",
            endpoint="/rest/api/3/issue",
            data={"fields": fields}
        )
        
        return {
            "issue_id": response.get("key"),
            "issue_url": f"{self.api_url}/browse/{response.get('key')}",
            "created": True
        }
