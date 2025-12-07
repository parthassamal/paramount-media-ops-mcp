"""
Forecast Revenue with Constraints Tool.

Projects revenue impact of fixes with operational constraints.
"""

from typing import Dict, Any, List, Optional
from mcp.resources import RevenueImpactResource, OperationalEfficiencyResource


class ForecastRevenueWithConstraintsTool:
    """
    Tool to forecast revenue impact considering operational constraints.
    
    Models different intervention scenarios with budget and timeline constraints.
    """
    
    def __init__(self):
        """Initialize the tool."""
        self.revenue_resource = RevenueImpactResource()
        self.efficiency_resource = OperationalEfficiencyResource()
    
    def execute(
        self,
        budget_constraint: Optional[float] = None,
        timeline_months: int = 12,
        scenario: str = "moderate"
    ) -> Dict[str, Any]:
        """
        Forecast revenue with operational constraints.
        
        Args:
            budget_constraint: Maximum budget available (None = unlimited)
            timeline_months: Timeline for interventions (default: 12)
            scenario: Scenario to model: "conservative", "moderate", "aggressive"
        
        Returns:
            Revenue forecast with multiple scenarios
            
        Example:
            >>> tool = ForecastRevenueWithConstraintsTool()
            >>> result = tool.execute(budget_constraint=10000000, scenario="moderate")
            >>> print(result["forecast"]["total_recovery"])
            25000000
        """
        # Get current revenue impact
        revenue_data = self.revenue_resource.query(include_projections=True)
        
        # Get operational efficiency constraints
        efficiency_data = self.efficiency_resource.query()
        
        # Get ROI prioritization
        roi_data = self.revenue_resource.get_roi_prioritization()
        
        # Build forecast models
        baseline_forecast = self._build_baseline_forecast(revenue_data, timeline_months)
        
        constrained_forecast = self._build_constrained_forecast(
            revenue_data,
            roi_data,
            budget_constraint,
            timeline_months,
            scenario,
            efficiency_data
        )
        
        # Calculate gap and recommendations
        gap_analysis = self._analyze_gap(baseline_forecast, constrained_forecast)
        
        return {
            "constraints": {
                "budget": budget_constraint or "unlimited",
                "timeline_months": timeline_months,
                "scenario": scenario,
                "operational_efficiency_score": efficiency_data["efficiency_score"]["overall_efficiency_score"]
            },
            "baseline_forecast": baseline_forecast,
            "constrained_forecast": constrained_forecast,
            "gap_analysis": gap_analysis,
            "recommendations": self._generate_recommendations(
                gap_analysis,
                budget_constraint,
                efficiency_data
            )
        }
    
    def _build_baseline_forecast(
        self,
        revenue_data: Dict[str, Any],
        timeline_months: int
    ) -> Dict[str, Any]:
        """Build baseline forecast (do nothing scenario)."""
        total_impact = revenue_data["total_aggregated_impact"]
        
        # Annualized impact
        annual_loss = total_impact["addressable_annual_loss"]
        
        # Project over timeline
        timeline_loss = annual_loss * (timeline_months / 12)
        
        return {
            "scenario": "baseline_do_nothing",
            "timeline_months": timeline_months,
            "projected_loss": timeline_loss,
            "annual_loss_rate": annual_loss,
            "breakdown": revenue_data["total_aggregated_impact"]["breakdown"]
        }
    
    def _build_constrained_forecast(
        self,
        revenue_data: Dict[str, Any],
        roi_data: Dict[str, Any],
        budget_constraint: Optional[float],
        timeline_months: int,
        scenario: str,
        efficiency_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build forecast with constraints applied."""
        # Get scenario-based recovery rates
        recovery_rates = {
            "conservative": 0.30,
            "moderate": 0.50,
            "aggressive": 0.70
        }
        recovery_rate = recovery_rates.get(scenario, 0.50)
        
        # Adjust recovery rate based on operational efficiency
        efficiency_score = efficiency_data["efficiency_score"]["overall_efficiency_score"]
        efficiency_multiplier = efficiency_score / 100  # 0-1 scale
        adjusted_recovery_rate = recovery_rate * efficiency_multiplier
        
        # Get addressable loss
        addressable_loss = revenue_data["total_aggregated_impact"]["addressable_annual_loss"]
        
        # Filter initiatives by budget
        feasible_initiatives = self._filter_by_budget(
            roi_data["initiatives"],
            budget_constraint
        )
        
        # Calculate potential recovery
        max_recovery = addressable_loss * adjusted_recovery_rate
        initiative_recovery = sum(i["revenue_impact"] for i in feasible_initiatives)
        
        # Actual recovery is min of max recovery and initiative recovery
        actual_recovery = min(max_recovery, initiative_recovery)
        
        # Project over timeline
        timeline_recovery = actual_recovery * (timeline_months / 12)
        
        # Calculate net position
        baseline_loss = addressable_loss * (timeline_months / 12)
        net_position = baseline_loss - timeline_recovery
        
        return {
            "scenario": scenario,
            "timeline_months": timeline_months,
            "recovery_rate": round(adjusted_recovery_rate, 2),
            "efficiency_adjustment": round(efficiency_multiplier, 2),
            "potential_recovery": timeline_recovery,
            "net_loss": net_position,
            "initiatives_deployed": feasible_initiatives,
            "total_investment": sum(i["investment_required"] for i in feasible_initiatives),
            "roi": round(timeline_recovery / sum(i["investment_required"] for i in feasible_initiatives), 2) if feasible_initiatives else 0
        }
    
    def _filter_by_budget(
        self,
        initiatives: List[Dict[str, Any]],
        budget_constraint: Optional[float]
    ) -> List[Dict[str, Any]]:
        """Filter initiatives by budget constraint."""
        if budget_constraint is None:
            return initiatives
        
        # Sort by ROI
        sorted_initiatives = sorted(initiatives, key=lambda x: x["roi_ratio"], reverse=True)
        
        # Select initiatives within budget
        selected = []
        remaining_budget = budget_constraint
        
        for initiative in sorted_initiatives:
            if initiative["investment_required"] <= remaining_budget:
                selected.append(initiative)
                remaining_budget -= initiative["investment_required"]
        
        return selected
    
    def _analyze_gap(
        self,
        baseline: Dict[str, Any],
        constrained: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze gap between baseline and constrained scenarios."""
        baseline_loss = baseline["projected_loss"]
        constrained_loss = constrained["net_loss"]
        
        improvement = baseline_loss - constrained_loss
        improvement_pct = (improvement / baseline_loss * 100) if baseline_loss > 0 else 0
        
        return {
            "baseline_loss": baseline_loss,
            "constrained_loss": constrained_loss,
            "improvement": improvement,
            "improvement_pct": round(improvement_pct, 1),
            "remaining_gap": constrained_loss,
            "gap_closure_pct": round(improvement_pct, 1)
        }
    
    def _generate_recommendations(
        self,
        gap_analysis: Dict[str, Any],
        budget_constraint: Optional[float],
        efficiency_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate recommendations based on forecast."""
        recommendations = []
        
        # Budget recommendations
        if budget_constraint and gap_analysis["remaining_gap"] > 0:
            additional_budget = gap_analysis["remaining_gap"] * 0.3  # 30% of gap
            recommendations.append({
                "area": "Budget",
                "recommendation": f"Increase budget by ${additional_budget:,.0f} to close remaining gap",
                "impact": "Could improve gap closure by 20-30%"
            })
        
        # Efficiency recommendations
        efficiency_score = efficiency_data["efficiency_score"]["overall_efficiency_score"]
        if efficiency_score < 80:
            recommendations.append({
                "area": "Operational Efficiency",
                "recommendation": "Improve operational efficiency to 80+ score before major investments",
                "impact": f"Could increase recovery rate by {(80 - efficiency_score) * 0.5:.0f}%"
            })
        
        # Prioritization recommendations
        if gap_analysis["improvement_pct"] < 50:
            recommendations.append({
                "area": "Initiative Prioritization",
                "recommendation": "Focus only on highest ROI initiatives (>3x return)",
                "impact": "Maximize recovery within budget constraints"
            })
        
        # Timeline recommendations
        recommendations.append({
            "area": "Timeline",
            "recommendation": "Execute in phases: Quick wins (0-3mo), Strategic (3-9mo), Long-term (9-12mo)",
            "impact": "Realize early wins while building momentum"
        })
        
        return recommendations


def create_tool() -> ForecastRevenueWithConstraintsTool:
    """Factory function to create the tool."""
    return ForecastRevenueWithConstraintsTool()
