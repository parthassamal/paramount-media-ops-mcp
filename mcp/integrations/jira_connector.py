"""
JIRA connector for production issues and costs.

Provides interface to JIRA API with mock mode support.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings
from mcp.mocks.generate_production_issues import ProductionIssueGenerator


class JiraConnector:
    """
    Connector for JIRA API to fetch production issues and costs.
    
    In mock mode, returns generated data. In production, connects to real JIRA API.
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize JIRA connector.
        
        Args:
            mock_mode: If True, use mock data. If None, use settings default.
        """
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
        self.api_url = settings.jira_api_url
        self.api_token = settings.jira_api_token
        self.project_key = settings.jira_project_key
        
        if self.mock_mode:
            self.generator = ProductionIssueGenerator()
    
    def get_production_issues(
        self,
        project: Optional[str] = None,
        status: Optional[List[str]] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch production issues from JIRA.
        
        Args:
            project: Project key (default: from settings)
            status: Filter by status (e.g., ["open", "in_progress"])
            severity: Filter by severity (e.g., "critical", "high")
            limit: Maximum number of issues to return
        
        Returns:
            List of production issue dictionaries
        """
        if self.mock_mode:
            return self._get_mock_issues(status, severity, limit)
        else:
            return self._fetch_from_jira(project, status, severity, limit)
    
    def _get_mock_issues(
        self,
        status: Optional[List[str]],
        severity: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get mock production issues."""
        issues = self.generator.generate(num_issues=20)
        
        # Apply filters
        if status:
            issues = [i for i in issues if i["status"] in status]
        
        if severity:
            issues = [i for i in issues if i["severity"] == severity]
        
        return issues[:limit]
    
    def _fetch_from_jira(
        self,
        project: Optional[str],
        status: Optional[List[str]],
        severity: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch from real JIRA API."""
        # TODO: Implement real JIRA API integration
        # This would use requests library to call JIRA REST API
        raise NotImplementedError("Real JIRA integration not yet implemented. Use mock_mode=True.")
    
    def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific issue by ID.
        
        Args:
            issue_id: JIRA issue ID (e.g., "PROD-0001")
        
        Returns:
            Issue dictionary or None if not found
        """
        issues = self.get_production_issues()
        for issue in issues:
            if issue["issue_id"] == issue_id:
                return issue
        return None
    
    def get_issues_by_show(self, show_name: str) -> List[Dict[str, Any]]:
        """
        Get all issues for a specific show.
        
        Args:
            show_name: Name of the show
        
        Returns:
            List of issues for that show
        """
        issues = self.get_production_issues()
        return [i for i in issues if i["show"] == show_name]
    
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
        
        return {
            "total_issues": len(issues),
            "total_cost_overrun": total_cost_overrun,
            "total_delay_days": total_delay_days,
            "total_revenue_at_risk": total_revenue_at_risk,
            "by_severity": by_severity,
            "critical_issues": [i for i in issues if i["severity"] == "critical"]
        }
