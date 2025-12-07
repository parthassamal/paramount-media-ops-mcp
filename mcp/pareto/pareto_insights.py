"""
Pareto Insights Generator.

This module generates business insights from Pareto analysis results,
translating statistical findings into actionable recommendations.
"""

from typing import List, Dict, Any, Optional
from .pareto_calculator import ParetoResult, ParetoCalculator


class ParetoInsights:
    """
    Generator for business insights from Pareto analysis.
    
    Translates Pareto analysis results into actionable business insights
    and recommendations for streaming operations optimization.
    """
    
    def __init__(self):
        """Initialize insights generator."""
        self.calculator = ParetoCalculator()
    
    def generate_insights(
        self,
        result: ParetoResult,
        context: str,
        impact_metric: str,
        item_type: str = "items"
    ) -> Dict[str, Any]:
        """
        Generate business insights from Pareto analysis.
        
        Args:
            result: ParetoResult from analysis
            context: Business context (e.g., "production delays", "churn drivers")
            impact_metric: Name of impact metric (e.g., "delay days", "churned subscribers")
            item_type: Type of items analyzed (e.g., "issues", "shows", "complaints")
        
        Returns:
            Dictionary containing insights and recommendations
        """
        top_20_count = len(result.top_20_percent_indices)
        total_count = len(result.sorted_items)
        contribution_pct = result.top_20_percent_contribution * 100
        
        # Build insight message
        insight = {
            "summary": self._build_summary(
                top_20_count, total_count, contribution_pct, context, item_type
            ),
            "key_findings": self._extract_key_findings(result, impact_metric, item_type),
            "recommendations": self._generate_recommendations(
                result, context, impact_metric, item_type
            ),
            "financial_impact": self._estimate_financial_impact(
                result, contribution_pct, impact_metric
            ),
            "priority_actions": self._identify_priority_actions(result, context),
            "pareto_validation": result._get_validation_message()
        }
        
        return insight
    
    def _build_summary(
        self,
        top_count: int,
        total_count: int,
        contribution_pct: float,
        context: str,
        item_type: str
    ) -> str:
        """Build executive summary."""
        return (
            f"Focus on {top_count} out of {total_count} {item_type} ({top_count/total_count*100:.0f}%) "
            f"driving {contribution_pct:.1f}% of {context}. "
            f"This represents a critical leverage point for operational improvement."
        )
    
    def _extract_key_findings(
        self,
        result: ParetoResult,
        impact_metric: str,
        item_type: str
    ) -> List[str]:
        """Extract key findings from analysis."""
        findings = []
        
        # Top contributor impact
        if result.sorted_items:
            top_item = result.sorted_items[0]
            top_contribution = result.cumulative_contributions[0] * 100
            findings.append(
                f"Single highest impact: {top_item.get('name', top_item.get('id', 'Unknown'))} "
                f"contributes {top_contribution:.1f}% of total {impact_metric}"
            )
        
        # Concentration level
        if result.is_pareto_valid:
            findings.append(
                f"Pareto principle confirmed: Classic 80/20 distribution observed"
            )
        elif result.top_20_percent_contribution > 0.85:
            findings.append(
                f"High concentration detected: Impact more concentrated than typical Pareto distribution"
            )
        
        # Total impact scale
        findings.append(
            f"Total {impact_metric} across all {item_type}: {result.total_impact:,.0f}"
        )
        
        return findings
    
    def _generate_recommendations(
        self,
        result: ParetoResult,
        context: str,
        impact_metric: str,
        item_type: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        top_count = len(result.top_20_percent_indices)
        
        recommendations.append(
            f"IMMEDIATE: Prioritize resources on top {top_count} {item_type} for maximum ROI"
        )
        
        if result.top_20_percent_contribution > 0.80:
            recommendations.append(
                f"HIGH LEVERAGE: Solving these {top_count} items could reduce {context} by "
                f"{result.top_20_percent_contribution*100:.0f}%"
            )
        
        recommendations.append(
            f"RESOURCE ALLOCATION: Assign senior teams to investigate root causes of top contributors"
        )
        
        if not result.is_pareto_valid and result.top_20_percent_contribution < 0.75:
            recommendations.append(
                f"BROAD STRATEGY NEEDED: Impact is distributed across many {item_type}; "
                f"consider systemic improvements"
            )
        
        return recommendations
    
    def _estimate_financial_impact(
        self,
        result: ParetoResult,
        contribution_pct: float,
        impact_metric: str
    ) -> Dict[str, Any]:
        """Estimate financial impact of addressing top contributors."""
        # Estimates based on Paramount+ industry benchmarks
        impact_multipliers = {
            "delay_days": 50000,  # $50K per day of production delay
            "churned_subscribers": 9.99,  # Average monthly ARPU
            "complaint_volume": 25,  # Cost per support ticket
            "content_underperformance": 100000  # Opportunity cost per underperforming show
        }
        
        # Use conservative multiplier if metric not recognized
        multiplier = impact_multipliers.get(impact_metric, 1000)
        
        potential_savings = result.total_impact * (contribution_pct / 100) * multiplier
        
        return {
            "potential_annual_savings": round(potential_savings, 2),
            "addressable_impact": round(result.total_impact * (contribution_pct / 100), 2),
            "confidence": "moderate" if result.is_pareto_valid else "low",
            "basis": f"Industry benchmark: ${multiplier:,.0f} per unit of {impact_metric}"
        }
    
    def _identify_priority_actions(
        self,
        result: ParetoResult,
        context: str
    ) -> List[Dict[str, str]]:
        """Identify specific priority actions."""
        actions = []
        
        for idx, item_idx in enumerate(result.top_20_percent_indices[:5], 1):
            if item_idx < len(result.sorted_items):
                item = result.sorted_items[item_idx]
                actions.append({
                    "priority": idx,
                    "item": item.get('name', item.get('id', f"Item {item_idx}")),
                    "action": f"Deep-dive analysis: Investigate root cause and mitigation strategies",
                    "expected_impact": f"{result.cumulative_contributions[item_idx]*100:.1f}% of total"
                })
        
        return actions
    
    def compare_scenarios(
        self,
        baseline: ParetoResult,
        scenario: ParetoResult,
        scenario_name: str
    ) -> Dict[str, Any]:
        """
        Compare baseline vs. scenario to show impact of interventions.
        
        Args:
            baseline: Current state Pareto analysis
            scenario: Projected state after interventions
            scenario_name: Name of the scenario
        
        Returns:
            Comparison insights
        """
        impact_reduction = baseline.total_impact - scenario.total_impact
        reduction_pct = (impact_reduction / baseline.total_impact) * 100
        
        return {
            "scenario_name": scenario_name,
            "baseline_impact": round(baseline.total_impact, 2),
            "scenario_impact": round(scenario.total_impact, 2),
            "absolute_reduction": round(impact_reduction, 2),
            "percentage_reduction": round(reduction_pct, 2),
            "recommendation": (
                f"Implementing {scenario_name} could reduce impact by {reduction_pct:.1f}%"
                if reduction_pct > 0
                else f"{scenario_name} shows no improvement"
            )
        }
