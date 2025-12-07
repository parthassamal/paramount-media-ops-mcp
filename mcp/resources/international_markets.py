"""
International Markets Resource.

Provides regional churn patterns and content gaps by geography.
"""

from typing import Dict, Any, List, Optional
from mcp.integrations import ContentAPIClient, AnalyticsClient


class InternationalMarketsResource:
    """Resource for international market analysis."""
    
    def __init__(self):
        """Initialize international markets resource."""
        self.content_api = ContentAPIClient()
        self.analytics = AnalyticsClient()
    
    def query(
        self,
        region: Optional[str] = None,
        min_performance: float = 0.1
    ) -> Dict[str, Any]:
        """
        Query international market performance and gaps.
        
        Args:
            region: Filter by region (e.g., "US", "UK", "LatAm")
            min_performance: Minimum performance threshold (default: 0.1)
        
        Returns:
            Dictionary with international analysis
        """
        # Get all shows with international metrics
        shows = self.content_api.get_content_catalog(limit=1000)
        
        # Aggregate by region
        regional_performance = self._aggregate_by_region(shows)
        
        # Identify content gaps by region
        content_gaps = self._identify_regional_gaps(shows, regional_performance)
        
        # Get churn patterns by region (simulated from cohort demographics)
        churn_patterns = self._analyze_regional_churn()
        
        result = {
            "regional_performance": regional_performance,
            "content_gaps": content_gaps,
            "churn_patterns": churn_patterns,
            "query_params": {
                "region": region,
                "min_performance": min_performance
            }
        }
        
        # Filter by region if specified
        if region and region in regional_performance:
            result["filtered_region"] = {
                "region": region,
                "performance": regional_performance[region],
                "gaps": [g for g in content_gaps if g["region"] == region]
            }
        
        return result
    
    def _aggregate_by_region(self, shows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate performance metrics by region."""
        regions = ["US", "Canada", "UK", "Australia", "LatAm"]
        regional_data = {}
        
        for region in regions:
            total_performance = 0
            show_count = 0
            top_shows = []
            
            for show in shows:
                perf = show["international_performance"].get(region, 0)
                if perf > 0:
                    total_performance += perf * show["viewing_hours_30d"]
                    show_count += 1
                    top_shows.append({
                        "name": show["name"],
                        "performance": perf,
                        "viewing_hours": show["viewing_hours_30d"]
                    })
            
            # Sort top shows
            top_shows_sorted = sorted(top_shows, key=lambda x: x["performance"], reverse=True)[:5]
            
            regional_data[region] = {
                "total_weighted_performance": round(total_performance, 2),
                "shows_available": show_count,
                "avg_performance": round(total_performance / show_count, 2) if show_count > 0 else 0,
                "top_shows": top_shows_sorted
            }
        
        return regional_data
    
    def _identify_regional_gaps(
        self,
        shows: List[Dict[str, Any]],
        regional_performance: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify content gaps by region."""
        gaps = []
        regions = ["US", "Canada", "UK", "Australia", "LatAm"]
        
        # Analyze genre availability by region
        for region in regions:
            regional_perf = regional_performance[region]["avg_performance"]
            
            # If region has low performance, identify potential gaps
            if regional_perf < 0.25:
                gap = {
                    "region": region,
                    "severity": "high",
                    "current_performance": regional_perf,
                    "issue": f"Low overall performance in {region}",
                    "recommendations": [
                        f"License region-specific content for {region}",
                        f"Invest in local original productions",
                        f"Improve content discovery for {region} audience"
                    ]
                }
                gaps.append(gap)
        
        # Genre-specific gaps
        genre_by_region = self._analyze_genre_distribution_by_region(shows)
        for region, genres in genre_by_region.items():
            underrepresented = [g for g, count in genres.items() if count < 3]
            if underrepresented:
                gaps.append({
                    "region": region,
                    "severity": "medium",
                    "issue": f"Underrepresented genres in {region}",
                    "missing_genres": underrepresented,
                    "recommendations": [
                        f"Expand {', '.join(underrepresented)} content for {region}"
                    ]
                })
        
        return gaps
    
    def _analyze_genre_distribution_by_region(self, shows: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        """Analyze genre distribution by region."""
        regions = ["US", "Canada", "UK", "Australia", "LatAm"]
        genre_by_region = {region: {} for region in regions}
        
        for show in shows:
            genre = show["genre"]
            for region, perf in show["international_performance"].items():
                if perf > 0.2:  # Show is relevant in this region
                    if genre not in genre_by_region[region]:
                        genre_by_region[region][genre] = 0
                    genre_by_region[region][genre] += 1
        
        return genre_by_region
    
    def _analyze_regional_churn(self) -> Dict[str, Any]:
        """Analyze churn patterns by region."""
        cohorts = self.analytics.get_churn_cohorts(risk_threshold=0.0, min_cohort_size=0)
        
        # Aggregate churn by region from cohort demographics
        regional_churn = {}
        regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
        
        for region in regions:
            regional_cohorts = [
                c for c in cohorts
                if c["demographic"]["primary_region"] == region
            ]
            
            if regional_cohorts:
                avg_risk = sum(c["churn_risk_score"] for c in regional_cohorts) / len(regional_cohorts)
                total_at_risk = sum(c["projected_churners_30d"] for c in regional_cohorts)
                
                regional_churn[region] = {
                    "avg_churn_risk": round(avg_risk, 2),
                    "total_at_risk_subscribers": total_at_risk,
                    "cohorts_analyzed": len(regional_cohorts)
                }
        
        return regional_churn
    
    def get_expansion_opportunities(self) -> Dict[str, Any]:
        """
        Identify international expansion opportunities.
        
        Returns:
            Expansion opportunity analysis
        """
        shows = self.content_api.get_content_catalog(limit=1000)
        regional_performance = self._aggregate_by_region(shows)
        
        # Calculate expansion potential
        opportunities = []
        for region, data in regional_performance.items():
            if data["avg_performance"] < 0.30:  # Low performance = opportunity
                opportunities.append({
                    "region": region,
                    "current_performance": data["avg_performance"],
                    "shows_available": data["shows_available"],
                    "expansion_potential": "high",
                    "strategy": f"Focus on licensing and original content for {region}"
                })
        
        return {
            "expansion_opportunities": opportunities,
            "total_opportunities": len(opportunities)
        }


def create_resource() -> InternationalMarketsResource:
    """Factory function to create international markets resource."""
    return InternationalMarketsResource()
