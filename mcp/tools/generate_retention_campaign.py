"""
Generate Retention Campaign Tool.

Creates targeted retention campaigns from analysis.
"""

from typing import Dict, Any, List, Optional
from mcp.resources import (
    ChurnSignalsResource,
    ComplaintsTopicsResource,
    RetentionCampaignsResource
)


class GenerateRetentionCampaignTool:
    """
    Tool to generate targeted retention campaigns.
    
    Uses churn analysis and complaint data to create personalized campaigns.
    """
    
    def __init__(self):
        """Initialize the tool."""
        self.churn_resource = ChurnSignalsResource()
        self.complaints_resource = ComplaintsTopicsResource()
        self.campaigns_resource = RetentionCampaignsResource()
    
    def execute(
        self,
        cohort_id: str,
        budget: Optional[float] = None,
        timeline_days: int = 45
    ) -> Dict[str, Any]:
        """
        Generate retention campaign for a specific cohort.
        
        Args:
            cohort_id: Target cohort ID
            budget: Campaign budget (None = auto-calculate)
            timeline_days: Campaign duration in days (default: 45)
        
        Returns:
            Complete campaign plan with tactics and projections
            
        Example:
            >>> tool = GenerateRetentionCampaignTool()
            >>> campaign = tool.execute(cohort_id="COHORT-001", budget=500000)
            >>> print(campaign["campaign_name"])
            "High-Value Churner Win-Back Campaign"
        """
        # Get cohort details
        cohort_data = self.churn_resource.get_cohort_details(cohort_id)
        if not cohort_data:
            return {"error": f"Cohort {cohort_id} not found"}
        
        cohort = cohort_data["cohort"]
        
        # Get related complaint themes
        primary_driver = cohort["primary_driver"]
        related_complaints = self._find_related_complaints(primary_driver)
        
        # Get historical campaign performance for similar cohorts
        historical_campaigns = self.campaigns_resource.query()
        
        # Generate campaign strategy
        campaign_strategy = self._generate_strategy(
            cohort,
            related_complaints,
            historical_campaigns
        )
        
        # Calculate budget if not provided
        if budget is None:
            budget = self._calculate_recommended_budget(cohort)
        
        # Build campaign plan
        campaign_plan = self._build_campaign_plan(
            cohort,
            campaign_strategy,
            budget,
            timeline_days
        )
        
        # Project outcomes
        projections = self._project_outcomes(
            cohort,
            campaign_plan,
            historical_campaigns
        )
        
        return {
            "campaign_name": f"{cohort['name']} Retention Campaign",
            "target_cohort": {
                "cohort_id": cohort_id,
                "name": cohort["name"],
                "size": cohort["size"],
                "at_risk": cohort["projected_churners_30d"],
                "primary_driver": primary_driver
            },
            "campaign_plan": campaign_plan,
            "projected_outcomes": projections,
            "budget": budget,
            "timeline_days": timeline_days,
            "implementation_guide": self._generate_implementation_guide(campaign_plan)
        }
    
    def _find_related_complaints(self, primary_driver: str) -> List[Dict[str, Any]]:
        """Find complaint themes related to churn driver."""
        complaint_data = self.complaints_resource.query()
        themes = complaint_data["themes"]
        
        # Simple keyword matching (in production, use NLP)
        related = []
        driver_keywords = primary_driver.lower().split()
        
        for theme in themes:
            theme_text = theme["name"].lower()
            if any(kw in theme_text for kw in driver_keywords):
                related.append({
                    "theme_name": theme["name"],
                    "churn_correlation": theme["churn_correlation"],
                    "recommended_actions": theme["recommended_actions"]
                })
        
        return related[:3]
    
    def _generate_strategy(
        self,
        cohort: Dict[str, Any],
        complaints: List[Dict[str, Any]],
        historical_campaigns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate campaign strategy based on analysis."""
        primary_driver = cohort["primary_driver"]
        
        # Define strategy based on driver
        strategy_map = {
            "Content library": {
                "focus": "Content discovery and new additions",
                "key_message": "Discover new content you'll love",
                "channels": ["email", "in_app", "push_notifications"],
                "tactics": [
                    "Personalized content recommendations",
                    "Early access to new releases",
                    "Genre-specific curated playlists"
                ]
            },
            "Competitive pricing": {
                "focus": "Value demonstration and special offers",
                "key_message": "More value, exclusive benefits",
                "channels": ["email", "sms", "in_app"],
                "tactics": [
                    "Limited-time discount offer",
                    "Loyalty rewards program",
                    "Bundle with other services"
                ]
            },
            "App performance": {
                "focus": "Service improvement and compensation",
                "key_message": "We've fixed the issues you reported",
                "channels": ["email", "in_app", "direct_outreach"],
                "tactics": [
                    "App update announcement",
                    "Free month as apology",
                    "Priority technical support"
                ]
            }
        }
        
        # Select appropriate strategy
        for key, strategy in strategy_map.items():
            if key.lower() in primary_driver.lower():
                return strategy
        
        # Default strategy
        return {
            "focus": "General retention and value",
            "key_message": "We value your subscription",
            "channels": ["email", "in_app"],
            "tactics": [
                "Personalized offers",
                "Survey for feedback",
                "Engagement incentives"
            ]
        }
    
    def _calculate_recommended_budget(self, cohort: Dict[str, Any]) -> float:
        """Calculate recommended budget based on cohort value."""
        # Budget as percentage of potential loss
        potential_loss = cohort["financial_impact_30d"]
        recommended_budget = potential_loss * 0.15  # 15% of at-risk revenue
        
        # Cap and floor the budget
        return max(100000, min(recommended_budget, 1000000))  # $100K - $1M
    
    def _build_campaign_plan(
        self,
        cohort: Dict[str, Any],
        strategy: Dict[str, Any],
        budget: float,
        timeline_days: int
    ) -> Dict[str, Any]:
        """Build detailed campaign plan."""
        # Allocate budget across channels
        channel_allocation = self._allocate_budget(strategy["channels"], budget)
        
        # Build timeline
        campaign_timeline = self._build_timeline(timeline_days, strategy["tactics"])
        
        return {
            "strategy": strategy,
            "budget_allocation": channel_allocation,
            "timeline": campaign_timeline,
            "target_metrics": {
                "reach": cohort["projected_churners_30d"],
                "target_conversion_rate": cohort["predicted_retention_uplift"],
                "target_conversions": int(cohort["projected_churners_30d"] * cohort["predicted_retention_uplift"])
            },
            "creative_requirements": self._define_creative_requirements(strategy),
            "measurement_plan": {
                "kpis": ["Conversion rate", "Engagement rate", "Revenue retained"],
                "tracking": "Daily dashboard monitoring",
                "milestones": [
                    {"day": 7, "check": "10% of target reached"},
                    {"day": 21, "check": "50% of target reached"},
                    {"day": 45, "check": "Campaign complete"}
                ]
            }
        }
    
    def _allocate_budget(self, channels: List[str], total_budget: float) -> Dict[str, float]:
        """Allocate budget across channels."""
        allocation = {}
        
        # Define channel costs and priorities
        channel_weights = {
            "email": 0.2,
            "in_app": 0.3,
            "push_notifications": 0.15,
            "sms": 0.15,
            "direct_outreach": 0.2
        }
        
        total_weight = sum(channel_weights.get(ch, 0.2) for ch in channels)
        
        for channel in channels:
            weight = channel_weights.get(channel, 0.2)
            allocation[channel] = round(total_budget * (weight / total_weight), 2)
        
        return allocation
    
    def _build_timeline(self, duration_days: int, tactics: List[str]) -> List[Dict[str, Any]]:
        """Build campaign timeline."""
        timeline = []
        
        # Week 1: Setup and launch
        timeline.append({
            "phase": "Setup & Launch",
            "days": "1-7",
            "activities": [
                "Finalize creative assets",
                "Set up tracking and monitoring",
                "Launch initial wave: email + in-app"
            ]
        })
        
        # Week 2-4: Active engagement
        timeline.append({
            "phase": "Active Engagement",
            "days": "8-28",
            "activities": [
                "Deploy all tactics across channels",
                "Monitor engagement and adjust",
                "A/B test messaging variations"
            ]
        })
        
        # Week 5-6: Follow-up and close
        timeline.append({
            "phase": "Follow-up & Close",
            "days": f"29-{duration_days}",
            "activities": [
                "Final reminder to non-converters",
                "Exclusive last-chance offers",
                "Gather feedback from participants"
            ]
        })
        
        return timeline
    
    def _define_creative_requirements(self, strategy: Dict[str, Any]) -> Dict[str, List[str]]:
        """Define creative assets needed."""
        return {
            "email": [
                "Subject line variants (5x)",
                "Email body templates (3x)",
                "CTA buttons and landing pages"
            ],
            "in_app": [
                "Banner designs (3x sizes)",
                "Modal popups (2x variants)",
                "Home screen placements"
            ],
            "social": [
                "Social media graphics (3x platforms)",
                "Video snippets (30s, 60s)",
                "Story templates"
            ]
        }
    
    def _project_outcomes(
        self,
        cohort: Dict[str, Any],
        campaign_plan: Dict[str, Any],
        historical_campaigns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Project campaign outcomes."""
        target_reach = campaign_plan["target_metrics"]["reach"]
        target_conversion_rate = campaign_plan["target_metrics"]["target_conversion_rate"]
        
        # Conservative, moderate, aggressive scenarios
        scenarios = {
            "conservative": target_conversion_rate * 0.7,
            "moderate": target_conversion_rate,
            "aggressive": target_conversion_rate * 1.3
        }
        
        projections = {}
        for scenario_name, conversion_rate in scenarios.items():
            conversions = int(target_reach * conversion_rate)
            revenue_retained = conversions * cohort["avg_lifetime_value"]
            
            projections[scenario_name] = {
                "conversion_rate": round(conversion_rate, 2),
                "conversions": conversions,
                "revenue_retained_annual": revenue_retained,
                "roi": round(revenue_retained / campaign_plan["budget_allocation"].get("total", sum(campaign_plan["budget_allocation"].values())), 2)
            }
        
        return {
            "scenarios": projections,
            "recommended_scenario": "moderate",
            "confidence_level": "moderate" if cohort["churn_risk_score"] > 0.7 else "high"
        }
    
    def _generate_implementation_guide(self, campaign_plan: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate step-by-step implementation guide."""
        return [
            {
                "step": 1,
                "title": "Prepare Creative Assets",
                "description": "Develop all required creative assets per specifications",
                "owner": "Creative Team",
                "timeline": "Days 1-5"
            },
            {
                "step": 2,
                "title": "Set Up Tracking",
                "description": "Configure analytics, attribution, and monitoring dashboards",
                "owner": "Analytics Team",
                "timeline": "Days 1-7"
            },
            {
                "step": 3,
                "title": "Launch Campaign",
                "description": "Deploy initial wave across all channels",
                "owner": "Campaign Manager",
                "timeline": "Day 7"
            },
            {
                "step": 4,
                "title": "Monitor & Optimize",
                "description": "Daily monitoring, weekly optimization based on performance",
                "owner": "Campaign Manager",
                "timeline": "Days 8-45"
            },
            {
                "step": 5,
                "title": "Report Results",
                "description": "Compile final results and learnings for future campaigns",
                "owner": "Analytics Team",
                "timeline": "Day 50"
            }
        ]


def create_tool() -> GenerateRetentionCampaignTool:
    """Factory function to create the tool."""
    return GenerateRetentionCampaignTool()
