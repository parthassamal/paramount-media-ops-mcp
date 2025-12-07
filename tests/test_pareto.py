"""
Test suite for Pareto analysis engine.

Run with: pytest tests/test_pareto.py
"""

import pytest
from mcp.pareto import ParetoCalculator, ParetoInsights


class TestParetoCalculator:
    def test_basic_analysis(self):
        calculator = ParetoCalculator()
        items = [
            {"id": "A", "impact": 100},
            {"id": "B", "impact": 50},
            {"id": "C", "impact": 30},
            {"id": "D", "impact": 15},
            {"id": "E", "impact": 5}
        ]
        
        result = calculator.analyze(items, "impact", "id")
        
        assert result.total_impact == 200
        assert len(result.top_20_percent_indices) == 1  # 20% of 5 = 1
        assert result.sorted_items[0]["id"] == "A"
    
    def test_pareto_validation(self):
        calculator = ParetoCalculator(validation_range=(0.75, 0.85))
        
        # Create ideal Pareto distribution
        items = [
            {"id": "A", "impact": 80},
            {"id": "B", "impact": 10},
            {"id": "C", "impact": 5},
            {"id": "D", "impact": 3},
            {"id": "E", "impact": 2}
        ]
        
        result = calculator.analyze(items, "impact", "id")
        assert result.is_pareto_valid
    
    def test_multiple_dimensions(self):
        calculator = ParetoCalculator()
        items = [
            {"id": "A", "impact1": 100, "impact2": 50},
            {"id": "B", "impact1": 50, "impact2": 100},
        ]
        
        results = calculator.analyze_multiple_dimensions(
            items,
            ["impact1", "impact2"]
        )
        
        assert "impact1" in results
        assert "impact2" in results


class TestParetoInsights:
    def test_generate_insights(self):
        insights_gen = ParetoInsights()
        calculator = ParetoCalculator()
        
        items = [
            {"id": "A", "name": "Issue A", "impact": 80},
            {"id": "B", "name": "Issue B", "impact": 20}
        ]
        
        result = calculator.analyze(items, "impact", "id")
        insights = insights_gen.generate_insights(
            result,
            context="test issues",
            impact_metric="impact_units",
            item_type="issues"
        )
        
        assert "summary" in insights
        assert "key_findings" in insights
        assert "recommendations" in insights
    
    def test_compare_scenarios(self):
        insights_gen = ParetoInsights()
        calculator = ParetoCalculator()
        
        baseline_items = [{"id": str(i), "impact": 100 - i*10} for i in range(10)]
        scenario_items = [{"id": str(i), "impact": 50 - i*5} for i in range(10)]
        
        baseline = calculator.analyze(baseline_items, "impact", "id")
        scenario = calculator.analyze(scenario_items, "impact", "id")
        
        comparison = insights_gen.compare_scenarios(
            baseline,
            scenario,
            "Intervention Scenario"
        )
        
        assert "percentage_reduction" in comparison
        assert comparison["baseline_impact"] > comparison["scenario_impact"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
