"""Tests for Mock Data Generator"""
import pytest
from src.mock_data import MockDataGenerator


def test_generate_churn_cohort():
    """Test churn cohort generation"""
    cohort = MockDataGenerator.generate_churn_cohort(50)
    
    assert len(cohort) == 50
    assert all("user_id" in user for user in cohort)
    assert all("churn_risk_score" in user for user in cohort)
    assert all(0 <= user["churn_risk_score"] <= 1 for user in cohort)


def test_generate_production_issues():
    """Test production issues generation"""
    issues = MockDataGenerator.generate_production_issues(30)
    
    assert len(issues) == 30
    assert all("issue_id" in issue for issue in issues)
    assert all("impact_score" in issue for issue in issues)
    assert all("severity" in issue for issue in issues)


def test_generate_complaint_themes():
    """Test complaint themes generation"""
    complaints = MockDataGenerator.generate_complaint_themes(40)
    
    assert len(complaints) == 40
    assert all("complaint_id" in c for c in complaints)
    assert all("topic" in c for c in complaints)
    assert all("sentiment_score" in c for c in complaints)
    assert all(-1 <= c["sentiment_score"] <= 1 for c in complaints)


def test_generate_content_catalog():
    """Test content catalog generation"""
    catalog = MockDataGenerator.generate_content_catalog(25)
    
    assert len(catalog) == 25
    assert all("content_id" in item for item in catalog)
    assert all("title" in item for item in catalog)
    assert all("roi" in item for item in catalog)


def test_data_consistency():
    """Test that generated data is consistent"""
    # Generate multiple times and check structure consistency
    cohort1 = MockDataGenerator.generate_churn_cohort(10)
    cohort2 = MockDataGenerator.generate_churn_cohort(10)
    
    assert set(cohort1[0].keys()) == set(cohort2[0].keys())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
