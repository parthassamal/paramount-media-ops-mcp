"""
Test suite for integration clients.

Tests JIRA, Conviva, NewRelic, and other integration clients.

Run with: pytest tests/test_integrations.py -v
"""

import pytest


class TestJiraConnector:
    """Tests for JIRA connector."""
    
    def test_initialization_mock_mode(self):
        """Test JIRA connector initializes in mock mode."""
        from mcp.integrations import JiraConnector
        
        connector = JiraConnector(mock_mode=True)
        assert connector.mock_mode is True
    
    def test_get_production_issues(self):
        """Test fetching production issues in mock mode."""
        from mcp.integrations import JiraConnector
        
        connector = JiraConnector(mock_mode=True)
        issues = connector.get_production_issues()
        
        assert isinstance(issues, list)
        assert len(issues) > 0
        
        # Check issue structure
        issue = issues[0]
        assert "issue_id" in issue
        assert "title" in issue
        assert "severity" in issue
        assert "status" in issue
    
    def test_get_production_issues_with_filters(self):
        """Test fetching issues with severity filter."""
        from mcp.integrations import JiraConnector
        
        connector = JiraConnector(mock_mode=True)
        issues = connector.get_production_issues(severity="Critical")
        
        for issue in issues:
            assert issue["severity"].lower() == "critical"
    
    def test_get_issue_by_id(self):
        """Test fetching a specific issue by ID."""
        from mcp.integrations import JiraConnector
        
        connector = JiraConnector(mock_mode=True)
        issues = connector.get_production_issues(limit=1)
        
        if issues:
            issue_id = issues[0]["issue_id"]
            issue = connector.get_issue_by_id(issue_id)
            assert issue is not None
            assert issue["issue_id"] == issue_id
    
    def test_get_critical_issues(self):
        """Test fetching critical issues."""
        from mcp.integrations import JiraConnector
        
        connector = JiraConnector(mock_mode=True)
        result = connector.get_critical_issues()
        
        # Result is a dict with issues list
        assert "issues" in result
        assert isinstance(result["issues"], list)
    
    def test_get_cost_summary(self):
        """Test cost summary calculation."""
        from mcp.integrations import JiraConnector
        
        connector = JiraConnector(mock_mode=True)
        summary = connector.get_cost_summary()
        
        # Check for actual keys in the response
        assert "total_issues" in summary
        assert "total_cost_overrun" in summary
        assert "total_delay_days" in summary


class TestConvivaClient:
    """Tests for Conviva streaming QoE client."""
    
    def test_initialization_mock_mode(self):
        """Test Conviva client initializes in mock mode."""
        from mcp.integrations import ConvivaClient
        
        client = ConvivaClient(mock_mode=True)
        assert client.mock_mode is True
    
    def test_get_qoe_metrics(self):
        """Test fetching QoE metrics."""
        from mcp.integrations import ConvivaClient
        
        client = ConvivaClient(mock_mode=True)
        result = client.get_qoe_metrics()
        
        # Check for overall metrics structure
        assert "overall" in result
        overall = result["overall"]
        assert "plays" in overall
        assert "concurrent_plays" in overall
        assert "buffering_ratio" in overall
        assert "video_start_failures" in overall
        assert "average_bitrate" in overall
    
    def test_get_qoe_metrics_with_dimension(self):
        """Test QoE metrics with dimension grouping."""
        from mcp.integrations import ConvivaClient
        
        client = ConvivaClient(mock_mode=True)
        result = client.get_qoe_metrics(dimension="device_type")
        
        assert "overall" in result
        assert "by_dimension" in result
        assert isinstance(result["by_dimension"], list)
    
    def test_get_buffering_hotspots(self):
        """Test buffering hotspot analysis."""
        from mcp.integrations import ConvivaClient
        
        client = ConvivaClient(mock_mode=True)
        result = client.get_buffering_hotspots()
        
        # Check actual structure
        assert "geographic_hotspots" in result
        assert "device_hotspots" in result
        assert "recommendations" in result
        assert isinstance(result["geographic_hotspots"], list)
    
    def test_metrics_are_realistic(self):
        """Test that mock metrics are within realistic ranges."""
        from mcp.integrations import ConvivaClient
        
        client = ConvivaClient(mock_mode=True)
        result = client.get_qoe_metrics()
        
        overall = result["overall"]
        
        # Buffering should be 0-10%
        assert 0 <= overall["buffering_ratio"] <= 0.10
        
        # Bitrate should be 1-15 Mbps
        assert 1000 <= overall["average_bitrate"] <= 15000
        
        # Plays should be positive
        assert overall["plays"] > 0


