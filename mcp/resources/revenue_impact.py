"""
Revenue Impact Resource.

Provides financial correlations with churn and delays.
"""

from typing import Dict, Any, List, Optional
from mcp.integrations import AnalyticsClient, JiraConnector, ContentAPIClient, EmailParser


class RevenueImpactResource:
    """Resource for revenue impact analysis across operations."""
    
    def __init__(self):
        """Initialize revenue impact resource."""
        self.analytics = AnalyticsClient()
        self.jira = JiraConnector()
        self.content_api = ContentAPIClient()
        self.email_parser = EmailParser()
    
    def query(
        self,
        include_projections: bool = True,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Query revenue impact across all operational dimensions.
        
        Args:
            include_projections: Include future projections (default: True)
            timeframe_days: Timeframe for analysis in days (default: 30)
        
        Returns:
            Dictionary with comprehensive revenue impact analysis
        """
        # Get data from all sources
        churn_impact = self._calculate_churn_revenue_impact()
        production_impact = self._calculate_production_revenue_impact()
        complaint_impact = self._calculate_complaint_revenue_impact()
        content_impact = self._calculate_content_revenue_impact()
        
        # Aggregate total impact
        total_impact = self._aggregate_total_impact(
            churn_impact,
            production_impact,
            complaint_impact,
            content_impact
        )
        
        result = {
            "churn_revenue_impact": churn_impact,
            "production_revenue_impact": production_impact,
            "complaint_revenue_impact": complaint_impact,
            "content_revenue_impact": content_impact,
            "total_aggregated_impact": total_impact,
            "query_params": {
                "timeframe_days": timeframe_days,
                "include_projections": include_projections
            }
        }
        
        # Add projections if requested
        if include_projections:
            result["revenue_projections"] = self._generate_projections(total_impact)
        
        return result
    
    def _calculate_churn_revenue_impact(self) -> Dict[str, Any]:
        """Calculate revenue impact from churn."""
        cohorts = self.analytics.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        
        total_30d_impact = sum(c["financial_impact_30d"] for c in cohorts)
        annual_projected = total_30d_impact * 12
        
        return {
            "impact_30d": total_30d_impact,
            "annual_projected": annual_projected,
            "at_risk_subscribers": sum(c["projected_churners_30d"] for c in cohorts),
            "avg_ltv_at_risk": sum(c["avg_lifetime_value"] for c in cohorts) / len(cohorts) if cohorts else 0,
            "category": "subscriber_churn"
        }
    
    def _calculate_production_revenue_impact(self) -> Dict[str, Any]:
        """Calculate revenue impact from production delays."""
        issues = self.jira.get_production_issues(limit=1000)
        
        total_cost_overrun = sum(i["cost_overrun"] for i in issues)
        total_revenue_at_risk = sum(i["revenue_at_risk"] for i in issues)
        
        # Delays impact revenue through:
        # 1. Direct cost overruns
        # 2. Delayed monetization
        # 3. Lost subscriber growth window
        
        return {
            "direct_cost_overrun": total_cost_overrun,
            "revenue_at_risk": total_revenue_at_risk,
            "total_impact": total_cost_overrun + total_revenue_at_risk,
            "delay_days": sum(i["delay_days"] for i in issues),
            "category": "production_delays"
        }
    
    def _calculate_complaint_revenue_impact(self) -> Dict[str, Any]:
        """Calculate revenue impact from complaints."""
        themes = self.email_parser.get_complaint_themes(days_back=30, min_volume=0)
        
        total_annual_impact = sum(t["revenue_impact_annual"] for t in themes)
        total_churners = sum(t["churners_attributed"] for t in themes)
        
        return {
            "annual_impact": total_annual_impact,
            "impact_30d": total_annual_impact / 12,
            "churners_attributed": total_churners,
            "complaint_volume": sum(t["complaint_volume"] for t in themes),
            "category": "customer_complaints"
        }
    
    def _calculate_content_revenue_impact(self) -> Dict[str, Any]:
        """Calculate revenue impact from content performance."""
        shows = self.content_api.get_content_catalog(limit=1000)
        monetization = self.content_api.get_monetization_summary()
        
        # Revenue from content
        total_monthly_revenue = monetization["total_monthly_revenue"]
        
        # Opportunity cost from underperforming content
        underperforming = [s for s in shows if s["completion_rate"] < 0.5 or s["avg_rating"] < 3.5]
        opportunity_cost = len(underperforming) * 100000  # $100K per underperforming show
        
        return {
            "current_monthly_revenue": total_monthly_revenue,
            "annual_projected": total_monthly_revenue * 12,
            "opportunity_cost_annual": opportunity_cost * 12,
            "underperforming_shows": len(underperforming),
            "category": "content_performance"
        }
    
    def _aggregate_total_impact(
        self,
        churn: Dict[str, Any],
        production: Dict[str, Any],
        complaints: Dict[str, Any],
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Aggregate total revenue impact."""
        # Calculate addressable losses (things we can fix)
        addressable_annual = (
            churn["annual_projected"] +
            production["total_impact"] +
            complaints["annual_impact"]
        )
        
        # Total revenue opportunity
        total_opportunity = addressable_annual + content["opportunity_cost_annual"]
        
        return {
            "addressable_annual_loss": addressable_annual,
            "total_opportunity": total_opportunity,
            "breakdown": {
                "churn_loss": churn["annual_projected"],
                "production_delays": production["total_impact"],
                "complaint_driven": complaints["annual_impact"],
                "content_opportunity": content["opportunity_cost_annual"]
            },
            "breakdown_percentages": {
                "churn": round(churn["annual_projected"] / total_opportunity * 100, 1),
                "production": round(production["total_impact"] / total_opportunity * 100, 1),
                "complaints": round(complaints["annual_impact"] / total_opportunity * 100, 1),
                "content": round(content["opportunity_cost_annual"] / total_opportunity * 100, 1)
            }
        }
    
    def _generate_projections(self, total_impact: Dict[str, Any]) -> Dict[str, Any]:
        """Generate revenue projections with interventions."""
        baseline_loss = total_impact["addressable_annual_loss"]
        
        # Conservative scenario: Fix 30% of issues
        conservative_recovery = baseline_loss * 0.30
        
        # Moderate scenario: Fix 50% of issues
        moderate_recovery = baseline_loss * 0.50
        
        # Aggressive scenario: Fix 70% of issues
        aggressive_recovery = baseline_loss * 0.70
        
        return {
            "baseline_annual_loss": baseline_loss,
            "scenarios": {
                "conservative": {
                    "recovery_pct": 30,
                    "revenue_recovered": conservative_recovery,
                    "net_loss": baseline_loss - conservative_recovery
                },
                "moderate": {
                    "recovery_pct": 50,
                    "revenue_recovered": moderate_recovery,
                    "net_loss": baseline_loss - moderate_recovery
                },
                "aggressive": {
                    "recovery_pct": 70,
                    "revenue_recovered": aggressive_recovery,
                    "net_loss": baseline_loss - aggressive_recovery
                }
            },
            "recommendation": (
                f"Target moderate scenario: Recover ${moderate_recovery:,.0f} "
                f"by addressing top 20% of issues across all categories"
            )
        }
    
    def get_roi_prioritization(self) -> Dict[str, Any]:
        """
        Prioritize initiatives by ROI potential.
        
        Returns:
            ROI-prioritized initiative list
        """
        # Get all impacts
        result = self.query(include_projections=False)
        
        # Create initiative list with estimated ROI
        initiatives = [
            {
                "initiative": "Address top churn drivers",
                "investment_required": 2000000,  # $2M
                "revenue_impact": result["churn_revenue_impact"]["annual_projected"] * 0.5,
                "roi_ratio": (result["churn_revenue_impact"]["annual_projected"] * 0.5) / 2000000,
                "timeline": "3-6 months",
                "confidence": "high"
            },
            {
                "initiative": "Accelerate production on delayed shows",
                "investment_required": 5000000,  # $5M
                "revenue_impact": result["production_revenue_impact"]["revenue_at_risk"] * 0.6,
                "roi_ratio": (result["production_revenue_impact"]["revenue_at_risk"] * 0.6) / 5000000,
                "timeline": "6-12 months",
                "confidence": "moderate"
            },
            {
                "initiative": "Fix top complaint themes",
                "investment_required": 3000000,  # $3M
                "revenue_impact": result["complaint_revenue_impact"]["annual_impact"] * 0.7,
                "roi_ratio": (result["complaint_revenue_impact"]["annual_impact"] * 0.7) / 3000000,
                "timeline": "2-4 months",
                "confidence": "high"
            }
        ]
        
        # Sort by ROI ratio
        initiatives_sorted = sorted(initiatives, key=lambda x: x["roi_ratio"], reverse=True)
        
        return {
            "initiatives": initiatives_sorted,
            "total_investment": sum(i["investment_required"] for i in initiatives),
            "total_expected_return": sum(i["revenue_impact"] for i in initiatives),
            "blended_roi": sum(i["revenue_impact"] for i in initiatives) / sum(i["investment_required"] for i in initiatives)
        }


def create_resource() -> RevenueImpactResource:
    """Factory function to create revenue impact resource."""
    return RevenueImpactResource()
