"""
Content Catalog Resource.

Provides show metadata and performance metrics.
"""

from typing import Dict, Any, List, Optional
from mcp.integrations import ContentAPIClient
from mcp.pareto import ParetoCalculator


class ContentCatalogResource:
    """Resource for content catalog and performance."""
    
    def __init__(self):
        """Initialize content catalog resource."""
        self.content_api = ContentAPIClient()
        self.pareto = ParetoCalculator()
    
    def query(
        self,
        genre: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 50,
        include_pareto: bool = True
    ) -> Dict[str, Any]:
        """
        Query content catalog with performance metrics.
        
        Args:
            genre: Filter by genre (optional)
            tier: Filter by tier: "flagship" or "catalog" (optional)
            limit: Maximum number of shows to return (default: 50)
            include_pareto: Include Pareto analysis (default: True)
        
        Returns:
            Dictionary with shows and analysis
        """
        # Get content catalog
        shows = self.content_api.get_content_catalog(
            genre=genre,
            tier=tier,
            limit=limit
        )
        
        # Get performance summary
        performance = self.content_api.get_performance_summary()
        
        # Get genre analysis
        genre_analysis = self.content_api.get_genre_analysis()
        
        # Get monetization summary
        monetization = self.content_api.get_monetization_summary()
        
        result = {
            "shows": shows,
            "performance_summary": performance,
            "genre_analysis": genre_analysis,
            "monetization_summary": monetization,
            "query_params": {
                "genre": genre,
                "tier": tier,
                "limit": limit
            }
        }
        
        # Add Pareto analysis if requested
        if include_pareto and shows:
            # Analyze by viewing hours
            pareto_viewing = self.pareto.analyze(
                shows,
                impact_field="viewing_hours_30d",
                id_field="show_id"
            )
            
            # Analyze by retention contribution
            shows_with_positive_retention = [
                s for s in shows if s["retention_contribution"] > 0
            ]
            
            if shows_with_positive_retention:
                pareto_retention = self.pareto.analyze(
                    shows_with_positive_retention,
                    impact_field="retention_contribution",
                    id_field="show_id"
                )
                
                result["pareto_analysis"] = {
                    "by_viewing_hours": pareto_viewing.to_dict(),
                    "by_retention_contribution": pareto_retention.to_dict()
                }
            else:
                result["pareto_analysis"] = {
                    "by_viewing_hours": pareto_viewing.to_dict()
                }
        
        return result
    
    def get_show_details(self, show_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific show.
        
        Args:
            show_id: Show identifier (e.g., "SHOW-0001")
        
        Returns:
            Show details or None if not found
        """
        return self.content_api.get_show_by_id(show_id)
    
    def get_show_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get show details by name.
        
        Args:
            name: Show name
        
        Returns:
            Show details or None if not found
        """
        return self.content_api.get_show_by_name(name)
    
    def get_underperforming_content(self) -> Dict[str, Any]:
        """
        Identify underperforming content that may need intervention.
        
        Returns:
            Analysis of underperforming content
        """
        shows = self.content_api.get_content_catalog(limit=1000)
        
        # Define underperformance criteria
        underperforming = []
        for show in shows:
            score = 0
            reasons = []
            
            # Low completion rate
            if show["completion_rate"] < 0.5:
                score += 3
                reasons.append(f"Low completion rate: {show['completion_rate']:.0%}")
            
            # Low rating
            if show["avg_rating"] < 3.5:
                score += 2
                reasons.append(f"Low rating: {show['avg_rating']:.1f}/5")
            
            # Negative churn impact (increases churn)
            if show["churn_impact"] > 0:
                score += 4
                reasons.append(f"Increases churn by {show['churn_impact']:.1%}")
            
            # Low viewing hours for tier
            if show["tier"] == "flagship" and show["viewing_hours_30d"] < 5000000:
                score += 3
                reasons.append("Low viewing hours for flagship show")
            
            if score >= 5:  # Threshold for underperforming
                underperforming.append({
                    **show,
                    "underperformance_score": score,
                    "reasons": reasons
                })
        
        # Sort by underperformance score
        underperforming_sorted = sorted(
            underperforming,
            key=lambda x: x["underperformance_score"],
            reverse=True
        )
        
        return {
            "underperforming_shows": underperforming_sorted,
            "total_count": len(underperforming),
            "recommendation": (
                f"{len(underperforming)} shows identified as underperforming. "
                "Consider content refresh, marketing boost, or removal."
            )
        }
    
    def get_content_gaps(self) -> Dict[str, Any]:
        """
        Identify content gaps and opportunities.
        
        Returns:
            Content gap analysis
        """
        shows = self.content_api.get_content_catalog(limit=1000)
        
        # Analyze genre distribution
        genre_count = {}
        genre_performance = {}
        
        for show in shows:
            genre = show["genre"]
            if genre not in genre_count:
                genre_count[genre] = 0
                genre_performance[genre] = []
            
            genre_count[genre] += 1
            genre_performance[genre].append(show["viewing_hours_30d"])
        
        # Calculate average performance by genre
        genre_avg_performance = {
            genre: sum(hours) / len(hours)
            for genre, hours in genre_performance.items()
        }
        
        # Identify gaps (high performance, low count)
        gaps = []
        for genre, avg_perf in genre_avg_performance.items():
            count = genre_count[genre]
            if avg_perf > 3000000 and count < 5:  # High performance, few shows
                gaps.append({
                    "genre": genre,
                    "current_count": count,
                    "avg_viewing_hours": avg_perf,
                    "recommendation": f"Invest in more {genre} content - high demand, low supply"
                })
        
        return {
            "content_gaps": gaps,
            "genre_distribution": genre_count,
            "top_performing_genres": sorted(
                genre_avg_performance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


def create_resource() -> ContentCatalogResource:
    """Factory function to create content catalog resource."""
    return ContentCatalogResource()
