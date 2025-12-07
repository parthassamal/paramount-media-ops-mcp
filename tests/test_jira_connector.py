"""Tests for JIRA Connector"""
import pytest
from src.jira_connector import JIRAConnector


def test_jira_initialization():
    """Test JIRA connector initialization"""
    jira = JIRAConnector()
    
    assert jira is not None
    assert jira.use_mock is True  # Should use mock without credentials


def test_fetch_production_issues():
    """Test fetching production issues"""
    jira = JIRAConnector()
    issues = jira.fetch_production_issues(20)
    
    assert len(issues) > 0
    assert all("issue_id" in issue for issue in issues)
    assert all("impact_score" in issue for issue in issues)


def test_analyze_issues_with_pareto():
    """Test Pareto analysis of issues"""
    jira = JIRAConnector()
    issues = jira.fetch_production_issues(30)
    pareto_result = jira.analyze_issues_with_pareto(issues)
    
    assert "vital_few" in pareto_result
    assert "pareto_insight" in pareto_result
    assert pareto_result["total_items"] == len(issues)


def test_get_critical_issues():
    """Test getting critical issues"""
    jira = JIRAConnector()
    issues = jira.fetch_production_issues(40)
    critical = jira.get_critical_issues(issues)
    
    assert len(critical) > 0
    assert len(critical) <= len(issues)
    # Critical issues should be sorted by impact
    if len(critical) > 1:
        assert critical[0]["impact_score"] >= critical[-1]["impact_score"]


def test_create_issue():
    """Test issue creation (mock mode)"""
    jira = JIRAConnector()
    result = jira.create_issue(
        summary="Test Issue",
        description="Test Description",
        priority="High"
    )
    
    assert "status" in result
    assert result["status"] in ["created_mock", "created", "error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
