"""
Test suite for resources.

Run with: pytest tests/test_resources.py
"""

import pytest
from mcp.resources import (
    create_churn_signals,
    create_complaints_topics,
    create_production_issues,
    create_content_catalog,
    create_international_markets,
    create_revenue_impact,
    create_retention_campaigns,
    create_operational_efficiency,
    create_pareto_analysis
)


class TestChurnSignals:
    def test_query_returns_data(self):
        resource = create_churn_signals()
        result = resource.query()
        assert "cohorts" in result
        assert "retention_metrics" in result
        assert len(result["cohorts"]) > 0
    
    def test_pareto_included(self):
        resource = create_churn_signals()
        result = resource.query(include_pareto=True)
        assert "pareto_analysis" in result


class TestComplaintsTopics:
    def test_query_returns_themes(self):
        resource = create_complaints_topics()
        result = resource.query()
        assert "themes" in result
        assert len(result["themes"]) > 0
    
    def test_fixable_themes(self):
        resource = create_complaints_topics()
        result = resource.get_fixable_themes()
        assert "fixable_themes" in result


class TestProductionIssues:
    def test_query_returns_issues(self):
        resource = create_production_issues()
        result = resource.query()
        assert "issues" in result
        assert "cost_summary" in result
    
    def test_critical_path(self):
        resource = create_production_issues()
        result = resource.get_critical_path_analysis()
        assert "critical_path_issues" in result


class TestContentCatalog:
    def test_query_returns_shows(self):
        resource = create_content_catalog()
        result = resource.query()
        assert "shows" in result
        assert len(result["shows"]) > 0
    
    def test_underperforming_content(self):
        resource = create_content_catalog()
        result = resource.get_underperforming_content()
        assert "underperforming_shows" in result


class TestInternationalMarkets:
    def test_query_returns_regional_data(self):
        resource = create_international_markets()
        result = resource.query()
        assert "regional_performance" in result
        assert "content_gaps" in result


class TestRevenueImpact:
    def test_query_returns_impact(self):
        resource = create_revenue_impact()
        result = resource.query()
        assert "churn_revenue_impact" in result
        assert "total_aggregated_impact" in result
    
    def test_roi_prioritization(self):
        resource = create_revenue_impact()
        result = resource.get_roi_prioritization()
        assert "initiatives" in result


class TestRetentionCampaigns:
    def test_query_returns_campaigns(self):
        resource = create_retention_campaigns()
        result = resource.query()
        assert "campaigns" in result
        assert "summary" in result


class TestOperationalEfficiency:
    def test_query_returns_metrics(self):
        resource = create_operational_efficiency()
        result = resource.query()
        assert "efficiency_score" in result
    
    def test_specific_metric_type(self):
        resource = create_operational_efficiency()
        result = resource.query(metric_type="production")
        assert "production_metrics" in result


class TestParetoAnalysis:
    def test_query_all_dimensions(self):
        resource = create_pareto_analysis()
        result = resource.query(dimension="all")
        assert "cross_dimensional_analysis" in result
    
    def test_validation(self):
        resource = create_pareto_analysis()
        result = resource.validate_pareto_principle()
        assert "overall" in result
        assert "pareto_principle_holds" in result["overall"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