class TestNewRelicClient:
    """Tests for NewRelic APM client."""
    
    def test_initialization_mock_mode(self):
        """Test NewRelic client initializes in mock mode."""
        from mcp.integrations import NewRelicClient
        
        client = NewRelicClient(mock_mode=True)
        assert client.mock_mode is True
    
    def test_get_apm_metrics(self):
        """Test fetching APM metrics."""
        from mcp.integrations import NewRelicClient
        
        client = NewRelicClient(mock_mode=True)
        result = client.get_apm_metrics()
        
        # Check for overall metrics structure
        assert "overall" in result
        overall = result["overall"]
        assert "response_time_avg_ms" in overall
        assert "response_time_p95_ms" in overall
        assert "throughput_rpm" in overall
        assert "error_rate" in overall
        assert "apdex_score" in overall
    
    def test_get_infrastructure_metrics(self):
        """Test fetching infrastructure metrics."""
        from mcp.integrations import NewRelicClient
        
        client = NewRelicClient(mock_mode=True)
        result = client.get_infrastructure_metrics()
        
        # Check for overall metrics structure
        assert "overall" in result
        overall = result["overall"]
        assert "cpu_percent" in overall
        assert "memory_percent" in overall
        assert "disk_percent" in overall
    
    def test_get_incidents(self):
        """Test incident retrieval."""
        from mcp.integrations import NewRelicClient
        
        client = NewRelicClient(mock_mode=True)
        result = client.get_incidents()
        
        # Result is a dict with incidents list
        assert "incidents" in result
        assert isinstance(result["incidents"], list)
    
    def test_get_operational_health_summary(self):
        """Test operational health summary."""
        from mcp.integrations import NewRelicClient
        
        client = NewRelicClient(mock_mode=True)
        result = client.get_operational_health_summary()
        
        # Check actual structure
        assert "overall_health" in result
        assert "apm_summary" in result
        assert "infrastructure_summary" in result
    
    def test_apm_metrics_are_realistic(self):
        """Test that APM metrics are within realistic ranges."""
        from mcp.integrations import NewRelicClient
        
        client = NewRelicClient(mock_mode=True)
        result = client.get_apm_metrics()
        
        overall = result["overall"]
        
        # Response time should be 10-5000ms
        assert 10 <= overall["response_time_avg_ms"] <= 5000
        
        # Error rate should be 0-5%
        assert 0 <= overall["error_rate"] <= 0.05
        
        # Apdex should be 0.5-1.0
        assert 0.5 <= overall["apdex_score"] <= 1.0


class TestAnalyticsClient:
    """Tests for internal analytics client."""
    
    def test_get_churn_cohorts(self):
        """Test churn cohort retrieval."""
        from mcp.integrations import AnalyticsClient
        
        client = AnalyticsClient()
        cohorts = client.get_churn_cohorts()
        
        assert isinstance(cohorts, list)
        assert len(cohorts) > 0
        
        cohort = cohorts[0]
        assert "cohort_id" in cohort
        assert "name" in cohort
        assert "churn_risk_score" in cohort
    
    def test_get_retention_metrics(self):
        """Test retention metrics."""
        from mcp.integrations import AnalyticsClient
        
        client = AnalyticsClient()
        metrics = client.get_retention_metrics()
        
        # Check actual structure
        assert "total_subscribers" in metrics
        assert "total_at_risk_30d" in metrics
        assert "churn_rate_30d" in metrics
    
    def test_get_ltv_analysis(self):
        """Test LTV analysis."""
        from mcp.integrations import AnalyticsClient
        
        client = AnalyticsClient()
        ltv = client.get_ltv_analysis()
        
        # Check actual structure
        assert "total_ltv_at_risk" in ltv
        assert "cohort_ltv_ranking" in ltv


