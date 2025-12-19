"""
AI-Powered Insights Generator.

Generates contextual, actionable insights using LLM analysis and statistical methods.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class AIInsightsGenerator:
    """
    Generate AI-powered insights and recommendations.
    
    Features:
    - Executive summaries
    - Root cause analysis
    - Action plan generation
    - Impact assessments
    """
    
    def __init__(self, llm_provider: Optional[str] = None):
        """
        Initialize insights generator.
        
        Args:
            llm_provider: LLM provider ("anthropic", "openai", or None for rule-based)
        """
        self.llm_provider = llm_provider
        self.use_llm = llm_provider is not None
        
    def generate_executive_summary(
        self,
        data: Dict[str, Any],
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """
        Generate executive summary from operational data.
        
        Args:
            data: Operational data (churn, production, streaming, etc.)
            timeframe: Time period for summary
            
        Returns:
            Executive summary with key insights
        """
        summary = {
            "generated_at": datetime.now().isoformat(),
            "timeframe": timeframe,
            "key_insights": [],
            "critical_alerts": [],
            "opportunities": [],
            "recommendations": []
        }
        
        # Analyze churn data
        if "churn" in data:
            churn_insights = self._analyze_churn_data(data["churn"])
            summary["key_insights"].extend(churn_insights["insights"])
            if churn_insights.get("critical"):
                summary["critical_alerts"].append(churn_insights["critical"])
        
        # Analyze production issues
        if "production" in data:
            prod_insights = self._analyze_production_data(data["production"])
            summary["key_insights"].extend(prod_insights["insights"])
            summary["recommendations"].extend(prod_insights["recommendations"])
        
        # Analyze streaming metrics
        if "streaming" in data:
            streaming_insights = self._analyze_streaming_data(data["streaming"])
            summary["key_insights"].extend(streaming_insights["insights"])
            if streaming_insights.get("opportunities"):
                summary["opportunities"].extend(streaming_insights["opportunities"])
        
        # Generate overall recommendation
        summary["executive_recommendation"] = self._generate_priority_recommendation(summary)
        
        logger.info(
            "Executive summary generated",
            insights=len(summary["key_insights"]),
            alerts=len(summary["critical_alerts"])
        )
        
        return summary
    
    def generate_root_cause_analysis(
        self,
        issue: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate root cause analysis for an issue.
        
        Args:
            issue: Issue data
            context: Additional context (related issues, metrics, etc.)
            
        Returns:
            Root cause analysis with confidence scores
        """
        analysis = {
            "issue_id": issue.get("issue_id", "Unknown"),
            "issue_summary": issue.get("title", "Unknown issue"),
            "root_causes": [],
            "contributing_factors": [],
            "confidence_score": 0.0,
            "recommended_actions": []
        }
        
        # Analyze issue characteristics
        severity = issue.get("severity", "Medium")
        affected_users = issue.get("affected_users", 0)
        issue_type = issue.get("type", "Unknown")
        
        # Identify potential root causes
        root_causes = []
        
        # Rule 1: High user impact suggests infrastructure issue
        if affected_users > 10000:
            root_causes.append({
                "cause": "Infrastructure capacity or performance degradation",
                "confidence": 0.85,
                "evidence": f"{affected_users:,} users affected suggests system-wide issue",
                "recommended_action": "Scale infrastructure, check CDN performance"
            })
        
        # Rule 2: Issue type patterns
        if "streaming" in issue_type.lower() or "buffering" in issue.get("title", "").lower():
            root_causes.append({
                "cause": "CDN or network performance issue",
                "confidence": 0.80,
                "evidence": "Streaming-related symptoms detected",
                "recommended_action": "Analyze CDN logs, check network latency"
            })
        
        # Rule 3: Check context for correlations
        if context and "related_issues" in context:
            related_count = len(context["related_issues"])
            if related_count > 3:
                root_causes.append({
                    "cause": "Systemic issue affecting multiple components",
                    "confidence": 0.75,
                    "evidence": f"{related_count} related issues found",
                    "recommended_action": "Investigate common dependencies"
                })
        
        # Rule 4: Revenue impact suggests payment or subscription issue
        revenue_impact = issue.get("estimated_revenue_impact", 0)
        if revenue_impact > 50000:
            root_causes.append({
                "cause": "Payment processing or subscription management issue",
                "confidence": 0.70,
                "evidence": f"${revenue_impact:,} revenue impact detected",
                "recommended_action": "Check payment gateway, review subscription flows"
            })
        
        # Sort by confidence
        root_causes.sort(key=lambda x: x["confidence"], reverse=True)
        
        analysis["root_causes"] = root_causes[:3]  # Top 3
        analysis["confidence_score"] = root_causes[0]["confidence"] if root_causes else 0.0
        analysis["recommended_actions"] = [rc["recommended_action"] for rc in root_causes]
        
        logger.info(
            "Root cause analysis generated",
            issue_id=issue.get("issue_id"),
            root_causes_found=len(root_causes),
            confidence=analysis["confidence_score"]
        )
        
        return analysis
    
    def generate_action_plan(
        self,
        insights: List[Dict[str, Any]],
        budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generate prioritized action plan from insights.
        
        Args:
            insights: List of insights/issues
            budget: Optional budget constraint
            
        Returns:
            Prioritized action plan with ROI estimates
        """
        action_plan = {
            "generated_at": datetime.now().isoformat(),
            "total_actions": 0,
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "estimated_total_cost": 0.0,
            "estimated_total_impact": 0.0,
            "roi_estimate": 0.0
        }
        
        actions = []
        
        for insight in insights:
            # Extract action from insight
            action = {
                "title": insight.get("title", "Action required"),
                "description": insight.get("description", ""),
                "priority": self._calculate_priority(insight),
                "estimated_cost": insight.get("estimated_cost", 10000),
                "estimated_impact": insight.get("estimated_impact", 50000),
                "timeframe": insight.get("timeframe", "1-2 weeks"),
                "dependencies": insight.get("dependencies", [])
            }
            
            action["roi"] = action["estimated_impact"] / action["estimated_cost"] if action["estimated_cost"] > 0 else 0
            actions.append(action)
        
        # Sort by priority and ROI
        actions.sort(key=lambda a: (
            {"high": 3, "medium": 2, "low": 1}[a["priority"]],
            a["roi"]
        ), reverse=True)
        
        # Categorize by priority
        for action in actions:
            if action["priority"] == "high":
                action_plan["high_priority"].append(action)
            elif action["priority"] == "medium":
                action_plan["medium_priority"].append(action)
            else:
                action_plan["low_priority"].append(action)
        
        # Calculate totals
        action_plan["total_actions"] = len(actions)
        action_plan["estimated_total_cost"] = sum(a["estimated_cost"] for a in actions)
        action_plan["estimated_total_impact"] = sum(a["estimated_impact"] for a in actions)
        
        if action_plan["estimated_total_cost"] > 0:
            action_plan["roi_estimate"] = action_plan["estimated_total_impact"] / action_plan["estimated_total_cost"]
        
        # Apply budget constraint if provided
        if budget:
            action_plan = self._apply_budget_constraint(action_plan, budget)
        
        logger.info(
            "Action plan generated",
            total_actions=action_plan["total_actions"],
            high_priority=len(action_plan["high_priority"]),
            roi=action_plan["roi_estimate"]
        )
        
        return action_plan
    
    def generate_impact_assessment(
        self,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate impact assessment for a scenario.
        
        Args:
            scenario: Scenario data (changes, assumptions, etc.)
            
        Returns:
            Impact assessment with projections
        """
        assessment = {
            "scenario_name": scenario.get("name", "Unnamed scenario"),
            "assumptions": scenario.get("assumptions", []),
            "projected_impacts": {
                "revenue": {},
                "churn": {},
                "operations": {},
                "customer_satisfaction": {}
            },
            "risks": [],
            "opportunities": [],
            "confidence_level": "medium"
        }
        
        # Analyze revenue impact
        if "revenue_change" in scenario:
            revenue_change = scenario["revenue_change"]
            assessment["projected_impacts"]["revenue"] = {
                "change_percentage": revenue_change,
                "annual_impact": revenue_change * 750_000_000,  # Base $750M
                "confidence": 0.75
            }
        
        # Analyze churn impact
        if "churn_reduction" in scenario:
            churn_reduction = scenario["churn_reduction"]
            assessment["projected_impacts"]["churn"] = {
                "reduction_percentage": churn_reduction,
                "subscribers_retained": int(churn_reduction * 8_000_000 * 0.05),  # 5% base churn
                "ltv_preserved": churn_reduction * 8_000_000 * 0.05 * 8.99 * 12,
                "confidence": 0.70
            }
        
        # Identify risks
        if scenario.get("aggressive", False):
            assessment["risks"].append({
                "risk": "Aggressive assumptions may not materialize",
                "likelihood": "medium",
                "mitigation": "Implement phased rollout with monitoring"
            })
        
        # Identify opportunities
        if scenario.get("investment") and scenario["investment"] > 0:
            assessment["opportunities"].append({
                "opportunity": "Investment in technology/content",
                "potential_return": scenario["investment"] * 3,  # 3x ROI assumption
                "timeframe": "6-12 months"
            })
        
        logger.info(
            "Impact assessment generated",
            scenario=scenario.get("name"),
            risks=len(assessment["risks"]),
            opportunities=len(assessment["opportunities"])
        )
        
        return assessment
    
    def _analyze_churn_data(self, churn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze churn data and generate insights."""
        insights = {"insights": [], "critical": None}
        
        at_risk = churn_data.get("total_at_risk", 0)
        annual_impact = churn_data.get("annual_impact", 0)
        
        if at_risk > 200000:
            insights["critical"] = {
                "type": "churn_spike",
                "message": f"⚠️ {at_risk:,} subscribers at risk (${annual_impact/1e6:.1f}M annual impact)",
                "severity": "critical"
            }
        
        insights["insights"].append({
            "category": "churn",
            "insight": f"{at_risk:,} subscribers at high churn risk",
            "impact": f"${annual_impact/1e6:.1f}M annual revenue at risk",
            "action": "Launch targeted retention campaigns"
        })
        
        return insights
    
    def _analyze_production_data(self, prod_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze production data and generate insights."""
        insights = {"insights": [], "recommendations": []}
        
        critical_issues = prod_data.get("critical_count", 0)
        total_issues = prod_data.get("total_issues", 0)
        
        if critical_issues > 5:
            insights["insights"].append({
                "category": "production",
                "insight": f"{critical_issues} critical production issues require immediate attention",
                "impact": "High risk of service degradation",
                "action": "Escalate to engineering leadership"
            })
            insights["recommendations"].append(
                "Set up war room for critical issue resolution"
            )
        
        if total_issues > 50:
            insights["recommendations"].append(
                "Implement Pareto analysis to focus on top 20% of issues"
            )
        
        return insights
    
    def _analyze_streaming_data(self, streaming_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze streaming data and generate insights."""
        insights = {"insights": [], "opportunities": []}
        
        buffering_ratio = streaming_data.get("buffering_ratio", 0)
        
        if buffering_ratio > 0.03:  # > 3%
            insights["insights"].append({
                "category": "streaming",
                "insight": f"Buffering ratio at {buffering_ratio*100:.1f}% (target: <2%)",
                "impact": "Poor user experience, increased churn risk",
                "action": "Investigate CDN performance and network issues"
            })
        else:
            insights["opportunities"].append({
                "opportunity": "Streaming quality is excellent",
                "recommendation": "Leverage in marketing campaigns"
            })
        
        return insights
    
    def _generate_priority_recommendation(self, summary: Dict[str, Any]) -> str:
        """Generate overall priority recommendation."""
        critical_count = len(summary["critical_alerts"])
        
        if critical_count > 0:
            return f"🚨 URGENT: {critical_count} critical issue(s) require immediate attention. Focus on crisis management."
        
        insights_count = len(summary["key_insights"])
        if insights_count > 5:
            return "📊 Multiple operational areas need attention. Apply Pareto principle to focus on top 20% of issues."
        
        return "✅ Operations are stable. Focus on optimization and growth opportunities."
    
    def _calculate_priority(self, insight: Dict[str, Any]) -> str:
        """Calculate priority level for an insight."""
        impact = insight.get("estimated_impact", 0)
        urgency = insight.get("urgency", "medium")
        
        if urgency == "critical" or impact > 500000:
            return "high"
        elif urgency == "high" or impact > 100000:
            return "medium"
        else:
            return "low"
    
    def _apply_budget_constraint(
        self,
        action_plan: Dict[str, Any],
        budget: float
    ) -> Dict[str, Any]:
        """Apply budget constraint to action plan."""
        # Prioritize high-priority, high-ROI actions within budget
        all_actions = (
            action_plan["high_priority"] +
            action_plan["medium_priority"] +
            action_plan["low_priority"]
        )
        
        selected_actions = []
        remaining_budget = budget
        
        for action in all_actions:
            if action["estimated_cost"] <= remaining_budget:
                selected_actions.append(action)
                remaining_budget -= action["estimated_cost"]
        
        # Recategorize
        action_plan["high_priority"] = [a for a in selected_actions if a["priority"] == "high"]
        action_plan["medium_priority"] = [a for a in selected_actions if a["priority"] == "medium"]
        action_plan["low_priority"] = [a for a in selected_actions if a["priority"] == "low"]
        action_plan["total_actions"] = len(selected_actions)
        action_plan["budget_constraint"] = budget
        action_plan["budget_utilized"] = budget - remaining_budget
        action_plan["budget_remaining"] = remaining_budget
        
        return action_plan



