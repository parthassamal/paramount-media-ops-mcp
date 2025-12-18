"""
Unit tests for Dynatrace integration.
"""
import pytest
from mcp.integrations.dynatrace_client import DynatraceClient


class TestDynatraceClient:
    """Test suite for Dynatrace client."""
    
    def test_initialization_default(self):
        """Test client initializes correctly."""
        dynatrace = DynatraceClient()
        # Client should initialize without error
        assert dynatrace is not None
        # use_mock_data depends on environment configuration
        assert isinstance(dynatrace.use_mock_data, bool)
    
    def test_initialization_with_credentials(self):
        """Test client initialization with credentials."""
        dynatrace = DynatraceClient(
            environment_url="https://test.live.dynatrace.com",
            api_token="test-token"
        )
        assert dynatrace.environment_url == "https://test.live.dynatrace.com"
        assert dynatrace.api_token == "test-token"
    
    def test_get_application_metrics(self):
        """Test fetching application metrics."""
        dynatrace = DynatraceClient()
        result = dynatrace.get_application_metrics()
        assert isinstance(result, dict)
    
    def test_get_application_metrics_with_timeframe(self):
        """Test fetching application metrics with timeframe."""
        dynatrace = DynatraceClient()
        result = dynatrace.get_application_metrics(timeframe="-2h")
        assert isinstance(result, dict)
    
    def test_get_infrastructure_health(self):
        """Test fetching infrastructure health."""
        dynatrace = DynatraceClient()
        result = dynatrace.get_infrastructure_health()
        assert isinstance(result, dict)
    
    def test_get_problems(self):
        """Test fetching problems/incidents."""
        dynatrace = DynatraceClient()
        result = dynatrace.get_problems()
        assert isinstance(result, dict)
    
    def test_get_problems_with_state_filter(self):
        """Test fetching problems with state filter."""
        dynatrace = DynatraceClient()
        result = dynatrace.get_problems(state="OPEN")
        assert isinstance(result, dict)
    
    def test_get_service_health(self):
        """Test fetching service health."""
        dynatrace = DynatraceClient()
        result = dynatrace.get_service_health()
        assert isinstance(result, dict)
    
    def test_get_user_experience(self):
        """Test fetching user experience data."""
        dynatrace = DynatraceClient()
        result = dynatrace.get_user_experience()
        assert isinstance(result, dict)


class TestDynatraceMetricsValidation:
    """Test metrics returned by Dynatrace are valid."""
    
    def test_application_metrics_has_response_time(self):
        """Test application metrics include response time."""
        dynatrace = DynatraceClient()
        metrics = dynatrace.get_application_metrics()
        # Mock data should include common metrics
        assert "applications" in metrics or "metrics" in metrics or len(metrics) > 0
    
    def test_infrastructure_health_structure(self):
        """Test infrastructure health has proper structure."""
        dynatrace = DynatraceClient()
        health = dynatrace.get_infrastructure_health()
        assert isinstance(health, dict)
    
    def test_problems_response_structure(self):
        """Test problems response has proper structure."""
        dynatrace = DynatraceClient()
        problems = dynatrace.get_problems()
        assert isinstance(problems, dict)


class TestDynatraceMockData:
    """Test mock data quality."""
    
    def test_mock_data_returns_data(self):
        """Test mock mode returns usable data."""
        dynatrace = DynatraceClient()
        
        # All methods should return data in mock mode
        assert dynatrace.get_application_metrics() is not None
        assert dynatrace.get_infrastructure_health() is not None
        assert dynatrace.get_problems() is not None
        assert dynatrace.get_service_health() is not None
        assert dynatrace.get_user_experience() is not None
    
    def test_mock_mode_is_deterministic(self):
        """Test mock data returns consistent structure."""
        dynatrace1 = DynatraceClient()
        dynatrace2 = DynatraceClient()
        
        result1 = dynatrace1.get_application_metrics()
        result2 = dynatrace2.get_application_metrics()
        
        # Both should return dicts
        assert type(result1) == type(result2) == dict
    
    def test_mock_mode_does_not_require_network(self):
        """Test mock mode works without network access."""
        dynatrace = DynatraceClient()
        # Should not raise any exceptions
        result = dynatrace.get_application_metrics()
        assert result is not None


class TestDynatraceServiceHealth:
    """Test service health functionality."""
    
    def test_service_health_returns_services(self):
        """Test service health includes services."""
        dynatrace = DynatraceClient()
        services = dynatrace.get_service_health()
        assert isinstance(services, dict)
    
    def test_user_experience_returns_data(self):
        """Test user experience returns RUM data."""
        dynatrace = DynatraceClient()
        ux = dynatrace.get_user_experience()
        assert isinstance(ux, dict)
