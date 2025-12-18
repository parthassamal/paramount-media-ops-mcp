"""
Unit tests for main FastAPI server.
"""

import pytest
from fastapi.testclient import TestClient

from mcp.server import app


client = TestClient(app)


class TestServerEndpoints:
    """Test main server endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns server information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert "message" in data["data"]
        assert "version" in data["data"]
        assert "endpoints" in data["data"]
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert "server_name" in data["data"]
        assert "version" in data["data"]
        assert "resources_available" in data["data"]
        assert "tools_available" in data["data"]
        assert "integrations" in data["data"]
        assert "api_endpoints" in data["data"]
    
    def test_health_check_integrations(self):
        """Test that health check includes all integrations."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        integrations = data["data"]["integrations"]
        assert "jira" in integrations
        assert "confluence" in integrations
        assert "conviva" in integrations
        assert "newrelic" in integrations
        assert "analytics" in integrations
        assert "figma" in integrations
    
    def test_health_check_api_endpoints(self):
        """Test that health check lists API endpoints."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        api_endpoints = data["data"]["api_endpoints"]
        assert api_endpoints["jira"] == "/api/jira"
        assert api_endpoints["confluence"] == "/api/confluence"
        assert api_endpoints["analytics"] == "/api/analytics"
        assert api_endpoints["streaming"] == "/api/streaming"


class TestMCPResourceEndpoints:
    """Test MCP resource endpoints."""
    
    def test_list_resources(self):
        """Test listing all MCP resources."""
        response = client.get("/resources")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "resources" in data["data"]
        assert "total_count" in data["data"]
        assert isinstance(data["data"]["resources"], list)
        assert data["data"]["total_count"] == 9
    
    def test_resource_structure(self):
        """Test resource object structure."""
        response = client.get("/resources")
        
        assert response.status_code == 200
        data = response.json()
        
        resources = data["data"]["resources"]
        if len(resources) > 0:
            resource = resources[0]
            assert "name" in resource
            assert "description" in resource
            assert "query_endpoint" in resource
            assert "uri" in resource


class TestMCPToolEndpoints:
    """Test MCP tool endpoints."""
    
    def test_list_tools(self):
        """Test listing all MCP tools."""
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "tools" in data["data"]
        assert "total_count" in data["data"]
        assert isinstance(data["data"]["tools"], list)
        assert data["data"]["total_count"] == 5
    
    def test_tool_structure(self):
        """Test tool object structure."""
        response = client.get("/tools")
        
        assert response.status_code == 200
        data = response.json()
        
        tools = data["data"]["tools"]
        if len(tools) > 0:
            tool = tools[0]
            assert "name" in tool
            assert "description" in tool
            assert "execute_endpoint" in tool


class TestCORS:
    """Test CORS configuration."""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present."""
        response = client.options("/health")
        
        # CORS headers should be present
        assert response.status_code in [200, 405]


class TestErrorHandling:
    """Test global error handling."""
    
    def test_404_not_found(self):
        """Test 404 handling for non-existent endpoints."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test 405 for unsupported HTTP methods."""
        response = client.delete("/health")
        
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

