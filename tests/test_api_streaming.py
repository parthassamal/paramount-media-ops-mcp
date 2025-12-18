"""
Unit tests for Streaming QoE and Infrastructure REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from mcp.server import app


client = TestClient(app)


class TestStreamingQoEEndpoints:
    """Test suite for Streaming QoE API endpoints."""
    
    def test_get_qoe_metrics_success(self):
        """Test successful retrieval of QoE metrics."""
        response = client.get("/api/streaming/qoe/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            metric = data[0]
            assert "metric_name" in metric
            assert "value" in metric
            assert "threshold" in metric
            assert "status" in metric
            assert "unit" in metric
    
    def test_qoe_metrics_with_filters(self):
        """Test QoE metrics with dimension filters."""
        response = client.get("/api/streaming/qoe/metrics?dimension=device&time_range=1")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_qoe_metric_statuses(self):
        """Test that QoE metric statuses are valid."""
        response = client.get("/api/streaming/qoe/metrics")
        
        assert response.status_code == 200
        metrics = response.json()
        
        valid_statuses = ["good", "warning", "critical"]
        for metric in metrics:
            assert metric["status"] in valid_statuses
    
    def test_get_buffering_hotspots_success(self):
        """Test buffering hotspots analysis."""
        response = client.get("/api/streaming/qoe/buffering-hotspots")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_buffering_hotspots_with_time_range(self):
        """Test buffering hotspots with custom time range."""
        response = client.get("/api/streaming/qoe/buffering-hotspots?time_range=12")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestInfrastructureEndpoints:
    """Test suite for Infrastructure API endpoints."""
    
    def test_get_service_health_success(self):
        """Test service health endpoint."""
        response = client.get("/api/streaming/infrastructure/services")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            service = data[0]
            assert "service_name" in service
            assert "status" in service
            assert "response_time_ms" in service
            assert "error_rate" in service
            assert "throughput_rpm" in service
    
    def test_service_health_statuses(self):
        """Test that service health statuses are valid."""
        response = client.get("/api/streaming/infrastructure/services")
        
        assert response.status_code == 200
        services = response.json()
        
        valid_statuses = ["healthy", "degraded", "critical"]
        for service in services:
            assert service["status"] in valid_statuses
    
    def test_get_incidents_success(self):
        """Test incidents endpoint."""
        response = client.get("/api/streaming/infrastructure/incidents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)  # Returns dict, not list
        if "incidents" in data:
            assert isinstance(data["incidents"], list)
    
    def test_get_operational_health_success(self):
        """Test operational health summary."""
        response = client.get("/api/streaming/infrastructure/operational-health")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_streaming_health_check(self):
        """Test streaming APIs health check."""
        response = client.get("/api/streaming/health")
        
        assert response.status_code == 200
        health = response.json()
        
        assert "conviva" in health
        assert "newrelic" in health
        assert "timestamp" in health


class TestStreamingAPIDataValidation:
    """Test data validation in Streaming API."""
    
    def test_response_time_positive(self):
        """Test that response times are positive."""
        response = client.get("/api/streaming/infrastructure/services")
        
        assert response.status_code == 200
        services = response.json()
        
        for service in services:
            rt = service["response_time_ms"]
            assert rt >= 0, f"Invalid response time: {rt}"
    
    def test_error_rate_range(self):
        """Test that error rates are within valid range (0-1)."""
        response = client.get("/api/streaming/infrastructure/services")
        
        assert response.status_code == 200
        services = response.json()
        
        for service in services:
            err_rate = service["error_rate"]
            assert 0 <= err_rate <= 1, f"Invalid error rate: {err_rate}"
    
    def test_throughput_positive(self):
        """Test that throughput is non-negative."""
        response = client.get("/api/streaming/infrastructure/services")
        
        assert response.status_code == 200
        services = response.json()
        
        for service in services:
            throughput = service["throughput_rpm"]
            assert throughput >= 0, f"Invalid throughput: {throughput}"


class TestStreamingAPIQueryParameters:
    """Test query parameter handling."""
    
    def test_time_range_validation(self):
        """Test time range parameter validation."""
        # Valid range
        response = client.get("/api/streaming/qoe/metrics?time_range=24")
        assert response.status_code == 200
        
        # Invalid range (too large)
        response = client.get("/api/streaming/qoe/metrics?time_range=999")
        # Should either clamp to max or return validation error
        assert response.status_code in [200, 422]
    
    def test_dimension_filter(self):
        """Test dimension filter parameter."""
        valid_dimensions = ["device", "cdn", "geo", "content"]
        
        for dimension in valid_dimensions:
            response = client.get(f"/api/streaming/qoe/metrics?dimension={dimension}")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

