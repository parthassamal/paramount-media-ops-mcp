"""
Mock data generator for churn cohorts.

Generates realistic at-risk subscriber cohorts with Pareto distribution.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from config import settings


class ChurnCohortGenerator:
    """Generator for at-risk subscriber cohorts with Pareto characteristics."""
    
    def __init__(self, seed: int = None):
        """
        Initialize generator with optional seed for reproducibility.
        
        Args:
            seed: Random seed for reproducible data generation
        """
        self.seed = seed or settings.random_seed
        random.seed(self.seed)
    
    def generate(self, num_cohorts: int = 5) -> List[Dict[str, Any]]:
        """
        Generate at-risk subscriber cohorts.
        
        The data follows Pareto distribution where top 20% of cohorts
        drive 80% of churn risk.
        
        Args:
            num_cohorts: Number of cohorts to generate (default: 5)
        
        Returns:
            List of cohort dictionaries with churn signals
        """
        cohorts = []
        
        # Define cohort templates with Pareto-distributed risk
        # Top 20% (cohort 1) should drive ~80% of impact
        cohort_templates = [
            {
                "name": "High-Value Serial Churners",
                "size": 45000,
                "churn_risk_score": 0.98,  # Even higher
                "avg_ltv": 1400,  # Increased further
                "complaint_rate": 0.34,
                "content_engagement_drop": 0.58,
                "primary_driver": "Content library gaps in key genres"
            },
            {
                "name": "Price-Sensitive Millennials",
                "size": 52000,
                "churn_risk_score": 0.65,  # Reduced
                "avg_ltv": 280,  # Reduced
                "complaint_rate": 0.28,
                "content_engagement_drop": 0.45,
                "primary_driver": "Competitive pricing pressure"
            },
            {
                "name": "Tech-Frustrated Early Adopters",
                "size": 28000,
                "churn_risk_score": 0.55,  # Reduced
                "avg_ltv": 350,  # Reduced
                "complaint_rate": 0.52,
                "content_engagement_drop": 0.31,
                "primary_driver": "App performance and buffering issues"
            },
            {
                "name": "Seasonal Sports Viewers",
                "size": 38000,
                "churn_risk_score": 0.35,  # Reduced
                "avg_ltv": 180,  # Reduced
                "complaint_rate": 0.15,
                "content_engagement_drop": 0.67,
                "primary_driver": "Single-sport dependency (NFL/Soccer)"
            },
            {
                "name": "Post-Free-Trial Drop-offs",
                "size": 71000,
                "churn_risk_score": 0.25,  # Reduced
                "avg_ltv": 80,  # Reduced
                "complaint_rate": 0.09,
                "content_engagement_drop": 0.22,
                "primary_driver": "Never activated beyond trial"
            }
        ]
        
        base_date = datetime.now() - timedelta(days=30)
        
        for i, template in enumerate(cohort_templates[:num_cohorts], 1):
            # Calculate financial impact (LTV * size * churn_risk)
            projected_churn = int(template["size"] * template["churn_risk_score"])
            financial_impact = projected_churn * template["avg_ltv"]
            
            cohort = {
                "cohort_id": f"COHORT-{i:03d}",
                "name": template["name"],
                "size": template["size"],
                "churn_risk_score": template["churn_risk_score"],
                "projected_churners_30d": projected_churn,
                "avg_lifetime_value": template["avg_ltv"],
                "financial_impact_30d": financial_impact,
                "complaint_rate": template["complaint_rate"],
                "content_engagement_drop_pct": template["content_engagement_drop"],
                "primary_driver": template["primary_driver"],
                "identified_date": (base_date + timedelta(days=i*2)).isoformat(),
                "demographic": self._generate_demographics(),
                "retention_interventions": self._generate_interventions(template["primary_driver"]),
                "predicted_retention_uplift": round(random.uniform(0.15, 0.35), 2)
            }
            
            cohorts.append(cohort)
        
        return cohorts
    
    def _generate_demographics(self) -> Dict[str, Any]:
        """Generate demographic profile for cohort."""
        age_groups = ["18-24", "25-34", "35-44", "45-54", "55+"]
        regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
        
        return {
            "primary_age_group": random.choice(age_groups),
            "primary_region": random.choice(regions),
            "device_mix": {
                "smart_tv": round(random.uniform(0.25, 0.45), 2),
                "mobile": round(random.uniform(0.20, 0.35), 2),
                "web": round(random.uniform(0.10, 0.20), 2),
                "streaming_device": round(random.uniform(0.15, 0.30), 2)
            }
        }
    
    def _generate_interventions(self, primary_driver: str) -> List[str]:
        """Generate targeted retention interventions."""
        intervention_map = {
            "Content library": [
                "License key missing franchises",
                "Accelerate original content in weak genres",
                "Create personalized content recommendations"
            ],
            "Competitive pricing": [
                "Introduce tiered pricing with ads",
                "Launch loyalty discount program",
                "Bundle with partner services"
            ],
            "App performance": [
                "Emergency tech sprint on buffering",
                "Upgrade CDN infrastructure",
                "Launch beta testing program for complainers"
            ],
            "Single-sport": [
                "Cross-promote complementary sports content",
                "Create off-season engagement campaigns",
                "Offer multi-sport packages"
            ],
            "Never activated": [
                "Improve onboarding experience",
                "Personalized welcome emails with recommendations",
                "Early engagement incentives"
            ]
        }
        
        for key in intervention_map:
            if key in primary_driver:
                return intervention_map[key]
        
        return ["General retention campaign", "Engagement survey", "Win-back offer"]
    
    def get_pareto_summary(self, cohorts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Pareto distribution summary for cohorts.
        
        Args:
            cohorts: List of generated cohorts
        
        Returns:
            Pareto analysis summary
        """
        total_impact = sum(c["financial_impact_30d"] for c in cohorts)
        total_churners = sum(c["projected_churners_30d"] for c in cohorts)
        
        # Sort by financial impact
        sorted_cohorts = sorted(cohorts, key=lambda x: x["financial_impact_30d"], reverse=True)
        
        # Calculate top 20%
        top_20_count = max(1, len(cohorts) // 5)
        top_20_impact = sum(c["financial_impact_30d"] for c in sorted_cohorts[:top_20_count])
        top_20_contribution = top_20_impact / total_impact if total_impact > 0 else 0
        
        return {
            "total_cohorts": len(cohorts),
            "total_at_risk_subscribers": total_churners,
            "total_financial_impact_30d": total_impact,
            "top_20_percent_count": top_20_count,
            "top_20_percent_contribution": round(top_20_contribution, 2),
            "top_cohorts": [
                {
                    "cohort_id": c["cohort_id"],
                    "name": c["name"],
                    "financial_impact": c["financial_impact_30d"]
                }
                for c in sorted_cohorts[:top_20_count]
            ],
            "pareto_validated": 0.75 <= top_20_contribution <= 0.85
        }
