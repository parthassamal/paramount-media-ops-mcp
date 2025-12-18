"""
Unit tests for Analytics REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from mcp.server import app


client = TestClient(app)


class TestAnalyticsAPIEndpoints:
    """Test suite for Analytics API endpoints."""
    
    def test_get_churn_cohorts_success(self):
        """Test successful retrieval of churn cohorts."""
        response = client.get("/api/analytics/churn/cohorts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            cohort = data[0]
            assert "cohort_name" in cohort
            assert "subscriber_count" in cohort
            assert "churn_probability" in cohort
            assert "risk_level" in cohort
            assert "primary_reason" in cohort
            assert "revenue_at_risk" in cohort
    
    def test_churn_cohorts_risk_levels(self):
        """Test that risk levels are correctly categorized."""
        response = client.get("/api/analytics/churn/cohorts")
        
        assert response.status_code == 200
        cohorts = response.json()
        
        valid_risk_levels = ["High", "Medium", "Low"]
        for cohort in cohorts:
            assert cohort["risk_level"] in valid_risk_levels
            
            # Verify risk level matches probability
            if cohort["churn_probability"] >= 0.7:
                assert cohort["risk_level"] == "High"
            elif cohort["churn_probability"] >= 0.4:
                assert cohort["risk_level"] == "Medium"
            else:
                assert cohort["risk_level"] == "Low"
    
    def test_get_ltv_analysis_success(self):
        """Test LTV analysis endpoint."""
        response = client.get("/api/analytics/ltv/analysis")
        
        assert response.status_code == 200
        ltv = response.json()
        
        assert "total_ltv_at_risk" in ltv
        assert "ltv_by_cohort" in ltv
        assert "avg_subscriber_ltv" in ltv
        
        assert isinstance(ltv["total_ltv_at_risk"], (int, float))
        assert isinstance(ltv["ltv_by_cohort"], dict)
        assert isinstance(ltv["avg_subscriber_ltv"], (int, float))
    
    def test_get_subscriber_stats_success(self):
        """Test subscriber statistics endpoint."""
        response = client.get("/api/analytics/subscribers/stats")
        
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_subscribers" in stats
        assert "high_risk_subscribers" in stats
        assert "churn_rate" in stats
        assert "total_ltv_at_risk" in stats
        assert "avg_subscriber_ltv" in stats
        assert "timestamp" in stats
        
        # Verify data types
        assert isinstance(stats["total_subscribers"], int)
        assert isinstance(stats["high_risk_subscribers"], int)
        assert isinstance(stats["churn_rate"], (int, float))
        assert stats["churn_rate"] >= 0 and stats["churn_rate"] <= 1
    
    def test_analytics_health_check(self):
        """Test Analytics health check endpoint."""
        response = client.get("/api/analytics/health")
        
        assert response.status_code == 200
        health = response.json()
        
        assert "status" in health
        assert "mock_mode" in health
        assert "timestamp" in health


class TestAnalyticsAPIDataValidation:
    """Test data validation in Analytics API."""
    
    def test_churn_probability_range(self):
        """Test that churn probabilities are within valid range (0-1)."""
        response = client.get("/api/analytics/churn/cohorts")
        
        assert response.status_code == 200
        cohorts = response.json()
        
        for cohort in cohorts:
            prob = cohort["churn_probability"]
            assert 0 <= prob <= 1, f"Invalid churn probability: {prob}"
    
    def test_subscriber_count_positive(self):
        """Test that subscriber counts are positive."""
        response = client.get("/api/analytics/churn/cohorts")
        
        assert response.status_code == 200
        cohorts = response.json()
        
        for cohort in cohorts:
            count = cohort["subscriber_count"]
            assert count > 0, f"Invalid subscriber count: {count}"
    
    def test_revenue_at_risk_positive(self):
        """Test that revenue at risk is non-negative."""
        response = client.get("/api/analytics/churn/cohorts")
        
        assert response.status_code == 200
        cohorts = response.json()
        
        for cohort in cohorts:
            revenue = cohort["revenue_at_risk"]
            assert revenue >= 0, f"Invalid revenue: {revenue}"


class TestAnalyticsAPIBusinessLogic:
    """Test business logic in Analytics API."""
    
    def test_high_risk_cohorts_identified(self):
        """Test that high-risk cohorts are properly identified."""
        response = client.get("/api/analytics/churn/cohorts")
        
        assert response.status_code == 200
        cohorts = response.json()
        
        high_risk = [c for c in cohorts if c["risk_level"] == "High"]
        
        # Should have at least one high-risk cohort in mock data
        assert len(high_risk) > 0
        
        # High-risk cohorts should have significant revenue impact
        for cohort in high_risk:
            assert cohort["revenue_at_risk"] > 0
    
    def test_pareto_principle_observable(self):
        """Test that Pareto principle (80/20) is observable in data."""
        response = client.get("/api/analytics/churn/cohorts")
        
        assert response.status_code == 200
        cohorts = response.json()
        
        if len(cohorts) >= 5:
            # Sort by revenue at risk
            sorted_cohorts = sorted(
                cohorts, 
                key=lambda x: x["revenue_at_risk"], 
                reverse=True
            )
            
            # Calculate top 20% contribution
            top_20_count = max(1, len(cohorts) // 5)
            top_20_revenue = sum(
                c["revenue_at_risk"] for c in sorted_cohorts[:top_20_count]
            )
            total_revenue = sum(c["revenue_at_risk"] for c in cohorts)
            
            if total_revenue > 0:
                top_20_percent = top_20_revenue / total_revenue
                
                # Should be close to 80% (between 60-95% is reasonable)
                assert 0.60 <= top_20_percent <= 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

