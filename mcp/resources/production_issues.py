"""
Production Issues Resource.

Provides JIRA-style tasks, delays, and cost overruns.
"""

from typing import Dict, Any, List, Optional
from mcp.integrations import JiraConnector
from mcp.pareto import ParetoCalculator, ParetoInsights


class ProductionIssuesResource:
    """Resource for production issues and delays."""
    
    def __init__(self):
        """Initialize production issues resource."""
        self.jira = JiraConnector()
        self.pareto = ParetoCalculator()
        self.insights = ParetoInsights()
    
    def query(
        self,
        status: Optional[List[str]] = None,
        severity: Optional[str] = None,
        limit: int = 100,
        include_pareto: bool = True
    ) -> Dict[str, Any]:
        """
        Query production issues and delays.
        
        Args:
            status: Filter by status (e.g., ["open", "in_progress"])
            severity: Filter by severity ("critical", "high", "medium", "low")
            limit: Maximum number of issues to return (default: 100)
            include_pareto: Include Pareto analysis (default: True)
        
        Returns:
            Dictionary with issues and analysis
        """
        # Get production issues
        issues = self.jira.get_production_issues(
            status=status,
            severity=severity,
            limit=limit
        )
        
        # Get cost summary
        cost_summary = self.jira.get_cost_summary()
        
        result = {
            "issues": issues,
            "cost_summary": cost_summary,
            "query_params": {
                "status": status,
                "severity": severity,
                "limit": limit
            }
        }
        
        # Add Pareto analysis if requested
        if include_pareto and issues:
            # Analyze by delay days
            pareto_delays = self.pareto.analyze(
                issues,
                impact_field="delay_days",
                id_field="issue_id"
            )
            
            # Analyze by cost overrun
            pareto_costs = self.pareto.analyze(
                issues,
                impact_field="cost_overrun",
                id_field="issue_id"
            )
            
            result["pareto_analysis"] = {
                "by_delay_days": pareto_delays.to_dict(),
                "by_cost_overrun": pareto_costs.to_dict()
            }
            
            # Generate insights for delays
            insights_delays = self.insights.generate_insights(
                pareto_delays,
                context="production delays",
                impact_metric="delay_days",
                item_type="production issues"
            )
            
            result["pareto_insights"] = {
                "delay_insights": insights_delays
            }
            
            # Get top contributors
            result["top_delay_contributors"] = self.pareto.get_top_contributors(
                pareto_delays,
                id_field="issue_id",
                impact_field="delay_days"
            )
        
        return result
    
    def get_issue_details(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific issue.
        
        Args:
            issue_id: Issue identifier (e.g., "PROD-0001")
        
        Returns:
            Issue details or None if not found
        """
        return self.jira.get_issue_by_id(issue_id)
    
    def get_issues_by_show(self, show_name: str) -> Dict[str, Any]:
        """
        Get all issues for a specific show with analysis.
        
        Args:
            show_name: Name of the show
        
        Returns:
            Issues for the show with summary
        """
        issues = self.jira.get_issues_by_show(show_name)
        
        if not issues:
            return {
                "show": show_name,
                "issues": [],
                "summary": {"message": "No issues found for this show"}
            }
        
        total_delay = sum(i["delay_days"] for i in issues)
        total_cost = sum(i["cost_overrun"] for i in issues)
        
        return {
            "show": show_name,
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "total_delay_days": total_delay,
                "total_cost_overrun": total_cost,
                "critical_issues": [i for i in issues if i["severity"] == "critical"]
            }
        }
    
    def get_critical_path_analysis(self) -> Dict[str, Any]:
        """
        Identify critical path issues blocking multiple productions.
        
        Returns:
            Critical path analysis
        """
        issues = self.jira.get_production_issues(limit=1000)
        
        # Focus on high severity, high delay issues
        critical_path = [
            i for i in issues
            if i["severity"] in ["critical", "high"] and i["delay_days"] >= 10
        ]
        
        # Sort by delay days
        critical_path_sorted = sorted(
            critical_path,
            key=lambda x: x["delay_days"],
            reverse=True
        )
        
        total_delay = sum(i["delay_days"] for i in critical_path)
        
        return {
            "critical_path_issues": critical_path_sorted,
            "total_critical_delay_days": total_delay,
            "shows_impacted": len(set(i["show"] for i in critical_path)),
            "recommendation": (
                f"Immediate escalation required: {len(critical_path)} critical issues "
                f"causing {total_delay} days of delays"
            )
        }


def create_resource() -> ProductionIssuesResource:
    """Factory function to create production issues resource."""
    return ProductionIssuesResource()
