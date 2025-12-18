"""
Unit tests for Confluence REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from mcp.server import app


client = TestClient(app)


class TestConfluenceAPIEndpoints:
    """Test suite for Confluence API endpoints."""
    
    def test_get_spaces_success(self):
        """Test successful retrieval of Confluence spaces."""
        response = client.get("/api/confluence/spaces")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            space = data[0]
            assert "id" in space
            assert "key" in space
            assert "name" in space
            assert "type" in space
            assert "url" in space
    
    def test_get_pages_in_space_success(self):
        """Test retrieving pages in a specific space."""
        response = client.get("/api/confluence/spaces/OPS/pages")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            page = data[0]
            assert "id" in page
            assert "title" in page
            assert "space_key" in page
            assert "url" in page
    
    def test_get_pages_with_limit(self):
        """Test page retrieval with limit parameter."""
        response = client.get("/api/confluence/spaces/OPS/pages?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
    
    def test_get_pages_with_search(self):
        """Test page retrieval with search filter."""
        response = client.get("/api/confluence/spaces/OPS/pages?search=runbook")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_page_by_id(self):
        """Test retrieving a specific page by ID."""
        # First get pages to get a valid ID
        pages_response = client.get("/api/confluence/spaces/OPS/pages")
        
        if pages_response.status_code == 200:
            pages = pages_response.json()
            if len(pages) > 0:
                page_id = pages[0]["id"]
                response = client.get(f"/api/confluence/pages/{page_id}")
                
                assert response.status_code in [200, 404]
    
    def test_create_page_success(self):
        """Test creating a new Confluence page."""
        new_page = {
            "space_key": "OPS",
            "title": "Test Page from Unit Tests",
            "content": "<h1>Test Content</h1><p>This is a test page.</p>",
            "parent_id": None
        }
        
        response = client.post("/api/confluence/pages", json=new_page)
        
        assert response.status_code == 201
        created_page = response.json()
        assert created_page["title"] == new_page["title"]
        assert created_page["space_key"] == new_page["space_key"]
    
    def test_create_page_validation_error(self):
        """Test creating page with missing required fields."""
        invalid_page = {
            "space_key": "OPS"
            # Missing title and content
        }
        
        response = client.post("/api/confluence/pages", json=invalid_page)
        
        assert response.status_code == 422
    
    def test_search_pages_success(self):
        """Test searching across Confluence."""
        response = client.get("/api/confluence/search?q=production")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_pages_with_space_filter(self):
        """Test searching within a specific space."""
        response = client.get("/api/confluence/search?q=runbook&space_key=OPS")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_pages_with_limit(self):
        """Test search with result limit."""
        response = client.get("/api/confluence/search?q=test&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
    
    def test_confluence_health_check(self):
        """Test Confluence health check endpoint."""
        response = client.get("/api/confluence/health")
        
        assert response.status_code == 200
        health = response.json()
        
        assert "status" in health
        assert "mock_mode" in health
        assert "timestamp" in health


class TestConfluenceAPIErrorHandling:
    """Test error handling in Confluence API."""
    
    def test_page_not_found(self):
        """Test handling of non-existent page."""
        response = client.get("/api/confluence/pages/NONEXISTENT-999")
        
        assert response.status_code == 404
    
    def test_invalid_space_key(self):
        """Test handling of invalid space key."""
        response = client.get("/api/confluence/spaces/INVALID/pages")
        
        # Should return empty list or error
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

