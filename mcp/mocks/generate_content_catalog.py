"""
Mock data generator for content catalog.

Generates realistic Paramount+ show metadata with performance metrics.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from config import settings


class ContentCatalogGenerator:
    """Generator for content catalog with performance metrics."""
    
    def __init__(self, seed: int = None):
        """
        Initialize generator with optional seed.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed or settings.random_seed
        random.seed(self.seed)
    
    def generate(self, num_shows: int = 50) -> List[Dict[str, Any]]:
        """
        Generate content catalog with realistic Paramount+ shows.
        
        Args:
            num_shows: Number of shows to generate (default: 50)
        
        Returns:
            List of show dictionaries with performance metrics
        """
        # Real Paramount+ flagship and catalog shows
        flagship_shows = [
            {"name": "Yellowstone", "genre": "Drama", "seasons": 5, "is_original": True, "tier": "flagship"},
            {"name": "Star Trek: Discovery", "genre": "Sci-Fi", "seasons": 5, "is_original": True, "tier": "flagship"},
            {"name": "1923", "genre": "Drama", "seasons": 1, "is_original": True, "tier": "flagship"},
            {"name": "Halo", "genre": "Sci-Fi", "seasons": 2, "is_original": True, "tier": "flagship"},
            {"name": "Tulsa King", "genre": "Drama", "seasons": 1, "is_original": True, "tier": "flagship"},
            {"name": "Lioness", "genre": "Action", "seasons": 1, "is_original": True, "tier": "flagship"},
            {"name": "Mayor of Kingstown", "genre": "Drama", "seasons": 2, "is_original": True, "tier": "flagship"},
            {"name": "Frasier", "genre": "Comedy", "seasons": 1, "is_original": True, "tier": "flagship"},
            {"name": "NCIS", "genre": "Crime", "seasons": 21, "is_original": False, "tier": "catalog"},
            {"name": "Blue Bloods", "genre": "Crime", "seasons": 14, "is_original": False, "tier": "catalog"},
            {"name": "FBI", "genre": "Crime", "seasons": 6, "is_original": False, "tier": "catalog"},
            {"name": "Seal Team", "genre": "Action", "seasons": 7, "is_original": True, "tier": "catalog"},
            {"name": "Fire Country", "genre": "Drama", "seasons": 2, "is_original": False, "tier": "catalog"},
            {"name": "Ghosts", "genre": "Comedy", "seasons": 3, "is_original": False, "tier": "catalog"},
            {"name": "The Equalizer", "genre": "Action", "seasons": 4, "is_original": False, "tier": "catalog"},
        ]
        
        catalog_shows = [
            {"name": "Criminal Minds: Evolution", "genre": "Crime", "seasons": 2, "is_original": True, "tier": "catalog"},
            {"name": "CSI: Vegas", "genre": "Crime", "seasons": 3, "is_original": True, "tier": "catalog"},
            {"name": "Star Trek: Strange New Worlds", "genre": "Sci-Fi", "seasons": 2, "is_original": True, "tier": "catalog"},
            {"name": "Star Trek: Lower Decks", "genre": "Animated", "seasons": 4, "is_original": True, "tier": "catalog"},
            {"name": "Star Trek: Picard", "genre": "Sci-Fi", "seasons": 3, "is_original": True, "tier": "catalog"},
            {"name": "Evil", "genre": "Horror", "seasons": 4, "is_original": True, "tier": "catalog"},
            {"name": "Billions", "genre": "Drama", "seasons": 7, "is_original": False, "tier": "catalog"},
            {"name": "The Good Fight", "genre": "Legal", "seasons": 6, "is_original": True, "tier": "catalog"},
            {"name": "Why Women Kill", "genre": "Comedy", "seasons": 2, "is_original": True, "tier": "catalog"},
            {"name": "Rabbit Hole", "genre": "Thriller", "seasons": 1, "is_original": True, "tier": "catalog"},
        ]
        
        shows = []
        all_show_templates = flagship_shows + catalog_shows
        
        for i in range(min(num_shows, len(all_show_templates))):
            template = all_show_templates[i]
            
            # Generate performance metrics with Pareto distribution
            # Flagship shows get higher metrics
            if template["tier"] == "flagship":
                viewing_hours = random.randint(8000000, 25000000)
                completion_rate = random.uniform(0.65, 0.85)
                retention_contribution = random.uniform(0.15, 0.35)
            else:
                viewing_hours = random.randint(500000, 8000000)
                completion_rate = random.uniform(0.35, 0.65)
                retention_contribution = random.uniform(0.02, 0.15)
            
            show = {
                "show_id": f"SHOW-{i+1:04d}",
                "name": template["name"],
                "genre": template["genre"],
                "seasons": template["seasons"],
                "is_original": template["is_original"],
                "tier": template["tier"],
                "release_date": self._generate_release_date(template["seasons"]),
                "viewing_hours_30d": viewing_hours,
                "unique_viewers_30d": int(viewing_hours / random.uniform(8, 15)),
                "completion_rate": completion_rate,
                "avg_rating": random.uniform(3.5, 4.8),
                "retention_contribution": retention_contribution,
                "production_budget_season": self._estimate_budget(template),
                "revenue_per_viewer": random.uniform(5, 25),
                "churn_impact": -retention_contribution,  # Negative = reduces churn
                "content_gaps": self._identify_content_gaps(template),
                "international_performance": self._generate_international_metrics(),
                "demographics": self._generate_demographics(),
                "monetization": {
                    "ad_revenue_30d": int(viewing_hours * random.uniform(0.05, 0.15)),
                    "subscription_attribution": random.randint(5000, 50000),
                    "licensing_revenue_annual": random.randint(100000, 5000000) if not template["is_original"] else 0
                }
            }
            
            shows.append(show)
        
        # Fill remaining slots with generic shows if needed
        for i in range(len(all_show_templates), num_shows):
            shows.append(self._generate_generic_show(i))
        
        return shows
    
    def _generate_release_date(self, seasons: int) -> str:
        """Generate realistic release date based on seasons."""
        years_ago = min(seasons, 10)
        release_date = datetime.now() - timedelta(days=years_ago*365 + random.randint(0, 365))
        return release_date.strftime("%Y-%m-%d")
    
    def _estimate_budget(self, template: Dict[str, Any]) -> int:
        """Estimate production budget per season."""
        budget_ranges = {
            ("flagship", True): (8000000, 15000000),  # Original flagship
            ("flagship", False): (0, 0),  # Licensed flagship (no production cost)
            ("catalog", True): (3000000, 8000000),  # Original catalog
            ("catalog", False): (0, 0)  # Licensed catalog
        }
        
        range_key = (template["tier"], template["is_original"])
        min_budget, max_budget = budget_ranges.get(range_key, (1000000, 5000000))
        
        return random.randint(min_budget, max_budget) if max_budget > 0 else 0
    
    def _identify_content_gaps(self, template: Dict[str, Any]) -> List[str]:
        """Identify content gaps for the show."""
        gaps = []
        
        if template["genre"] in ["Sci-Fi", "Fantasy"]:
            gaps.append("High demand for more sci-fi content")
        
        if not template["is_original"]:
            gaps.append("Risk: Licensed content may be lost to competitors")
        
        if template["seasons"] == 1:
            gaps.append("Need renewal decision to maintain audience")
        
        return gaps if gaps else ["No significant gaps identified"]
    
    def _generate_international_metrics(self) -> Dict[str, float]:
        """Generate international performance metrics."""
        regions = ["US", "Canada", "UK", "Australia", "LatAm"]
        return {region: round(random.uniform(0.1, 0.4), 2) for region in regions}
    
    def _generate_demographics(self) -> Dict[str, Any]:
        """Generate viewer demographics."""
        return {
            "primary_age_group": random.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
            "gender_split": {
                "male": round(random.uniform(0.4, 0.6), 2),
                "female": round(random.uniform(0.4, 0.6), 2)
            },
            "household_income": random.choice(["<50K", "50-100K", "100-150K", "150K+"])
        }
    
    def _generate_generic_show(self, index: int) -> Dict[str, Any]:
        """Generate a generic show entry."""
        genres = ["Drama", "Comedy", "Crime", "Action", "Thriller", "Documentary"]
        
        return {
            "show_id": f"SHOW-{index+1:04d}",
            "name": f"Generic Show {index+1}",
            "genre": random.choice(genres),
            "seasons": random.randint(1, 5),
            "is_original": random.choice([True, False]),
            "tier": "catalog",
            "release_date": self._generate_release_date(random.randint(1, 5)),
            "viewing_hours_30d": random.randint(100000, 2000000),
            "unique_viewers_30d": random.randint(10000, 200000),
            "completion_rate": random.uniform(0.3, 0.7),
            "avg_rating": random.uniform(3.0, 4.5),
            "retention_contribution": random.uniform(0.01, 0.10),
            "production_budget_season": random.randint(1000000, 5000000),
            "revenue_per_viewer": random.uniform(5, 15),
            "churn_impact": random.uniform(-0.1, -0.01),
            "content_gaps": ["Generic content entry"],
            "international_performance": self._generate_international_metrics(),
            "demographics": self._generate_demographics(),
            "monetization": {
                "ad_revenue_30d": random.randint(10000, 500000),
                "subscription_attribution": random.randint(1000, 10000),
                "licensing_revenue_annual": random.randint(50000, 1000000)
            }
        }
    
    def get_pareto_summary(self, shows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Pareto distribution summary for content.
        
        Args:
            shows: List of generated shows
        
        Returns:
            Pareto analysis summary
        """
        total_viewing_hours = sum(show["viewing_hours_30d"] for show in shows)
        
        # Sort by viewing hours
        sorted_shows = sorted(shows, key=lambda x: x["viewing_hours_30d"], reverse=True)
        
        # Calculate top 20%
        top_20_count = max(1, len(shows) // 5)
        top_20_hours = sum(show["viewing_hours_30d"] for show in sorted_shows[:top_20_count])
        top_20_contribution = top_20_hours / total_viewing_hours if total_viewing_hours > 0 else 0
        
        return {
            "total_shows": len(shows),
            "total_viewing_hours_30d": total_viewing_hours,
            "top_20_percent_count": top_20_count,
            "top_20_percent_contribution": round(top_20_contribution, 2),
            "top_shows": [
                {
                    "show_id": show["show_id"],
                    "name": show["name"],
                    "viewing_hours": show["viewing_hours_30d"]
                }
                for show in sorted_shows[:top_20_count]
            ],
            "pareto_validated": 0.75 <= top_20_contribution <= 0.85
        }
