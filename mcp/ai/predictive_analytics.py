"""
Predictive Analytics Engine.

ML-powered predictions for churn, revenue, and production risk.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import structlog

logger = structlog.get_logger()


class PredictiveAnalytics:
    """
    Predictive analytics for streaming operations.
    
    Features:
    - User churn prediction
    - Revenue forecasting
    - Incident duration prediction
    - Optimal action recommendations
    """
    
    def __init__(self):
        """Initialize predictive analytics engine."""
        self.models_loaded = False
        
    def predict_user_churn(
        self,
        user_features: Dict[str, Any],
        horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Predict churn probability for a user.
        
        Args:
            user_features: User behavioral and demographic features
            horizon_days: Prediction horizon in days
            
        Returns:
            Churn prediction with confidence and contributing factors
        """
        # Extract features
        engagement_score = user_features.get("engagement_score", 0.5)
        content_diversity = user_features.get("content_diversity_score", 0.5)
        subscription_tenure_days = user_features.get("subscription_tenure_days", 180)
        payment_issues = user_features.get("payment_issues", 0)
        support_tickets = user_features.get("support_tickets", 0)
        last_login_days_ago = user_features.get("last_login_days_ago", 7)
        
        # Simple rule-based model (can be replaced with trained ML model)
        churn_score = 0.0
        contributing_factors = []
        
        # Factor 1: Low engagement
        if engagement_score < 0.3:
            churn_score += 0.25
            contributing_factors.append({
                "factor": "low_engagement",
                "impact": 0.25,
                "description": "User engagement is significantly below average"
            })
        elif engagement_score < 0.5:
            churn_score += 0.10
            contributing_factors.append({
                "factor": "moderate_engagement",
                "impact": 0.10,
                "description": "User engagement is below average"
            })
        
        # Factor 2: Low content diversity
        if content_diversity < 0.3:
            churn_score += 0.20
            contributing_factors.append({
                "factor": "low_content_diversity",
                "impact": 0.20,
                "description": "User watches limited content variety"
            })
        
        # Factor 3: Recent subscriber (higher churn risk)
        if subscription_tenure_days < 90:
            churn_score += 0.15
            contributing_factors.append({
                "factor": "new_subscriber",
                "impact": 0.15,
                "description": "Recent subscribers have higher churn risk"
            })
        
        # Factor 4: Payment issues
        if payment_issues > 0:
            churn_score += 0.30
            contributing_factors.append({
                "factor": "payment_issues",
                "impact": 0.30,
                "description": f"{payment_issues} payment issue(s) detected"
            })
        
        # Factor 5: Support tickets (dissatisfaction indicator)
        if support_tickets > 2:
            churn_score += 0.20
            contributing_factors.append({
                "factor": "high_support_tickets",
                "impact": 0.20,
                "description": f"{support_tickets} support tickets indicate dissatisfaction"
            })
        
        # Factor 6: Inactivity
        if last_login_days_ago > 14:
            churn_score += 0.25
            contributing_factors.append({
                "factor": "inactivity",
                "impact": 0.25,
                "description": f"No login for {last_login_days_ago} days"
            })
        
        # Cap at 1.0
        churn_score = min(churn_score, 1.0)
        
        # Calculate confidence based on feature completeness
        feature_completeness = sum(1 for v in user_features.values() if v is not None) / len(user_features)
        confidence = 0.6 + (0.3 * feature_completeness)
        
        # Risk category
        if churn_score >= 0.7:
            risk_category = "critical"
        elif churn_score >= 0.5:
            risk_category = "high"
        elif churn_score >= 0.3:
            risk_category = "medium"
        else:
            risk_category = "low"
        
        prediction = {
            "user_id": user_features.get("user_id", "unknown"),
            "churn_probability": round(churn_score, 3),
            "risk_category": risk_category,
            "confidence": round(confidence, 3),
            "prediction_horizon_days": horizon_days,
            "contributing_factors": sorted(
                contributing_factors,
                key=lambda x: x["impact"],
                reverse=True
            ),
            "recommended_interventions": self._recommend_interventions(contributing_factors),
            "predicted_at": datetime.now().isoformat()
        }
        
        logger.debug(
            "Churn prediction generated",
            user_id=prediction["user_id"],
            churn_probability=prediction["churn_probability"],
            risk_category=risk_category
        )
        
        return prediction
    
    def predict_revenue_impact(
        self,
        scenario: Dict[str, Any],
        forecast_months: int = 12
    ) -> Dict[str, Any]:
        """
        Predict revenue impact of a scenario.
        
        Args:
            scenario: Scenario parameters (churn rate, growth rate, etc.)
            forecast_months: Number of months to forecast
            
        Returns:
            Revenue forecast with confidence intervals
        """
        # Base metrics
        current_subscribers = scenario.get("current_subscribers", 8_000_000)
        current_arpu = scenario.get("arpu", 8.99)
        base_churn_rate = scenario.get("churn_rate", 0.05)
        base_growth_rate = scenario.get("growth_rate", 0.12)
        
        # Scenario adjustments
        churn_reduction = scenario.get("churn_reduction", 0.0)
        growth_acceleration = scenario.get("growth_acceleration", 0.0)
        
        adjusted_churn = base_churn_rate * (1 - churn_reduction)
        adjusted_growth = base_growth_rate * (1 + growth_acceleration)
        
        # Monthly forecast
        forecasts = []
        subscribers = current_subscribers
        
        for month in range(1, forecast_months + 1):
            # Calculate monthly changes
            new_subs = int(subscribers * adjusted_growth / 12)
            churned_subs = int(subscribers * adjusted_churn / 12)
            
            subscribers = subscribers + new_subs - churned_subs
            monthly_revenue = subscribers * current_arpu
            
            forecasts.append({
                "month": month,
                "subscribers": subscribers,
                "new_subscribers": new_subs,
                "churned_subscribers": churned_subs,
                "net_growth": new_subs - churned_subs,
                "monthly_revenue": round(monthly_revenue, 2),
                "cumulative_revenue": round(sum(f.get("monthly_revenue", 0) for f in forecasts) + monthly_revenue, 2)
            })
        
        # Calculate confidence intervals (simple ±10%)
        final_revenue = forecasts[-1]["cumulative_revenue"]
        
        forecast_result = {
            "scenario_name": scenario.get("name", "Unnamed scenario"),
            "forecast_months": forecast_months,
            "baseline": {
                "current_subscribers": current_subscribers,
                "churn_rate": base_churn_rate,
                "growth_rate": base_growth_rate
            },
            "scenario_adjustments": {
                "churn_reduction": churn_reduction,
                "growth_acceleration": growth_acceleration,
                "adjusted_churn_rate": adjusted_churn,
                "adjusted_growth_rate": adjusted_growth
            },
            "forecast": {
                "final_subscribers": forecasts[-1]["subscribers"],
                "total_revenue": final_revenue,
                "revenue_lower_bound": final_revenue * 0.9,
                "revenue_upper_bound": final_revenue * 1.1,
                "confidence_level": 0.80
            },
            "monthly_forecasts": forecasts,
            "predicted_at": datetime.now().isoformat()
        }
        
        logger.info(
            "Revenue forecast generated",
            scenario=scenario.get("name"),
            final_subscribers=forecasts[-1]["subscribers"],
            total_revenue=final_revenue
        )
        
        return forecast_result
    
    def predict_incident_duration(
        self,
        issue: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict how long an incident will take to resolve.
        
        Args:
            issue: Issue data
            
        Returns:
            Duration prediction with confidence
        """
        # Extract features
        severity = issue.get("severity", "Medium")
        issue_type = issue.get("type", "Unknown")
        affected_users = issue.get("affected_users", 0)
        complexity = issue.get("complexity", "medium")
        
        # Base duration by severity (in hours)
        base_durations = {
            "Critical": 4,
            "High": 8,
            "Medium": 16,
            "Low": 24
        }
        
        base_duration = base_durations.get(severity, 16)
        
        # Adjust for complexity
        complexity_multipliers = {
            "low": 0.7,
            "medium": 1.0,
            "high": 1.5,
            "very_high": 2.0
        }
        
        duration = base_duration * complexity_multipliers.get(complexity, 1.0)
        
        # Adjust for scale
        if affected_users > 50000:
            duration *= 1.3  # More users = more pressure but also more resources
        elif affected_users > 10000:
            duration *= 1.1
        
        # Adjust for issue type
        if "infrastructure" in issue_type.lower():
            duration *= 1.2
        elif "configuration" in issue_type.lower():
            duration *= 0.8
        
        # Calculate confidence
        confidence = 0.65  # Base confidence
        if issue.get("similar_issues_resolved", 0) > 3:
            confidence += 0.15  # Higher confidence if we've seen similar issues
        
        # Estimated completion time
        estimated_completion = datetime.now() + timedelta(hours=duration)
        
        prediction = {
            "issue_id": issue.get("issue_id", "unknown"),
            "estimated_duration_hours": round(duration, 1),
            "estimated_completion": estimated_completion.isoformat(),
            "confidence": round(confidence, 2),
            "factors": {
                "severity": severity,
                "complexity": complexity,
                "affected_users": affected_users,
                "issue_type": issue_type
            },
            "range": {
                "min_hours": round(duration * 0.7, 1),
                "max_hours": round(duration * 1.5, 1)
            },
            "predicted_at": datetime.now().isoformat()
        }
        
        logger.debug(
            "Incident duration predicted",
            issue_id=prediction["issue_id"],
            duration_hours=prediction["estimated_duration_hours"]
        )
        
        return prediction
    
    def predict_optimal_actions(
        self,
        state: Dict[str, Any],
        budget: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict optimal actions to take given current state.
        
        Args:
            state: Current operational state
            budget: Optional budget constraint
            
        Returns:
            Ranked list of recommended actions
        """
        actions = []
        
        # Analyze churn state
        churn_rate = state.get("churn_rate", 0.05)
        if churn_rate > 0.06:  # Above 6%
            actions.append({
                "action": "launch_retention_campaign",
                "priority": "high",
                "estimated_cost": 500000,
                "estimated_impact": 2500000,
                "roi": 5.0,
                "timeframe": "2-4 weeks",
                "description": "Launch targeted retention campaign for high-risk cohorts",
                "confidence": 0.85
            })
        
        # Analyze production issues
        critical_issues = state.get("critical_issues", 0)
        if critical_issues > 5:
            actions.append({
                "action": "emergency_engineering_sprint",
                "priority": "critical",
                "estimated_cost": 200000,
                "estimated_impact": 1000000,
                "roi": 5.0,
                "timeframe": "1-2 weeks",
                "description": "Dedicate engineering resources to resolve critical issues",
                "confidence": 0.90
            })
        
        # Analyze streaming quality
        buffering_ratio = state.get("buffering_ratio", 0.02)
        if buffering_ratio > 0.03:
            actions.append({
                "action": "cdn_optimization",
                "priority": "high",
                "estimated_cost": 300000,
                "estimated_impact": 1500000,
                "roi": 5.0,
                "timeframe": "2-3 weeks",
                "description": "Optimize CDN configuration and add capacity",
                "confidence": 0.80
            })
        
        # Analyze content performance
        content_roi = state.get("content_roi", 1.5)
        if content_roi < 1.2:
            actions.append({
                "action": "content_portfolio_optimization",
                "priority": "medium",
                "estimated_cost": 1000000,
                "estimated_impact": 3000000,
                "roi": 3.0,
                "timeframe": "1-2 months",
                "description": "Optimize content portfolio using Pareto analysis",
                "confidence": 0.75
            })
        
        # Sort by priority and ROI
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        actions.sort(
            key=lambda a: (priority_order[a["priority"]], a["roi"]),
            reverse=True
        )
        
        # Apply budget constraint if provided
        if budget:
            selected_actions = []
            remaining_budget = budget
            
            for action in actions:
                if action["estimated_cost"] <= remaining_budget:
                    selected_actions.append(action)
                    remaining_budget -= action["estimated_cost"]
            
            actions = selected_actions
        
        logger.info(
            "Optimal actions predicted",
            actions_recommended=len(actions),
            total_estimated_cost=sum(a["estimated_cost"] for a in actions),
            total_estimated_impact=sum(a["estimated_impact"] for a in actions)
        )
        
        return actions
    
    def _recommend_interventions(
        self,
        contributing_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Recommend interventions based on churn factors."""
        interventions = []
        
        factor_map = {
            "low_engagement": "Personalized content recommendations and engagement campaigns",
            "low_content_diversity": "Curated content discovery features",
            "new_subscriber": "Enhanced onboarding and welcome campaigns",
            "payment_issues": "Proactive payment support and flexible payment options",
            "high_support_tickets": "Priority customer support and issue resolution",
            "inactivity": "Re-engagement campaigns with exclusive content offers"
        }
        
        for factor in contributing_factors[:3]:  # Top 3 factors
            factor_name = factor["factor"]
            if factor_name in factor_map:
                interventions.append(factor_map[factor_name])
        
        return interventions

