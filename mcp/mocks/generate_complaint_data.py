"""
Mock data generator for complaint data.

Generates realistic customer complaints with NLP-clustered themes.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from config import settings


class ComplaintDataGenerator:
    """Generator for customer complaints with Pareto-distributed themes."""
    
    def __init__(self, seed: int = None):
        """
        Initialize generator with optional seed.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed or settings.random_seed
        random.seed(self.seed)
    
    def generate_themes(self, num_themes: int = 10) -> List[Dict[str, Any]]:
        """
        Generate complaint themes where top 20% drive 70% of churn.
        
        Args:
            num_themes: Number of themes to generate (default: 10)
        
        Returns:
            List of complaint theme dictionaries
        """
        # Pre-defined themes with Pareto distribution
        theme_templates = [
            # Top 2 themes driving 70% of churn
            {
                "name": "Buffering/Streaming Quality",
                "volume": 8420,
                "churn_correlation": 0.68,
                "avg_sentiment": -0.72,
                "keywords": ["buffering", "loading", "quality", "freezing", "lag"],
                "fixable": True,
                "fix_complexity": "high"
            },
            {
                "name": "Content Library Gaps",
                "volume": 6890,
                "churn_correlation": 0.61,
                "avg_sentiment": -0.58,
                "keywords": ["missing shows", "no content", "library", "selection", "removed"],
                "fixable": True,
                "fix_complexity": "high"
            },
            # Mid-tier themes
            {
                "name": "App Crashes/Technical Issues",
                "volume": 4120,
                "churn_correlation": 0.45,
                "avg_sentiment": -0.81,
                "keywords": ["crash", "error", "not working", "bug", "login"],
                "fixable": True,
                "fix_complexity": "medium"
            },
            {
                "name": "Price/Value Concerns",
                "volume": 3450,
                "churn_correlation": 0.52,
                "avg_sentiment": -0.42,
                "keywords": ["expensive", "price", "not worth", "subscription", "cost"],
                "fixable": True,
                "fix_complexity": "medium"
            },
            {
                "name": "Ad Experience (Ad-Tier)",
                "volume": 2890,
                "churn_correlation": 0.38,
                "avg_sentiment": -0.55,
                "keywords": ["too many ads", "same ad", "ad quality", "interruption"],
                "fixable": True,
                "fix_complexity": "low"
            },
            {
                "name": "Device Compatibility",
                "volume": 2340,
                "churn_correlation": 0.33,
                "avg_sentiment": -0.64,
                "keywords": ["not supported", "device", "compatibility", "smart tv"],
                "fixable": True,
                "fix_complexity": "high"
            },
            # Long tail themes
            {
                "name": "Customer Service Response Time",
                "volume": 1820,
                "churn_correlation": 0.28,
                "avg_sentiment": -0.48,
                "keywords": ["support", "no response", "waiting", "help"],
                "fixable": True,
                "fix_complexity": "low"
            },
            {
                "name": "Audio/Subtitle Issues",
                "volume": 1450,
                "churn_correlation": 0.22,
                "avg_sentiment": -0.53,
                "keywords": ["audio", "subtitles", "sync", "volume"],
                "fixable": True,
                "fix_complexity": "medium"
            },
            {
                "name": "Account/Billing Issues",
                "volume": 980,
                "churn_correlation": 0.31,
                "avg_sentiment": -0.66,
                "keywords": ["charged", "billing", "cancel", "refund"],
                "fixable": True,
                "fix_complexity": "low"
            },
            {
                "name": "User Interface/UX",
                "volume": 720,
                "churn_correlation": 0.19,
                "avg_sentiment": -0.38,
                "keywords": ["confusing", "hard to find", "interface", "navigate"],
                "fixable": True,
                "fix_complexity": "medium"
            }
        ]
        
        themes = []
        base_date = datetime.now() - timedelta(days=90)
        
        for i, template in enumerate(theme_templates[:num_themes], 1):
            # Calculate impact metrics
            churners_attributed = int(template["volume"] * template["churn_correlation"])
            revenue_impact = churners_attributed * 9.99 * 12  # Annual impact at $9.99/month
            
            theme = {
                "theme_id": f"THEME-{i:03d}",
                "name": template["name"],
                "complaint_volume": template["volume"],
                "churn_correlation": template["churn_correlation"],
                "churners_attributed": churners_attributed,
                "revenue_impact_annual": revenue_impact,
                "avg_sentiment_score": template["avg_sentiment"],
                "keywords": template["keywords"],
                "is_fixable": template["fixable"],
                "fix_complexity": template["fix_complexity"],
                "identified_date": (base_date + timedelta(days=i*3)).isoformat(),
                "example_complaints": self._generate_example_complaints(template),
                "recommended_actions": self._generate_recommendations(template),
                "estimated_fix_timeline": self._estimate_fix_timeline(template["fix_complexity"]),
                "potential_retention_uplift": round(template["churn_correlation"] * 0.6, 2)  # 60% of churn can be prevented
            }
            
            themes.append(theme)
        
        return themes
    
    def _generate_example_complaints(self, template: Dict[str, Any]) -> List[str]:
        """Generate example complaint texts."""
        examples_map = {
            "Buffering/Streaming Quality": [
                "Video keeps buffering every few minutes, completely unwatchable",
                "Why am I paying for this when it can't even stream in HD without freezing?",
                "Constant loading issues, especially during prime time"
            ],
            "Content Library Gaps": [
                "You removed my favorite show with no warning, canceling subscription",
                "Selection is terrible compared to other streaming services",
                "Where are the new releases? Library feels outdated"
            ],
            "App Crashes/Technical Issues": [
                "App crashes every time I try to watch on my iPad",
                "Can't even log in half the time, error messages everywhere",
                "Latest update broke everything, worked fine before"
            ],
            "Price/Value Concerns": [
                "Not worth $9.99/month for this limited content",
                "Other services offer more for less money",
                "Just raised prices again? I'm out"
            ]
        }
        
        return examples_map.get(template["name"], [
            "Issue with service quality",
            "Not meeting expectations",
            "Considering cancellation"
        ])
    
    def _generate_recommendations(self, template: Dict[str, Any]) -> List[str]:
        """Generate recommended actions."""
        if not template["fixable"]:
            return ["Monitor sentiment", "Gather more feedback"]
        
        recommendations_map = {
            "Buffering/Streaming Quality": [
                "Emergency CDN infrastructure upgrade",
                "Implement adaptive bitrate optimization",
                "Regional load balancing improvements"
            ],
            "Content Library Gaps": [
                "Accelerate content licensing negotiations",
                "Increase original content production budget",
                "Improve content discovery algorithms"
            ],
            "App Crashes/Technical Issues": [
                "Emergency tech sprint on stability",
                "Comprehensive device testing before releases",
                "Rollback problematic updates"
            ],
            "Price/Value Concerns": [
                "Introduce ad-supported tier at lower price",
                "Bundle with other Paramount services",
                "Loyalty program for long-term subscribers"
            ]
        }
        
        return recommendations_map.get(template["name"], [
            "Investigate root cause",
            "Develop action plan",
            "Monitor impact of changes"
        ])
    
    def _estimate_fix_timeline(self, complexity: str) -> str:
        """Estimate fix timeline based on complexity."""
        timelines = {
            "low": "2-4 weeks",
            "medium": "1-3 months",
            "high": "3-6 months"
        }
        return timelines.get(complexity, "Unknown")
    
    def generate_individual_complaints(self, themes: List[Dict[str, Any]], count: int = 100) -> List[Dict[str, Any]]:
        """
        Generate individual complaint tickets mapped to themes.
        
        Args:
            themes: List of themes from generate_themes()
            count: Number of individual complaints to generate
        
        Returns:
            List of complaint ticket dictionaries
        """
        complaints = []
        base_date = datetime.now() - timedelta(days=30)
        
        # Weight complaints by theme volume
        theme_weights = [theme["complaint_volume"] for theme in themes]
        total_weight = sum(theme_weights)
        theme_probabilities = [w / total_weight for w in theme_weights]
        
        for i in range(count):
            # Select theme based on Pareto distribution
            theme = random.choices(themes, weights=theme_probabilities)[0]
            
            complaint = {
                "complaint_id": f"TICKET-{i+1:05d}",
                "theme_id": theme["theme_id"],
                "theme_name": theme["name"],
                "submitted_date": (base_date + timedelta(hours=random.randint(0, 720))).isoformat(),
                "text": random.choice(theme["example_complaints"]),
                "sentiment_score": theme["avg_sentiment_score"] + random.uniform(-0.1, 0.1),
                "customer_tier": random.choice(["free_trial", "basic", "premium"]),
                "churned": random.random() < theme["churn_correlation"],
                "resolved": random.choice([True, False]),
                "resolution_time_hours": random.randint(1, 72) if random.choice([True, False]) else None
            }
            
            complaints.append(complaint)
        
        return complaints
    
    def get_pareto_summary(self, themes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Pareto distribution summary for complaint themes.
        
        Args:
            themes: List of generated themes
        
        Returns:
            Pareto analysis summary
        """
        total_complaints = sum(theme["complaint_volume"] for theme in themes)
        total_churners = sum(theme["churners_attributed"] for theme in themes)
        total_revenue_impact = sum(theme["revenue_impact_annual"] for theme in themes)
        
        # Sort by churners attributed
        sorted_themes = sorted(themes, key=lambda x: x["churners_attributed"], reverse=True)
        
        # Calculate top 20%
        top_20_count = max(1, len(themes) // 5)
        top_20_churners = sum(theme["churners_attributed"] for theme in sorted_themes[:top_20_count])
        top_20_contribution = top_20_churners / total_churners if total_churners > 0 else 0
        
        return {
            "total_themes": len(themes),
            "total_complaints": total_complaints,
            "total_churners_attributed": total_churners,
            "total_revenue_impact_annual": total_revenue_impact,
            "top_20_percent_count": top_20_count,
            "top_20_percent_contribution": round(top_20_contribution, 2),
            "top_themes": [
                {
                    "theme_id": theme["theme_id"],
                    "name": theme["name"],
                    "churners_attributed": theme["churners_attributed"],
                    "revenue_impact": theme["revenue_impact_annual"]
                }
                for theme in sorted_themes[:top_20_count]
            ],
            "pareto_validated": 0.70 <= top_20_contribution <= 0.80  # Slightly lower for complaints
        }
