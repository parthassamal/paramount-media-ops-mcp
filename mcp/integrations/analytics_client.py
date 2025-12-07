"""
Analytics client for churn signals and retention curves.

Provides interface to analytics API with mock mode support.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from config import settings
from mcp.mocks.generate_churn_cohorts import ChurnCohortGenerator


class AnalyticsClient:
    """
    Client for analytics API to fetch churn signals and retention data.
    
    In mock mode, returns generated data. In production, connects to analytics platform.
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize analytics client.
        
        Args:
            mock_mode: If True, use mock data. If None, use settings default.
        """
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
        self.api_url = settings.analytics_api_url
        self.api_key = settings.analytics_api_key
        
        if self.mock_mode:
            self.generator = ChurnCohortGenerator()
    
    def get_churn_cohorts(
        self,
        risk_threshold: float = 0.3,
        min_cohort_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get at-risk subscriber cohorts.
        
        Args:
            risk_threshold: Minimum churn risk score to include (0-1)
            min_cohort_size: Minimum cohort size to include
        
        Returns:
            List of churn cohort dictionaries
        """
        if self.mock_mode:
            return self._get_mock_cohorts(risk_threshold, min_cohort_size)
        else:
            return self._fetch_from_analytics(risk_threshold, min_cohort_size)
    
    def _get_mock_cohorts(self, risk_threshold: float, min_cohort_size: int) -> List[Dict[str, Any]]:
        """Get mock churn cohorts."""
        cohorts = self.generator.generate(num_cohorts=5)
        
        # Apply filters
        cohorts = [
            c for c in cohorts
            if c["churn_risk_score"] >= risk_threshold
            and c["size"] >= min_cohort_size
        ]
        
        return cohorts
    
    def _fetch_from_analytics(self, risk_threshold: float, min_cohort_size: int) -> List[Dict[str, Any]]:
        """Fetch from real analytics API."""
        # TODO: Implement real analytics API integration
        raise NotImplementedError("Real analytics integration not yet implemented. Use mock_mode=True.")
    
    def get_cohort_by_id(self, cohort_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific cohort by ID.
        
        Args:
            cohort_id: Cohort ID (e.g., "COHORT-001")
        
        Returns:
            Cohort dictionary or None if not found
        """
        cohorts = self.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        for cohort in cohorts:
            if cohort["cohort_id"] == cohort_id:
                return cohort
        return None
    
    def get_retention_metrics(self) -> Dict[str, Any]:
        """
        Get overall retention metrics.
        
        Returns:
            Retention metrics dictionary
        """
        cohorts = self.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        
        total_subscribers = sum(c["size"] for c in cohorts)
        total_at_risk = sum(c["projected_churners_30d"] for c in cohorts)
        total_financial_impact = sum(c["financial_impact_30d"] for c in cohorts)
        
        # Calculate weighted average risk score
        weighted_risk = sum(
            c["churn_risk_score"] * c["size"] for c in cohorts
        ) / total_subscribers if total_subscribers > 0 else 0
        
        return {
            "total_subscribers": total_subscribers,
            "total_at_risk_30d": total_at_risk,
            "churn_rate_30d": round(total_at_risk / total_subscribers, 4) if total_subscribers > 0 else 0,
            "weighted_avg_risk_score": round(weighted_risk, 2),
            "financial_impact_30d": total_financial_impact,
            "annual_projected_impact": total_financial_impact * 12,
            "cohorts_analyzed": len(cohorts)
        }
    
    def get_engagement_metrics(self, cohort_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get engagement metrics for cohorts.
        
        Args:
            cohort_id: Optional cohort ID to filter
        
        Returns:
            Engagement metrics dictionary
        """
        if cohort_id:
            cohort = self.get_cohort_by_id(cohort_id)
            cohorts = [cohort] if cohort else []
        else:
            cohorts = self.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        
        if not cohorts:
            return {"error": "No cohorts found"}
        
        avg_engagement_drop = sum(
            c["content_engagement_drop_pct"] for c in cohorts
        ) / len(cohorts)
        
        avg_complaint_rate = sum(
            c["complaint_rate"] for c in cohorts
        ) / len(cohorts)
        
        return {
            "cohorts_analyzed": len(cohorts),
            "avg_engagement_drop": round(avg_engagement_drop, 2),
            "avg_complaint_rate": round(avg_complaint_rate, 2),
            "cohort_details": [
                {
                    "cohort_id": c["cohort_id"],
                    "name": c["name"],
                    "engagement_drop": c["content_engagement_drop_pct"],
                    "complaint_rate": c["complaint_rate"]
                }
                for c in cohorts
            ]
        }
    
    def get_ltv_analysis(self) -> Dict[str, Any]:
        """
        Get lifetime value analysis across cohorts.
        
        Returns:
            LTV analysis dictionary
        """
        cohorts = self.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        
        # Sort by LTV
        sorted_cohorts = sorted(cohorts, key=lambda x: x["avg_lifetime_value"], reverse=True)
        
        total_ltv_at_risk = sum(
            c["avg_lifetime_value"] * c["projected_churners_30d"] for c in cohorts
        )
        
        high_value_cohorts = [c for c in cohorts if c["avg_lifetime_value"] >= 500]
        high_value_impact = sum(
            c["financial_impact_30d"] for c in high_value_cohorts
        )
        
        return {
            "total_ltv_at_risk": total_ltv_at_risk,
            "high_value_cohorts": len(high_value_cohorts),
            "high_value_impact_pct": round(
                high_value_impact / sum(c["financial_impact_30d"] for c in cohorts), 2
            ) if cohorts else 0,
            "cohort_ltv_ranking": [
                {
                    "cohort_id": c["cohort_id"],
                    "name": c["name"],
                    "avg_ltv": c["avg_lifetime_value"],
                    "financial_impact": c["financial_impact_30d"]
                }
                for c in sorted_cohorts
            ]
        }
