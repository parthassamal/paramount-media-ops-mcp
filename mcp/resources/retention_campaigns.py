"""
Retention Campaigns Resource.

Provides campaign tracking and effectiveness metrics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
from config import settings


class RetentionCampaignsResource:
    """Resource for retention campaign tracking and analysis."""
    
    def __init__(self):
        """Initialize retention campaigns resource."""
        random.seed(settings.random_seed)
    
    def query(
        self,
        campaign_status: Optional[str] = None,
        min_effectiveness: float = 0.0
    ) -> Dict[str, Any]:
        """
        Query retention campaigns and their effectiveness.
        
        Args:
            campaign_status: Filter by status ("active", "completed", "planned")
            min_effectiveness: Minimum effectiveness score to include
        
        Returns:
            Dictionary with campaigns and analysis
        """
        # Generate campaigns (in production, this would query a campaign database)
        campaigns = self._generate_campaigns()
        
        # Apply filters
        if campaign_status:
            campaigns = [c for c in campaigns if c["status"] == campaign_status]
        
        campaigns = [c for c in campaigns if c["effectiveness_score"] >= min_effectiveness]
        
        # Calculate summary metrics
        summary = self._calculate_summary(campaigns)
        
        # Identify best practices
        best_practices = self._identify_best_practices(campaigns)
        
        return {
            "campaigns": campaigns,
            "summary": summary,
            "best_practices": best_practices,
            "query_params": {
                "campaign_status": campaign_status,
                "min_effectiveness": min_effectiveness
            }
        }
    
    def _generate_campaigns(self) -> List[Dict[str, Any]]:
        """Generate mock retention campaigns."""
        campaign_templates = [
            {
                "name": "High-Value Churner Win-Back",
                "target_cohort": "COHORT-001",
                "status": "active",
                "start_date": datetime.now() - timedelta(days=15),
                "tactics": ["Personalized content recommendations", "2-month discount offer", "Priority support"],
                "budget": 500000,
                "reach": 35000,
                "converted": 14000,
                "retention_uplift": 0.40,
                "effectiveness_score": 0.85
            },
            {
                "name": "Tech Issue Resolution Campaign",
                "target_cohort": "COHORT-003",
                "status": "completed",
                "start_date": datetime.now() - timedelta(days=45),
                "end_date": datetime.now() - timedelta(days=10),
                "tactics": ["App update notification", "Tech support outreach", "Beta access"],
                "budget": 200000,
                "reach": 28000,
                "converted": 17000,
                "retention_uplift": 0.61,
                "effectiveness_score": 0.92
            },
            {
                "name": "Content Library Expansion Awareness",
                "target_cohort": "COHORT-002",
                "status": "active",
                "start_date": datetime.now() - timedelta(days=20),
                "tactics": ["New content email series", "In-app notifications", "Social media campaign"],
                "budget": 350000,
                "reach": 52000,
                "converted": 18000,
                "retention_uplift": 0.35,
                "effectiveness_score": 0.68
            },
            {
                "name": "Sports Viewer Off-Season Engagement",
                "target_cohort": "COHORT-004",
                "status": "planned",
                "start_date": datetime.now() + timedelta(days=30),
                "tactics": ["Cross-sport recommendations", "Exclusive content", "Loyalty points"],
                "budget": 150000,
                "reach": 38000,
                "converted": None,  # Not started yet
                "retention_uplift": None,
                "effectiveness_score": 0.0  # Projected
            },
            {
                "name": "Trial Conversion Optimization",
                "target_cohort": "COHORT-005",
                "status": "active",
                "start_date": datetime.now() - timedelta(days=10),
                "tactics": ["Onboarding improvements", "Welcome discount", "Content discovery help"],
                "budget": 300000,
                "reach": 71000,
                "converted": 21000,
                "retention_uplift": 0.30,
                "effectiveness_score": 0.72
            }
        ]
        
        campaigns = []
        for i, template in enumerate(campaign_templates, 1):
            campaign = {
                "campaign_id": f"CAMP-{i:03d}",
                **template,
                "start_date": template["start_date"].isoformat() if isinstance(template["start_date"], datetime) else template["start_date"],
                "end_date": template.get("end_date").isoformat() if template.get("end_date") and isinstance(template.get("end_date"), datetime) else template.get("end_date")
            }
            
            # Calculate metrics for active/completed campaigns
            if campaign["status"] in ["active", "completed"] and campaign["converted"]:
                campaign["conversion_rate"] = round(campaign["converted"] / campaign["reach"], 2)
                campaign["cost_per_conversion"] = round(campaign["budget"] / campaign["converted"], 2)
                campaign["roi"] = round((campaign["converted"] * 9.99 * 12) / campaign["budget"], 2)
                campaign["subscribers_retained"] = campaign["converted"]
                campaign["revenue_impact_annual"] = campaign["converted"] * 9.99 * 12
            
            campaigns.append(campaign)
        
        return campaigns
    
    def _calculate_summary(self, campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary metrics across campaigns."""
        active_campaigns = [c for c in campaigns if c["status"] in ["active", "completed"]]
        
        if not active_campaigns:
            return {"message": "No active or completed campaigns found"}
        
        total_budget = sum(c["budget"] for c in active_campaigns)
        total_reach = sum(c["reach"] for c in active_campaigns)
        total_converted = sum(c.get("converted", 0) or 0 for c in active_campaigns)
        
        avg_effectiveness = sum(c["effectiveness_score"] for c in active_campaigns) / len(active_campaigns)
        
        return {
            "total_campaigns": len(campaigns),
            "active_campaigns": len([c for c in campaigns if c["status"] == "active"]),
            "completed_campaigns": len([c for c in campaigns if c["status"] == "completed"]),
            "total_budget": total_budget,
            "total_reach": total_reach,
            "total_subscribers_retained": total_converted,
            "overall_conversion_rate": round(total_converted / total_reach, 2) if total_reach > 0 else 0,
            "avg_effectiveness_score": round(avg_effectiveness, 2),
            "total_annual_revenue_impact": sum(c.get("revenue_impact_annual", 0) for c in active_campaigns)
        }
    
    def _identify_best_practices(self, campaigns: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Identify best practices from successful campaigns."""
        successful_campaigns = [
            c for c in campaigns
            if c["status"] in ["active", "completed"] and c["effectiveness_score"] >= 0.75
        ]
        
        if not successful_campaigns:
            return []
        
        # Analyze tactics
        tactic_usage = {}
        for campaign in successful_campaigns:
            for tactic in campaign["tactics"]:
                if tactic not in tactic_usage:
                    tactic_usage[tactic] = {
                        "count": 0,
                        "avg_effectiveness": []
                    }
                tactic_usage[tactic]["count"] += 1
                tactic_usage[tactic]["avg_effectiveness"].append(campaign["effectiveness_score"])
        
        # Calculate average effectiveness per tactic
        best_tactics = []
        for tactic, data in tactic_usage.items():
            avg_eff = sum(data["avg_effectiveness"]) / len(data["avg_effectiveness"])
            best_tactics.append({
                "tactic": tactic,
                "usage_count": data["count"],
                "avg_effectiveness": round(avg_eff, 2),
                "recommendation": f"Use in future campaigns - proven effective"
            })
        
        # Sort by effectiveness
        best_tactics_sorted = sorted(best_tactics, key=lambda x: x["avg_effectiveness"], reverse=True)
        
        return best_tactics_sorted
    
    def get_campaign_details(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific campaign.
        
        Args:
            campaign_id: Campaign identifier (e.g., "CAMP-001")
        
        Returns:
            Campaign details or None if not found
        """
        campaigns = self._generate_campaigns()
        for campaign in campaigns:
            if campaign["campaign_id"] == campaign_id:
                return campaign
        return None
    
    def get_campaign_recommendations(self, cohort_id: str) -> Dict[str, Any]:
        """
        Generate campaign recommendations for a specific cohort.
        
        Args:
            cohort_id: Target cohort identifier
        
        Returns:
            Campaign recommendations
        """
        # In production, this would use ML models trained on historical campaign performance
        recommendations = {
            "cohort_id": cohort_id,
            "recommended_tactics": [
                "Personalized content recommendations based on viewing history",
                "Limited-time discount offer (2-3 months)",
                "Priority customer support access",
                "Exclusive early access to new content"
            ],
            "estimated_budget": 400000,
            "projected_reach": 35000,
            "projected_conversion_rate": 0.38,
            "projected_roi": 2.5,
            "timeline": "30-45 days",
            "success_factors": [
                "Launch within 7 days to capture at-risk window",
                "Personalize messaging by primary churn driver",
                "Multi-channel approach (email + in-app + social)",
                "Monitor and adjust tactics weekly"
            ]
        }
        
        return recommendations


def create_resource() -> RetentionCampaignsResource:
    """Factory function to create retention campaigns resource."""
    return RetentionCampaignsResource()
