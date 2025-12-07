"""Tests for Pareto Analysis Engine"""
import pytest
from src.pareto_engine import ParetoAnalyzer


def test_pareto_basic_analysis():
    """Test basic Pareto analysis"""
    data = [
        {"item": "A", "value": 100},
        {"item": "B", "value": 80},
        {"item": "C", "value": 60},
        {"item": "D", "value": 40},
        {"item": "E", "value": 20}
    ]
    
    result = ParetoAnalyzer.analyze(data, "value", "item")
    
    assert result["total_items"] == 5
    assert result["total_value"] == 300
    assert len(result["vital_few"]) > 0
    assert result["vital_few_percentage"] > 0
    assert "pareto_insight" in result


def test_pareto_empty_data():
    """Test Pareto analysis with empty data"""
    result = ParetoAnalyzer.analyze([], "value", "item")
    
    assert result["total_items"] == 0
    assert result["vital_few_count"] == 0
    assert len(result["vital_few"]) == 0


def test_pareto_single_item():
    """Test Pareto analysis with single item"""
    data = [{"item": "A", "value": 100}]
    
    result = ParetoAnalyzer.analyze(data, "value", "item")
    
    assert result["total_items"] == 1
    assert len(result["vital_few"]) == 1
    assert result["vital_few"][0]["item"] == "A"


def test_pareto_critical_issues():
    """Test identifying critical issues"""
    issues = [
        {"issue_id": "ISSUE-1", "impact_score": 100},
        {"issue_id": "ISSUE-2", "impact_score": 80},
        {"issue_id": "ISSUE-3", "impact_score": 60},
        {"issue_id": "ISSUE-4", "impact_score": 40},
        {"issue_id": "ISSUE-5", "impact_score": 20}
    ]
    
    critical = ParetoAnalyzer.identify_critical_issues(issues)
    
    assert len(critical) > 0
    assert critical[0]["issue_id"] == "ISSUE-1"  # Highest impact first


def test_pareto_cumulative_percentage():
    """Test cumulative percentage calculation"""
    data = [
        {"item": "A", "value": 50},
        {"item": "B", "value": 30},
        {"item": "C", "value": 20}
    ]
    
    result = ParetoAnalyzer.analyze(data, "value", "item")
    
    # Check cumulative percentages
    cumulative = result["cumulative_data"]
    assert cumulative[0]["cumulative_percentage"] == 50.0
    assert cumulative[1]["cumulative_percentage"] == 80.0
    assert cumulative[2]["cumulative_percentage"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
