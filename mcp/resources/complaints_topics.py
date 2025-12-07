"""
Complaints Topics Resource.

Provides support tickets clustered by NLP themes.
"""

from typing import Dict, Any, List, Optional
from mcp.integrations import EmailParser
from mcp.pareto import ParetoCalculator, ParetoInsights


class ComplaintsTopicsResource:
    """Resource for complaint themes and analysis."""
    
    def __init__(self):
        """Initialize complaints topics resource."""
        self.email_parser = EmailParser()
        self.pareto = ParetoCalculator()
        self.insights = ParetoInsights()
    
    def query(
        self,
        days_back: int = 30,
        min_volume: int = 100,
        include_pareto: bool = True
    ) -> Dict[str, Any]:
        """
        Query complaint themes and sentiment analysis.
        
        Args:
            days_back: Number of days to analyze (default: 30)
            min_volume: Minimum complaint volume to include (default: 100)
            include_pareto: Include Pareto analysis (default: True)
        
        Returns:
            Dictionary with themes and analysis
        """
        # Get complaint themes
        themes = self.email_parser.get_complaint_themes(
            days_back=days_back,
            min_volume=min_volume
        )
        
        # Get sentiment trends
        sentiment_trends = self.email_parser.get_sentiment_trends(days_back)
        
        # Get churn correlation
        churn_correlation = self.email_parser.get_churn_correlation_analysis()
        
        result = {
            "themes": themes,
            "sentiment_trends": sentiment_trends,
            "churn_correlation": churn_correlation,
            "query_params": {
                "days_back": days_back,
                "min_volume": min_volume
            }
        }
        
        # Add Pareto analysis if requested
        if include_pareto and themes:
            # Analyze by churners attributed
            pareto_result = self.pareto.analyze(
                themes,
                impact_field="churners_attributed",
                id_field="theme_id"
            )
            
            result["pareto_analysis"] = pareto_result.to_dict()
            
            # Generate insights
            insights = self.insights.generate_insights(
                pareto_result,
                context="customer complaints",
                impact_metric="churned_subscribers",
                item_type="complaint themes"
            )
            result["pareto_insights"] = insights
        
        return result
    
    def get_theme_details(self, theme_id: str, limit: int = 50) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific theme including individual complaints.
        
        Args:
            theme_id: Theme identifier (e.g., "THEME-001")
            limit: Maximum number of complaints to return
        
        Returns:
            Theme details with sample complaints
        """
        themes = self.email_parser.get_complaint_themes(days_back=90, min_volume=0)
        
        theme = None
        for t in themes:
            if t["theme_id"] == theme_id:
                theme = t
                break
        
        if not theme:
            return None
        
        # Get individual complaints for this theme
        complaints = self.email_parser.get_individual_complaints(
            theme_id=theme_id,
            limit=limit
        )
        
        return {
            "theme": theme,
            "sample_complaints": complaints[:10],  # Return top 10 as samples
            "total_complaints_retrieved": len(complaints)
        }
    
    def get_fixable_themes(self) -> Dict[str, Any]:
        """
        Get themes that are fixable with prioritization.
        
        Returns:
            Fixable themes sorted by impact
        """
        themes = self.email_parser.get_complaint_themes(days_back=30, min_volume=0)
        
        # Filter fixable themes
        fixable = [t for t in themes if t.get("is_fixable", False)]
        
        # Sort by revenue impact
        fixable_sorted = sorted(
            fixable,
            key=lambda x: x["revenue_impact_annual"],
            reverse=True
        )
        
        # Calculate total addressable impact
        total_addressable = sum(t["revenue_impact_annual"] for t in fixable)
        
        return {
            "fixable_themes": fixable_sorted,
            "total_fixable_count": len(fixable),
            "total_addressable_revenue": total_addressable,
            "breakdown_by_complexity": {
                "low": [t for t in fixable if t["fix_complexity"] == "low"],
                "medium": [t for t in fixable if t["fix_complexity"] == "medium"],
                "high": [t for t in fixable if t["fix_complexity"] == "high"]
            }
        }


def create_resource() -> ComplaintsTopicsResource:
    """Factory function to create complaints topics resource."""
    return ComplaintsTopicsResource()
