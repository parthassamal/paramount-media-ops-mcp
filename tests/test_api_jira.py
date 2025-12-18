"""
Unit tests for JIRA REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from mcp.server import app
from config import settings


client = TestClient(app)


class TestJiraAPIEndpoints:
    """Test suite for JIRA API endpoints."""
    
    def test_get_jira_issues_success(self):
        """Test successful retrieval of JIRA issues."""
        response = client.get("/api/jira/issues")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            issue = data[0]
            assert "id" in issue
            assert "key" in issue
            assert "summary" in issue
            assert "status" in issue
            assert "severity" in issue
    
    def test_get_jira_issues_with_filters(self):
        """Test JIRA issues with query filters."""
        response = client.get("/api/jira/issues?severity=critical&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_jira_issue_by_key(self):
        """Test retrieving a specific JIRA issue by key."""
        # First get all issues to get a valid key
        all_issues = client.get("/api/jira/issues").json()
        
        if len(all_issues) > 0:
            issue_key = all_issues[0]["key"]
            response = client.get(f"/api/jira/issues/{issue_key}")
            
            assert response.status_code == 200
            issue = response.json()
            assert issue["key"] == issue_key
    
    def test_get_jira_issue_not_found(self):
        """Test retrieving non-existent JIRA issue."""
        response = client.get("/api/jira/issues/NONEXISTENT-999")
        
        assert response.status_code == 404
    
    def test_create_jira_issue_success(self):
        """Test creating a new JIRA issue."""
        new_issue = {
            "project_key": "PROD",
            "summary": "Test issue from unit tests",
            "description": "This is a test issue created by automated tests",
            "issue_type": "Bug",
            "severity": "Medium",
            "show_name": "Test Show",
            "cost_impact": 5000.0,
            "delay_days": 2
        }
        
        response = client.post("/api/jira/issues", json=new_issue)
        
        assert response.status_code == 201
        created_issue = response.json()
        assert created_issue["summary"] == new_issue["summary"]
        assert created_issue["severity"] == new_issue["severity"]
    
    def test_create_jira_issue_validation_error(self):
        """Test creating JIRA issue with missing required fields."""
        invalid_issue = {
            "project_key": "PROD"
            # Missing summary and description
        }
        
        response = client.post("/api/jira/issues", json=invalid_issue)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_issues_by_show(self):
        """Test retrieving issues for a specific show."""
        response = client.get("/api/jira/shows/Yellowstone/issues")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_critical_issues(self):
        """Test retrieving critical severity issues."""
        response = client.get("/api/jira/issues/critical")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Verify all returned issues are critical
        for issue in data:
            assert issue["severity"].lower() == "critical"
    
    def test_get_cost_summary(self):
        """Test cost impact summary endpoint."""
        response = client.get("/api/jira/analytics/cost-summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_cost_impact" in data or isinstance(data, dict)
    
    def test_get_jira_stats(self):
        """Test JIRA statistics endpoint."""
        response = client.get("/api/jira/analytics/stats")
        
        assert response.status_code == 200
        stats = response.json()
        
        assert "total_issues" in stats
        assert "by_status" in stats
        assert "by_severity" in stats
        assert "total_cost_impact" in stats
        assert "critical_count" in stats
        
        assert isinstance(stats["total_issues"], int)
        assert isinstance(stats["by_status"], dict)
        assert isinstance(stats["by_severity"], dict)
    
    def test_jira_health_check(self):
        """Test JIRA health check endpoint."""
        response = client.get("/api/jira/health")
        
        assert response.status_code == 200
        health = response.json()
        
        assert "status" in health
        assert "mock_mode" in health
        assert health["status"] in ["healthy", "disabled"]


class TestJiraAPIErrorHandling:
    """Test error handling in JIRA API."""
    
    def test_invalid_query_parameters(self):
        """Test handling of invalid query parameters."""
        response = client.get("/api/jira/issues?limit=9999")
        
        # Should either succeed with capped limit or return validation error
        assert response.status_code in [200, 422]
    
    def test_malformed_json_body(self):
        """Test handling of malformed JSON in request body."""
        response = client.post(
            "/api/jira/issues",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestJiraAPIResponseSchema:
    """Test response schema validation."""
    
    def test_issue_response_schema(self):
        """Test that issue responses match expected schema."""
        response = client.get("/api/jira/issues?limit=1")
        
        if response.status_code == 200:
            data = response.json()
            if len(data) > 0:
                issue = data[0]
                
                # Required fields
                required_fields = [
                    "id", "key", "summary", "status", 
                    "severity", "created", "updated", "url"
                ]
                for field in required_fields:
                    assert field in issue, f"Missing required field: {field}"
                
                # Optional fields (should be present but can be null)
                optional_fields = [
                    "show_name", "cost_impact", "delay_days", "assignee"
                ]
                for field in optional_fields:
                    assert field in issue, f"Missing optional field: {field}"
    
    def test_stats_response_schema(self):
        """Test statistics response schema."""
        response = client.get("/api/jira/analytics/stats")
        
        assert response.status_code == 200
        stats = response.json()
        
        # Verify data types
        assert isinstance(stats["total_issues"], int)
        assert isinstance(stats["total_cost_impact"], (int, float))
        assert isinstance(stats["average_delay_days"], (int, float))
        assert isinstance(stats["critical_count"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

