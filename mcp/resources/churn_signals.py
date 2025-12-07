"""
Churn Signals Resource.

Provides subscriber cohorts and retention risk scores.
"""

from typing import Dict, Any, List, Optional
from mcp.integrations import AnalyticsClient
from mcp.pareto import ParetoCalculator


class ChurnSignalsResource:
    """Resource for churn signals and at-risk subscriber cohorts."""
    
    def __init__(self):
        """Initialize churn signals resource."""
        self.analytics = AnalyticsClient()
        self.pareto = ParetoCalculator()
    
    def query(
        self,
        risk_threshold: float = 0.3,
        min_cohort_size: int = 1000,
        include_pareto: bool = True
    ) -> Dict[str, Any]:
        """
        Query churn signals and at-risk cohorts.
        
        Args:
            risk_threshold: Minimum churn risk score (0-1, default: 0.3)
            min_cohort_size: Minimum cohort size to include (default: 1000)
            include_pareto: Include Pareto analysis (default: True)
        
        Returns:
            Dictionary with cohorts and analysis
        """
        # Get cohorts from analytics
        cohorts = self.analytics.get_churn_cohorts(
            risk_threshold=risk_threshold,
            min_cohort_size=min_cohort_size
        )
        
        # Get additional metrics
        retention_metrics = self.analytics.get_retention_metrics()
        ltv_analysis = self.analytics.get_ltv_analysis()
        
        result = {
            "cohorts": cohorts,
            "retention_metrics": retention_metrics,
            "ltv_analysis": ltv_analysis,
            "query_params": {
                "risk_threshold": risk_threshold,
                "min_cohort_size": min_cohort_size
            }
        }
        
        # Add Pareto analysis if requested
        if include_pareto and cohorts:
            pareto_result = self.pareto.analyze(
                cohorts,
                impact_field="financial_impact_30d",
                id_field="cohort_id"
            )
            result["pareto_analysis"] = pareto_result.to_dict()
            result["pareto_top_cohorts"] = self.pareto.get_top_contributors(
                pareto_result,
                id_field="cohort_id",
                impact_field="financial_impact_30d"
            )
        
        return result
    
    def get_cohort_details(self, cohort_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific cohort.
        
        Args:
            cohort_id: Cohort identifier (e.g., "COHORT-001")
        
        Returns:
            Cohort details or None if not found
        """
        cohort = self.analytics.get_cohort_by_id(cohort_id)
        
        if not cohort:
            return None
        
        # Enrich with engagement metrics
        engagement = self.analytics.get_engagement_metrics(cohort_id)
        
        return {
            "cohort": cohort,
            "engagement_metrics": engagement
        }


def create_resource() -> ChurnSignalsResource:
    """Factory function to create churn signals resource."""
    return ChurnSignalsResource()
