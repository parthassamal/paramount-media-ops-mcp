"""
Operational Efficiency Resource.

Provides production metrics and resource utilization.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
from config import settings
from mcp.integrations import JiraConnector


class OperationalEfficiencyResource:
    """Resource for operational efficiency metrics."""
    
    def __init__(self):
        """Initialize operational efficiency resource."""
        self.jira = JiraConnector()
        random.seed(settings.random_seed)
    
    def query(
        self,
        metric_type: Optional[str] = None,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Query operational efficiency metrics.
        
        Args:
            metric_type: Type of metrics ("production", "resource", "quality", "all")
            timeframe_days: Timeframe for analysis (default: 30)
        
        Returns:
            Dictionary with efficiency metrics
        """
        # Get production metrics
        production_metrics = self._calculate_production_metrics()
        
        # Get resource utilization
        resource_metrics = self._calculate_resource_utilization()
        
        # Get quality metrics
        quality_metrics = self._calculate_quality_metrics()
        
        # Calculate overall efficiency score
        efficiency_score = self._calculate_efficiency_score(
            production_metrics,
            resource_metrics,
            quality_metrics
        )
        
        result = {
            "efficiency_score": efficiency_score,
            "query_params": {
                "metric_type": metric_type,
                "timeframe_days": timeframe_days
            }
        }
        
        # Add requested metrics
        if not metric_type or metric_type == "all":
            result["production_metrics"] = production_metrics
            result["resource_metrics"] = resource_metrics
            result["quality_metrics"] = quality_metrics
        elif metric_type == "production":
            result["production_metrics"] = production_metrics
        elif metric_type == "resource":
            result["resource_metrics"] = resource_metrics
        elif metric_type == "quality":
            result["quality_metrics"] = quality_metrics
        
        # Add recommendations
        result["recommendations"] = self._generate_recommendations(
            production_metrics,
            resource_metrics,
            quality_metrics
        )
        
        return result
    
    def _calculate_production_metrics(self) -> Dict[str, Any]:
        """Calculate production efficiency metrics."""
        issues = self.jira.get_production_issues(limit=1000)
        
        # Calculate metrics
        total_issues = len(issues)
        on_time_issues = len([i for i in issues if i["delay_days"] == 0])
        delayed_issues = len([i for i in issues if i["delay_days"] > 0])
        
        avg_delay = sum(i["delay_days"] for i in issues) / len(issues) if issues else 0
        
        # Calculate velocity (issues per show)
        shows_impacted = len(set(i["show"] for i in issues))
        velocity = total_issues / shows_impacted if shows_impacted > 0 else 0
        
        return {
            "total_production_issues": total_issues,
            "on_time_completion_rate": round(on_time_issues / total_issues, 2) if total_issues > 0 else 0,
            "delayed_issues": delayed_issues,
            "avg_delay_days": round(avg_delay, 1),
            "shows_in_production": shows_impacted,
            "issue_velocity": round(velocity, 2),
            "critical_issues_pct": round(
                len([i for i in issues if i["severity"] == "critical"]) / total_issues * 100, 1
            ) if total_issues > 0 else 0
        }
    
    def _calculate_resource_utilization(self) -> Dict[str, Any]:
        """Calculate resource utilization metrics."""
        issues = self.jira.get_production_issues(limit=1000)
        
        # Analyze team assignments
        team_workload = {}
        for issue in issues:
            team = issue["assigned_team"]
            if team not in team_workload:
                team_workload[team] = {
                    "issue_count": 0,
                    "total_delay": 0,
                    "total_cost": 0
                }
            team_workload[team]["issue_count"] += 1
            team_workload[team]["total_delay"] += issue["delay_days"]
            team_workload[team]["total_cost"] += issue["cost_overrun"]
        
        # Calculate utilization metrics
        total_budget_used = sum(i["cost_overrun"] for i in issues)
        estimated_total_budget = 50000000  # $50M production budget
        
        return {
            "team_workload": team_workload,
            "total_teams_engaged": len(team_workload),
            "budget_utilization": round(total_budget_used / estimated_total_budget, 2),
            "total_budget_used": total_budget_used,
            "estimated_total_budget": estimated_total_budget,
            "overloaded_teams": [
                team for team, data in team_workload.items()
                if data["issue_count"] > 5  # Threshold for overload
            ]
        }
    
    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate quality metrics."""
        issues = self.jira.get_production_issues(limit=1000)
        
        # Quality indicators
        rework_issues = [i for i in issues if "rewrites" in i["root_cause"].lower() or "redesign" in i["root_cause"].lower()]
        vendor_issues = [i for i in issues if "vendor" in i["root_cause"].lower() or "third-party" in i["root_cause"].lower()]
        
        # Calculate quality score (inverse of issues)
        quality_score = 100 - (len(rework_issues) / len(issues) * 100) if issues else 100
        
        return {
            "quality_score": round(quality_score, 1),
            "rework_rate": round(len(rework_issues) / len(issues), 2) if issues else 0,
            "vendor_issue_rate": round(len(vendor_issues) / len(issues), 2) if issues else 0,
            "total_rework_cost": sum(i["cost_overrun"] for i in rework_issues),
            "quality_improvement_potential": round((len(rework_issues) / len(issues)) * 100, 1) if issues else 0
        }
    
    def _calculate_efficiency_score(
        self,
        production: Dict[str, Any],
        resource: Dict[str, Any],
        quality: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall efficiency score."""
        # Weighted average of component scores
        production_score = production["on_time_completion_rate"] * 100
        resource_score = (1 - resource["budget_utilization"]) * 100  # Lower utilization of overruns is better
        quality_score = quality["quality_score"]
        
        overall_score = (
            production_score * 0.4 +
            resource_score * 0.3 +
            quality_score * 0.3
        )
        
        return {
            "overall_efficiency_score": round(overall_score, 1),
            "component_scores": {
                "production": round(production_score, 1),
                "resource": round(resource_score, 1),
                "quality": round(quality_score, 1)
            },
            "grade": self._get_efficiency_grade(overall_score)
        }
    
    def _get_efficiency_grade(self, score: float) -> str:
        """Get letter grade for efficiency score."""
        if score >= 90:
            return "A - Excellent"
        elif score >= 80:
            return "B - Good"
        elif score >= 70:
            return "C - Average"
        elif score >= 60:
            return "D - Below Average"
        else:
            return "F - Poor"
    
    def _generate_recommendations(
        self,
        production: Dict[str, Any],
        resource: Dict[str, Any],
        quality: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        # Production recommendations
        if production["on_time_completion_rate"] < 0.8:
            recommendations.append({
                "area": "Production Timeline",
                "priority": "high",
                "recommendation": "Implement agile production methodology to reduce delays",
                "expected_impact": f"Reduce avg delay from {production['avg_delay_days']} to <5 days"
            })
        
        # Resource recommendations
        if resource["overloaded_teams"]:
            recommendations.append({
                "area": "Resource Allocation",
                "priority": "high",
                "recommendation": f"Redistribute workload from overloaded teams: {', '.join(resource['overloaded_teams'])}",
                "expected_impact": "Improve team efficiency by 20-30%"
            })
        
        # Quality recommendations
        if quality["rework_rate"] > 0.15:
            recommendations.append({
                "area": "Quality Control",
                "priority": "medium",
                "recommendation": "Implement pre-production quality gates to reduce rework",
                "expected_impact": f"Save ${quality['total_rework_cost']:,.0f} in rework costs"
            })
        
        return recommendations
    
    def get_team_performance(self, team_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed team performance metrics.
        
        Args:
            team_name: Specific team name (optional)
        
        Returns:
            Team performance analysis
        """
        issues = self.jira.get_production_issues(limit=1000)
        
        if team_name:
            team_issues = [i for i in issues if i["assigned_team"] == team_name]
            if not team_issues:
                return {"error": f"No issues found for team: {team_name}"}
            
            return {
                "team": team_name,
                "total_issues": len(team_issues),
                "avg_delay": round(sum(i["delay_days"] for i in team_issues) / len(team_issues), 1),
                "total_cost": sum(i["cost_overrun"] for i in team_issues),
                "issues": team_issues
            }
        else:
            # Return all teams
            resource_metrics = self._calculate_resource_utilization()
            return resource_metrics["team_workload"]


def create_resource() -> OperationalEfficiencyResource:
    """Factory function to create operational efficiency resource."""
    return OperationalEfficiencyResource()