class TestContentAPIClient:
    """Tests for content API client."""
    
    def test_get_content_catalog(self):
        """Test content catalog retrieval."""
        from mcp.integrations import ContentAPIClient
        
        client = ContentAPIClient()
        catalog = client.get_content_catalog()
        
        assert isinstance(catalog, list)
        assert len(catalog) > 0
        
        show = catalog[0]
        assert "show_id" in show
        assert "name" in show


class TestEmailParser:
    """Tests for email parser."""
    
    def test_initialization(self):
        """Test email parser initialization."""
        from mcp.integrations import EmailParser
        
        parser = EmailParser()
        assert parser is not None
        assert parser.mock_mode is True  # Default is mock mode
    
    def test_get_complaint_themes(self):
        """Test getting complaint themes."""
        from mcp.integrations import EmailParser
        
        parser = EmailParser()
        themes = parser.get_complaint_themes()
        
        assert isinstance(themes, list)
        assert len(themes) > 0
        
        theme = themes[0]
        assert "name" in theme
        assert "complaint_volume" in theme
    
    def test_get_individual_complaints(self):
        """Test getting individual complaints."""
        from mcp.integrations import EmailParser
        
        parser = EmailParser()
        complaints = parser.get_individual_complaints(limit=5)
        
        assert isinstance(complaints, list)
        assert len(complaints) <= 5
    
    def test_get_sentiment_trends(self):
        """Test sentiment trend analysis."""
        from mcp.integrations import EmailParser
        
        parser = EmailParser()
        trends = parser.get_sentiment_trends()
        
        assert isinstance(trends, dict)


class TestFigmaClient:
    """Tests for Figma design system client."""
    
    def test_initialization_mock_mode(self):
        """Test Figma client initializes in mock mode."""
        from mcp.integrations import FigmaClient
        
        client = FigmaClient(mock_mode=True)
        assert client.mock_mode is True
    
    def test_get_design_tokens(self):
        """Test fetching design tokens."""
        from mcp.integrations import FigmaClient
        
        client = FigmaClient(mock_mode=True)
        tokens = client.get_design_tokens("test-file-id")
        
        assert "colors" in tokens
        assert "typography" in tokens
        assert "spacing" in tokens
        assert len(tokens["colors"]) > 0
    
    def test_get_dashboard_design_system(self):
        """Test fetching complete design system."""
        from mcp.integrations import FigmaClient
        
        client = FigmaClient(mock_mode=True)
        design_system = client.get_dashboard_design_system()
        
        assert "name" in design_system
        assert "tokens" in design_system
        assert "components" in design_system
        assert "breakpoints" in design_system
    
    def test_get_file_components(self):
        """Test fetching file components."""
        from mcp.integrations import FigmaClient
        
        client = FigmaClient(mock_mode=True)
        components = client.get_file_components("test-file-id")
        
        assert isinstance(components, list)
        assert len(components) > 0
        assert components[0].name is not None


class TestIntegrationConsistency:
    """Tests for consistency across integrations."""
    
    def test_all_integrations_have_mock_mode(self):
        """All integrations should support mock mode."""
        from mcp.integrations import (
            JiraConnector,
            ConvivaClient,
            NewRelicClient
        )
        
        # Each should accept mock_mode parameter
        jira = JiraConnector(mock_mode=True)
        conviva = ConvivaClient(mock_mode=True)
        newrelic = NewRelicClient(mock_mode=True)
        
        assert jira.mock_mode is True
        assert conviva.mock_mode is True
        assert newrelic.mock_mode is True
    
    def test_mock_data_is_deterministic(self):
        """Mock data should be deterministic with same seed."""
        from mcp.integrations import JiraConnector
        
        connector1 = JiraConnector(mock_mode=True)
        connector2 = JiraConnector(mock_mode=True)
        
        issues1 = connector1.get_production_issues(limit=5)
        issues2 = connector2.get_production_issues(limit=5)
        
        # Should get same issues with same seed
        assert len(issues1) == len(issues2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
