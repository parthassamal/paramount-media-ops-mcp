"""
Analyze Production Risk Tool.

Identifies 20% of issues causing 76% of delays using Pareto analysis.
"""

from typing import Dict, Any, List, Optional
from mcp.resources import ProductionIssuesResource
from mcp.pareto import ParetoCalculator, ParetoInsights


class AnalyzeProductionRiskTool:
    """
    Tool to analyze production risks using Pareto principle.
    
    Identifies critical issues that drive majority of delays and costs.
    """
    
    def __init__(self):
        """Initialize the tool."""
        self.production_resource = ProductionIssuesResource()
        self.pareto = ParetoCalculator()
        self.insights = ParetoInsights()
    
    def execute(
        self,
        severity_filter: Optional[str] = None,
        include_mitigation: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze production risks and identify critical issues.
        
        Args:
            severity_filter: Filter by severity ("critical", "high", "medium", "low")
            include_mitigation: Include mitigation recommendations (default: True)
        
        Returns:
            Risk analysis with Pareto breakdown and mitigation plans
            
        Example:
            >>> tool = AnalyzeProductionRiskTool()
            >>> result = tool.execute(severity_filter="critical")
            >>> print(result["critical_path_issues"][0]["title"])
            "VFX Pipeline Blocker - Star Trek: Discovery S5"
        """
        # Get production issues
        status_filter = ["open", "in_progress", "blocked"]
        production_data = self.production_resource.query(
            status=status_filter,
            severity=severity_filter
        )
        issues = production_data["issues"]
        
        # Get critical path analysis
        critical_path = self.production_resource.get_critical_path_analysis()
        
        # Perform Pareto analysis on delays
        pareto_delays = self.pareto.analyze(
            issues,
            impact_field="delay_days",
            id_field="issue_id"
        )
        
        # Perform Pareto analysis on costs
        pareto_costs = self.pareto.analyze(
            issues,
            impact_field="cost_overrun",
            id_field="issue_id"
        )
        
        # Get top contributors
        top_delay_drivers = self.pareto.get_top_contributors(
            pareto_delays,
            id_field="issue_id",
            impact_field="delay_days"
        )
        
        # Generate insights
        delay_insights = self.insights.generate_insights(
            pareto_delays,
            context="production delays",
            impact_metric="delay_days",
            item_type="production issues"
        )
        
        # Calculate risk scores
        risk_assessment = self._assess_risks(issues, top_delay_drivers)
        
        result = {
            "analysis_scope": {
                "total_issues": len(issues),
                "severity_filter": severity_filter or "all",
                "total_delay_days": sum(i["delay_days"] for i in issues),
                "total_cost_overrun": sum(i["cost_overrun"] for i in issues)
            },
            "pareto_analysis": {
                "by_delay": pareto_delays.to_dict(),
                "by_cost": pareto_costs.to_dict()
            },
            "top_delay_drivers": top_delay_drivers[:5],
            "critical_path_issues": critical_path["critical_path_issues"][:5],
            "risk_assessment": risk_assessment,
            "insights": delay_insights
        }
        
        if include_mitigation:
            result["mitigation_plans"] = self._generate_mitigation_plans(top_delay_drivers)
        
        return result
    
    def _assess_risks(
        self,
        issues: List[Dict[str, Any]],
        top_drivers: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess overall production risk."""
        # Calculate risk by category
        risk_by_type = {}
        for issue in issues:
            issue_type = issue["type"]
            if issue_type not in risk_by_type:
                risk_by_type[issue_type] = {
                    "count": 0,
                    "total_delay": 0,
                    "total_cost": 0
                }
            risk_by_type[issue_type]["count"] += 1
            risk_by_type[issue_type]["total_delay"] += issue["delay_days"]
            risk_by_type[issue_type]["total_cost"] += issue["cost_overrun"]
        
        # Calculate risk by show
        risk_by_show = {}
        for issue in issues:
            show = issue["show"]
            if show not in risk_by_show:
                risk_by_show[show] = {
                    "issue_count": 0,
                    "total_delay": 0,
                    "total_cost": 0
                }
            risk_by_show[show]["issue_count"] += 1
            risk_by_show[show]["total_delay"] += issue["delay_days"]
            risk_by_show[show]["total_cost"] += issue["cost_overrun"]
        
        # Identify highest risk shows
        highest_risk_shows = sorted(
            risk_by_show.items(),
            key=lambda x: x[1]["total_delay"],
            reverse=True
        )[:5]
        
        # Calculate concentration risk
        top_3_delay_pct = sum(d.get("contribution_percent", 0) for d in top_drivers[:3])
        
        return {
            "risk_by_type": risk_by_type,
            "highest_risk_shows": [
                {"show": show, **metrics} for show, metrics in highest_risk_shows
            ],
            "concentration_risk": {
                "top_3_issues_drive_pct": round(top_3_delay_pct, 1),
                "risk_level": "high" if top_3_delay_pct > 70 else "moderate"
            },
            "overall_risk_score": self._calculate_overall_risk(issues)
        }
    
    def _calculate_overall_risk(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall production risk score."""
        critical_count = len([i for i in issues if i["severity"] == "critical"])
        high_count = len([i for i in issues if i["severity"] == "high"])
        
        # Risk score based on severity distribution
        risk_score = (critical_count * 10 + high_count * 5) / len(issues) if issues else 0
        risk_score = min(risk_score, 10)  # Cap at 10
        
        risk_level = "critical" if risk_score >= 7 else "high" if risk_score >= 5 else "moderate"
        
        return {
            "score": round(risk_score, 1),
            "level": risk_level,
            "critical_issues": critical_count,
            "high_priority_issues": high_count
        }
    
    def _generate_mitigation_plans(
        self,
        top_drivers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate mitigation plans for top risk drivers."""
        mitigation_plans = []
        
        for i, driver in enumerate(top_drivers[:3], 1):
            # Extract issue details
            issue_id = driver.get("issue_id") or driver.get("id")
            issue_details = self.production_resource.get_issue_details(issue_id)
            
            if not issue_details:
                continue
            
            plan = {
                "priority": i,
                "issue_id": issue_id,
                "issue_title": issue_details["title"],
                "show": issue_details["show"],
                "current_delay": driver.get("delay_days"),
                "financial_impact": driver.get("cost_overrun"),
                "mitigation_steps": issue_details.get("mitigation_plan", []),
                "resource_requirements": self._estimate_resources(issue_details),
                "timeline": self._estimate_mitigation_timeline(issue_details),
                "expected_delay_reduction": int(driver.get("delay_days", 0) * 0.6)  # 60% reduction
            }
            
            mitigation_plans.append(plan)
        
        return mitigation_plans
    
    def _estimate_resources(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate resources needed for mitigation."""
        severity = issue["severity"]
        
        resource_map = {
            "critical": {
                "team_size": "8-12 people",
                "budget": "$500K-$1M",
                "executive_oversight": "Required"
            },
            "high": {
                "team_size": "4-6 people",
                "budget": "$200K-$500K",
                "executive_oversight": "Recommended"
            },
            "medium": {
                "team_size": "2-4 people",
                "budget": "$50K-$200K",
                "executive_oversight": "Optional"
            }
        }
        
        return resource_map.get(severity, resource_map["medium"])
    
    def _estimate_mitigation_timeline(self, issue: Dict[str, Any]) -> str:
        """Estimate timeline for mitigation."""
        severity = issue["severity"]
        delay = issue["delay_days"]
        
        if severity == "critical":
            return "2-4 weeks (emergency sprint)"
        elif delay >= 30:
            return "6-12 weeks"
        elif delay >= 10:
            return "4-8 weeks"
        else:
            return "2-4 weeks"


def create_tool() -> AnalyzeProductionRiskTool:
    """Factory function to create the tool."""
    return AnalyzeProductionRiskTool()
