"""
Content API client for catalog and performance data.

Provides interface to content API with mock mode support.
"""

from typing import List, Dict, Any, Optional
from config import settings
from mcp.mocks.generate_content_catalog import ContentCatalogGenerator


class ContentAPIClient:
    """
    Client for content API to fetch catalog and performance data.
    
    In mock mode, returns generated data. In production, connects to content management system.
    """
    
    def __init__(self, mock_mode: bool = None):
        """
        Initialize content API client.
        
        Args:
            mock_mode: If True, use mock data. If None, use settings default.
        """
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
        self.api_url = settings.content_api_url
        self.api_key = settings.content_api_key
        
        if self.mock_mode:
            self.generator = ContentCatalogGenerator()
    
    def get_content_catalog(
        self,
        genre: Optional[str] = None,
        tier: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get content catalog with performance metrics.
        
        Args:
            genre: Filter by genre (optional)
            tier: Filter by tier: "flagship" or "catalog" (optional)
            limit: Maximum number of shows to return
        
        Returns:
            List of show dictionaries
        """
        if self.mock_mode:
            return self._get_mock_catalog(genre, tier, limit)
        else:
            return self._fetch_from_api(genre, tier, limit)
    
    def _get_mock_catalog(
        self,
        genre: Optional[str],
        tier: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get mock content catalog."""
        shows = self.generator.generate(num_shows=50)
        
        # Apply filters
        if genre:
            shows = [s for s in shows if s["genre"] == genre]
        
        if tier:
            shows = [s for s in shows if s["tier"] == tier]
        
        return shows[:limit]
    
    def _fetch_from_api(
        self,
        genre: Optional[str],
        tier: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch from real content API."""
        # TODO: Implement real content API integration
        raise NotImplementedError("Real content API integration not yet implemented. Use mock_mode=True.")
    
    def get_show_by_id(self, show_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific show by ID.
        
        Args:
            show_id: Show ID (e.g., "SHOW-0001")
        
        Returns:
            Show dictionary or None if not found
        """
        shows = self.get_content_catalog(limit=1000)
        for show in shows:
            if show["show_id"] == show_id:
                return show
        return None
    
    def get_show_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific show by name.
        
        Args:
            name: Show name
        
        Returns:
            Show dictionary or None if not found
        """
        shows = self.get_content_catalog(limit=1000)
        for show in shows:
            if show["name"].lower() == name.lower():
                return show
        return None
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get overall content performance summary.
        
        Returns:
            Performance summary dictionary
        """
        shows = self.get_content_catalog(limit=1000)
        
        total_viewing_hours = sum(s["viewing_hours_30d"] for s in shows)
        total_viewers = sum(s["unique_viewers_30d"] for s in shows)
        
        # Calculate averages
        avg_completion = sum(s["completion_rate"] for s in shows) / len(shows) if shows else 0
        avg_rating = sum(s["avg_rating"] for s in shows) / len(shows) if shows else 0
        
        # Top performers
        top_by_viewing = sorted(shows, key=lambda x: x["viewing_hours_30d"], reverse=True)[:10]
        top_by_retention = sorted(shows, key=lambda x: x["retention_contribution"], reverse=True)[:10]
        
        return {
            "total_shows": len(shows),
            "total_viewing_hours_30d": total_viewing_hours,
            "total_unique_viewers_30d": total_viewers,
            "avg_completion_rate": round(avg_completion, 2),
            "avg_rating": round(avg_rating, 2),
            "flagship_shows": len([s for s in shows if s["tier"] == "flagship"]),
            "original_shows": len([s for s in shows if s["is_original"]]),
            "top_by_viewing_hours": [
                {
                    "show_id": s["show_id"],
                    "name": s["name"],
                    "viewing_hours": s["viewing_hours_30d"]
                }
                for s in top_by_viewing
            ],
            "top_by_retention_contribution": [
                {
                    "show_id": s["show_id"],
                    "name": s["name"],
                    "retention_contribution": s["retention_contribution"]
                }
                for s in top_by_retention
            ]
        }
    
    def get_genre_analysis(self) -> Dict[str, Any]:
        """
        Get performance analysis by genre.
        
        Returns:
            Genre analysis dictionary
        """
        shows = self.get_content_catalog(limit=1000)
        
        # Group by genre
        by_genre = {}
        for show in shows:
            genre = show["genre"]
            if genre not in by_genre:
                by_genre[genre] = {
                    "count": 0,
                    "total_viewing_hours": 0,
                    "total_viewers": 0,
                    "shows": []
                }
            by_genre[genre]["count"] += 1
            by_genre[genre]["total_viewing_hours"] += show["viewing_hours_30d"]
            by_genre[genre]["total_viewers"] += show["unique_viewers_30d"]
            by_genre[genre]["shows"].append(show["name"])
        
        # Calculate averages and sort
        for genre_data in by_genre.values():
            genre_data["avg_viewing_hours"] = genre_data["total_viewing_hours"] / genre_data["count"]
        
        return {
            "genres_analyzed": len(by_genre),
            "by_genre": by_genre,
            "top_genre_by_viewing": max(
                by_genre.items(),
                key=lambda x: x[1]["total_viewing_hours"]
            )[0] if by_genre else None
        }
    
    def get_monetization_summary(self) -> Dict[str, Any]:
        """
        Get monetization summary across content.
        
        Returns:
            Monetization summary dictionary
        """
        shows = self.get_content_catalog(limit=1000)
        
        total_ad_revenue = sum(s["monetization"]["ad_revenue_30d"] for s in shows)
        total_subscription_attribution = sum(s["monetization"]["subscription_attribution"] for s in shows)
        total_licensing = sum(s["monetization"]["licensing_revenue_annual"] for s in shows)
        
        return {
            "total_ad_revenue_30d": total_ad_revenue,
            "total_subscription_attribution": total_subscription_attribution,
            "total_licensing_revenue_annual": total_licensing,
            "total_monthly_revenue": total_ad_revenue + (total_subscription_attribution * 9.99),
            "revenue_mix": {
                "ad_supported": round(total_ad_revenue / (total_ad_revenue + total_subscription_attribution * 9.99), 2) if (total_ad_revenue + total_subscription_attribution) > 0 else 0,
                "subscription": round((total_subscription_attribution * 9.99) / (total_ad_revenue + total_subscription_attribution * 9.99), 2) if (total_ad_revenue + total_subscription_attribution) > 0 else 0
            }
        }
