"""
Test suite for tools.

Run with: pytest tests/test_tools.py
"""

import pytest
from mcp.tools import (
    create_analyze_churn,
    create_analyze_complaints,
    create_analyze_production,
    create_forecast_revenue,
    create_generate_campaign
)


class TestAnalyzeChurnRootCause:
    def test_execute_all_cohorts(self):
        tool = create_analyze_churn()
        result = tool.execute()
        assert "root_causes" in result
        assert "financial_impact" in result
    
    def test_execute_specific_cohort(self):
        tool = create_analyze_churn()
        result = tool.execute(cohort_id="COHORT-001")
        assert len(result["root_causes"]) == 1


class TestAnalyzeComplaintThemes:
    def test_execute_with_defaults(self):
        tool = create_analyze_complaints()
        result = tool.execute()
        assert "high_priority_themes" in result
        assert "prioritization" in result
    
    def test_fixable_only(self):
        tool = create_analyze_complaints()
        result = tool.execute(focus_on_fixable=True)
        for theme in result["high_priority_themes"]:
            assert theme.get("complexity") in ["low", "medium", "high"]


class TestAnalyzeProductionRisk:
    def test_execute_with_defaults(self):
        tool = create_analyze_production()
        result = tool.execute()
        assert "pareto_analysis" in result
        assert "risk_assessment" in result
    
    def test_mitigation_plans(self):
        tool = create_analyze_production()
        result = tool.execute(include_mitigation=True)
        assert "mitigation_plans" in result


class TestForecastRevenueWithConstraints:
    def test_execute_unlimited_budget(self):
        tool = create_forecast_revenue()
        result = tool.execute()
        assert "baseline_forecast" in result
        assert "constrained_forecast" in result
    
    def test_execute_with_budget(self):
        tool = create_forecast_revenue()
        result = tool.execute(budget_constraint=5000000)
        assert result["constraints"]["budget"] == 5000000
    
    def test_different_scenarios(self):
        tool = create_forecast_revenue()
        conservative = tool.execute(scenario="conservative")
        aggressive = tool.execute(scenario="aggressive")
        
        assert conservative["constrained_forecast"]["recovery_rate"] < \
               aggressive["constrained_forecast"]["recovery_rate"]


class TestGenerateRetentionCampaign:
    def test_execute_with_cohort(self):
        tool = create_generate_campaign()
        result = tool.execute(cohort_id="COHORT-001")
        assert "campaign_name" in result
        assert "campaign_plan" in result
        assert "projected_outcomes" in result
    
    def test_auto_budget_calculation(self):
        tool = create_generate_campaign()
        result = tool.execute(cohort_id="COHORT-001")
        assert result["budget"] > 0
    
    def test_custom_budget(self):
        tool = create_generate_campaign()
        result = tool.execute(cohort_id="COHORT-001", budget=1000000)
        assert result["budget"] == 1000000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
