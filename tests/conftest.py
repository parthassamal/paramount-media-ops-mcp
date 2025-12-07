"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_cohorts():
    """Sample churn cohorts for testing."""
    return [
        {
            "cohort_id": "TEST-001",
            "name": "Test Cohort",
            "size": 1000,
            "churn_risk_score": 0.8,
            "financial_impact_30d": 100000
        }
    ]


@pytest.fixture
def sample_issues():
    """Sample production issues for testing."""
    return [
        {
            "issue_id": "ISSUE-001",
            "title": "Test Issue",
            "delay_days": 10,
            "cost_overrun": 50000,
            "severity": "high"
        }
    ]


@pytest.fixture
def sample_themes():
    """Sample complaint themes for testing."""
    return [
        {
            "theme_id": "THEME-001",
            "name": "Test Theme",
            "complaint_volume": 500,
            "churn_correlation": 0.6,
            "is_fixable": True
        }
    ]
