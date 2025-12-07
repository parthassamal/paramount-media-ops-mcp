"""
Pareto Analysis Resource.

Provides 80/20 decomposition on all metrics.
"""

from typing import Dict, Any, List, Optional
from mcp.pareto import ParetoCalculator, ParetoInsights
from mcp.integrations import AnalyticsClient, JiraConnector, EmailParser, ContentAPIClient


class ParetoAnalysisResource:
    """Resource for Pareto analysis across all operational metrics."""
    
    def __init__(self):
        """Initialize Pareto analysis resource."""
        self.pareto = ParetoCalculator()
        self.insights = ParetoInsights()
        self.analytics = AnalyticsClient()
        self.jira = JiraConnector()
        self.email_parser = EmailParser()
        self.content_api = ContentAPIClient()
    
    def query(
        self,
        dimension: str = "all",
        include_insights: bool = True
    ) -> Dict[str, Any]:
        """
        Query Pareto analysis across dimensions.
        
        Args:
            dimension: Dimension to analyze ("churn", "production", "complaints", "content", "all")
            include_insights: Include business insights (default: True)
        
        Returns:
            Dictionary with Pareto analysis results
        """
        result = {
            "query_params": {
                "dimension": dimension,
                "include_insights": include_insights
            }
        }
        
        # Perform analysis based on dimension
        if dimension == "all" or dimension == "churn":
            result["churn_pareto"] = self._analyze_churn_pareto(include_insights)
        
        if dimension == "all" or dimension == "production":
            result["production_pareto"] = self._analyze_production_pareto(include_insights)
        
        if dimension == "all" or dimension == "complaints":
            result["complaints_pareto"] = self._analyze_complaints_pareto(include_insights)
        
        if dimension == "all" or dimension == "content":
            result["content_pareto"] = self._analyze_content_pareto(include_insights)
        
        # Add cross-dimensional analysis for "all"
        if dimension == "all":
            result["cross_dimensional_analysis"] = self._perform_cross_dimensional_analysis()
        
        return result
    
    def _analyze_churn_pareto(self, include_insights: bool) -> Dict[str, Any]:
        """Perform Pareto analysis on churn cohorts."""
        cohorts = self.analytics.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        
        if not cohorts:
            return {"error": "No churn data available"}
        
        pareto_result = self.pareto.analyze(
            cohorts,
            impact_field="financial_impact_30d",
            id_field="cohort_id"
        )
        
        analysis = {
            "pareto_result": pareto_result.to_dict(),
            "top_contributors": self.pareto.get_top_contributors(
                pareto_result,
                id_field="cohort_id",
                impact_field="financial_impact_30d"
            )
        }
        
        if include_insights:
            insights = self.insights.generate_insights(
                pareto_result,
                context="subscriber churn",
                impact_metric="churned_subscribers",
                item_type="cohorts"
            )
            analysis["insights"] = insights
        
        return analysis
    
    def _analyze_production_pareto(self, include_insights: bool) -> Dict[str, Any]:
        """Perform Pareto analysis on production issues."""
        issues = self.jira.get_production_issues(limit=1000)
        
        if not issues:
            return {"error": "No production data available"}
        
        # Analyze by delay days
        pareto_delays = self.pareto.analyze(
            issues,
            impact_field="delay_days",
            id_field="issue_id"
        )
        
        # Analyze by cost
        pareto_costs = self.pareto.analyze(
            issues,
            impact_field="cost_overrun",
            id_field="issue_id"
        )
        
        analysis = {
            "by_delay_days": {
                "pareto_result": pareto_delays.to_dict(),
                "top_contributors": self.pareto.get_top_contributors(
                    pareto_delays,
                    id_field="issue_id",
                    impact_field="delay_days"
                )[:5]
            },
            "by_cost_overrun": {
                "pareto_result": pareto_costs.to_dict(),
                "top_contributors": self.pareto.get_top_contributors(
                    pareto_costs,
                    id_field="issue_id",
                    impact_field="cost_overrun"
                )[:5]
            }
        }
        
        if include_insights:
            insights_delays = self.insights.generate_insights(
                pareto_delays,
                context="production delays",
                impact_metric="delay_days",
                item_type="issues"
            )
            analysis["by_delay_days"]["insights"] = insights_delays
        
        return analysis
    
    def _analyze_complaints_pareto(self, include_insights: bool) -> Dict[str, Any]:
        """Perform Pareto analysis on complaint themes."""
        themes = self.email_parser.get_complaint_themes(days_back=30, min_volume=0)
        
        if not themes:
            return {"error": "No complaint data available"}
        
        pareto_result = self.pareto.analyze(
            themes,
            impact_field="churners_attributed",
            id_field="theme_id"
        )
        
        analysis = {
            "pareto_result": pareto_result.to_dict(),
            "top_contributors": self.pareto.get_top_contributors(
                pareto_result,
                id_field="theme_id",
                impact_field="churners_attributed"
            )
        }
        
        if include_insights:
            insights = self.insights.generate_insights(
                pareto_result,
                context="customer complaints",
                impact_metric="churned_subscribers",
                item_type="themes"
            )
            analysis["insights"] = insights
        
        return analysis
    
    def _analyze_content_pareto(self, include_insights: bool) -> Dict[str, Any]:
        """Perform Pareto analysis on content performance."""
        shows = self.content_api.get_content_catalog(limit=1000)
        
        if not shows:
            return {"error": "No content data available"}
        
        pareto_viewing = self.pareto.analyze(
            shows,
            impact_field="viewing_hours_30d",
            id_field="show_id"
        )
        
        analysis = {
            "by_viewing_hours": {
                "pareto_result": pareto_viewing.to_dict(),
                "top_contributors": self.pareto.get_top_contributors(
                    pareto_viewing,
                    id_field="show_id",
                    impact_field="viewing_hours_30d"
                )[:10]
            }
        }
        
        if include_insights:
            insights = self.insights.generate_insights(
                pareto_viewing,
                context="content viewing",
                impact_metric="viewing_hours",
                item_type="shows"
            )
            analysis["by_viewing_hours"]["insights"] = insights
        
        return analysis
    
    def _perform_cross_dimensional_analysis(self) -> Dict[str, Any]:
        """Perform cross-dimensional Pareto analysis."""
        # Get all data
        cohorts = self.analytics.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        issues = self.jira.get_production_issues(limit=1000)
        themes = self.email_parser.get_complaint_themes(days_back=30, min_volume=0)
        shows = self.content_api.get_content_catalog(limit=1000)
        
        # Calculate total impacts
        total_churn_impact = sum(c["financial_impact_30d"] for c in cohorts)
        total_production_impact = sum(i["cost_overrun"] for i in issues)
        total_complaint_impact = sum(t["revenue_impact_annual"] for t in themes) / 12  # Monthly
        total_content_opportunity = len([s for s in shows if s["completion_rate"] < 0.5]) * 100000
        
        total_impact = total_churn_impact + total_production_impact + total_complaint_impact + total_content_opportunity
        
        # Create unified impact list
        impact_items = [
            {
                "category": "Churn",
                "impact": total_churn_impact,
                "percentage": round(total_churn_impact / total_impact * 100, 1),
                "top_driver": max(cohorts, key=lambda x: x["financial_impact_30d"])["name"] if cohorts else "N/A"
            },
            {
                "category": "Production Delays",
                "impact": total_production_impact,
                "percentage": round(total_production_impact / total_impact * 100, 1),
                "top_driver": max(issues, key=lambda x: x["cost_overrun"])["title"] if issues else "N/A"
            },
            {
                "category": "Complaints",
                "impact": total_complaint_impact,
                "percentage": round(total_complaint_impact / total_impact * 100, 1),
                "top_driver": max(themes, key=lambda x: x["churners_attributed"])["name"] if themes else "N/A"
            },
            {
                "category": "Content Gaps",
                "impact": total_content_opportunity,
                "percentage": round(total_content_opportunity / total_impact * 100, 1),
                "top_driver": "Underperforming content portfolio"
            }
        ]
        
        # Sort by impact
        impact_items_sorted = sorted(impact_items, key=lambda x: x["impact"], reverse=True)
        
        # Calculate cumulative
        cumulative = 0
        for item in impact_items_sorted:
            cumulative += item["percentage"]
            item["cumulative_percentage"] = round(cumulative, 1)
        
        return {
            "total_addressable_impact": total_impact,
            "impact_by_category": impact_items_sorted,
            "top_priority": impact_items_sorted[0]["category"],
            "pareto_validation": (
                "✅ Focus on top 2 categories covers "
                f"{impact_items_sorted[0]['percentage'] + impact_items_sorted[1]['percentage']:.1f}% of impact"
            )
        }
    
    def validate_pareto_principle(self) -> Dict[str, Any]:
        """
        Validate Pareto principle across all dimensions.
        
        Returns:
            Validation results for all dimensions
        """
        validation = {}
        
        # Validate churn
        cohorts = self.analytics.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        if cohorts:
            pareto_churn = self.pareto.analyze(cohorts, "financial_impact_30d", "cohort_id")
            validation["churn"] = {
                "is_valid": pareto_churn.is_pareto_valid,
                "contribution": round(pareto_churn.top_20_percent_contribution * 100, 1),
                "message": pareto_churn._get_validation_message()
            }
        
        # Validate production
        issues = self.jira.get_production_issues(limit=1000)
        if issues:
            pareto_production = self.pareto.analyze(issues, "delay_days", "issue_id")
            validation["production"] = {
                "is_valid": pareto_production.is_pareto_valid,
                "contribution": round(pareto_production.top_20_percent_contribution * 100, 1),
                "message": pareto_production._get_validation_message()
            }
        
        # Validate complaints
        themes = self.email_parser.get_complaint_themes(days_back=30, min_volume=0)
        if themes:
            pareto_complaints = self.pareto.analyze(themes, "churners_attributed", "theme_id")
            validation["complaints"] = {
                "is_valid": pareto_complaints.is_pareto_valid,
                "contribution": round(pareto_complaints.top_20_percent_contribution * 100, 1),
                "message": pareto_complaints._get_validation_message()
            }
        
        # Overall validation
        valid_count = sum(1 for v in validation.values() if v["is_valid"])
        validation["overall"] = {
            "dimensions_validated": valid_count,
            "total_dimensions": len(validation),
            "pareto_principle_holds": valid_count >= len(validation) * 0.66  # At least 2/3 dimensions
        }
        
        return validation


def create_resource() -> ParetoAnalysisResource:
    """Factory function to create Pareto analysis resource."""
    return ParetoAnalysisResource()
