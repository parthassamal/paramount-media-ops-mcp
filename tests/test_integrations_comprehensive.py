"""
Comprehensive integration tests for all client modules.
"""
import pytest
from fastapi.testclient import TestClient
from mcp.server import app
from mcp.integrations.newrelic_client import NewRelicClient, APMMetrics, InfraMetrics
from mcp.integrations.dynatrace_client import DynatraceClient
from mcp.integrations.conviva_client import ConvivaClient
from mcp.integrations.figma_client import FigmaClient, FigmaComponent, FigmaVariable


client = TestClient(app)


class TestNewRelicClientComprehensive:
    """Comprehensive tests for NewRelic client."""
    
    def test_apm_metrics_dataclass(self):
        """Test APMMetrics dataclass."""
        metrics = APMMetrics(
            response_time_avg=245.5,
            response_time_p95=520.0,
            throughput=15420.0,
            error_rate=0.0085,
            error_count=130,
            apdex_score=0.92
        )
        
        # Test to_dict
        d = metrics.to_dict()
        assert d["response_time_avg_ms"] == 245.5
        assert d["apdex_score"] == 0.92
    
    def test_apm_metrics_health_status_healthy(self):
        """Test healthy APM metrics status."""
        metrics = APMMetrics(
            response_time_avg=100,
            error_rate=0.001,
            apdex_score=0.95
        )
        assert metrics.get_health_status() == "healthy"
    
    def test_apm_metrics_health_status_warning(self):
        """Test warning APM metrics status."""
        metrics = APMMetrics(
            response_time_avg=300,
            error_rate=0.03,  # Above threshold
            apdex_score=0.80
        )
        status = metrics.get_health_status()
        assert status in ["warning", "critical"]
    
    def test_apm_metrics_health_status_critical(self):
        """Test critical APM metrics status."""
        metrics = APMMetrics(
            response_time_avg=5000,  # Very high
            error_rate=0.15,  # Very high
            apdex_score=0.5  # Very low
        )
        assert metrics.get_health_status() == "critical"
    
    def test_infra_metrics_dataclass(self):
        """Test InfraMetrics dataclass."""
        metrics = InfraMetrics(
            cpu_percent=45.2,
            memory_percent=62.8,
            disk_percent=58.3,
            network_rx_bytes=1_500_000,
            network_tx_bytes=800_000,
            host_count=24
        )
        
        d = metrics.to_dict()
        assert d["cpu_percent"] == 45.2
        assert d["host_count"] == 24
        assert "network_rx_mbps" in d
    
    def test_infra_metrics_health_healthy(self):
        """Test healthy infrastructure status."""
        metrics = InfraMetrics(
            cpu_percent=40,
            memory_percent=50,
            disk_percent=60
        )
        assert metrics.get_health_status() == "healthy"
    
    def test_infra_metrics_health_warning(self):
        """Test warning infrastructure status."""
        metrics = InfraMetrics(
            cpu_percent=80,  # Above 75%
            memory_percent=50,
            disk_percent=60
        )
        assert metrics.get_health_status() == "warning"
    
    def test_infra_metrics_health_critical(self):
        """Test critical infrastructure status."""
        metrics = InfraMetrics(
            cpu_percent=95,  # Above 90%
            memory_percent=50,
            disk_percent=60
        )
        assert metrics.get_health_status() == "critical"
    
    def test_newrelic_client_initialization(self):
        """Test NewRelic client initialization."""
        nr = NewRelicClient(mock_mode=True)
        assert nr.mock_mode is True
    
    def test_newrelic_get_apm_metrics(self):
        """Test getting APM metrics."""
        nr = NewRelicClient(mock_mode=True)
        metrics = nr.get_apm_metrics()
        assert metrics is not None
    
    def test_newrelic_get_infrastructure_metrics(self):
        """Test getting infrastructure metrics."""
        nr = NewRelicClient(mock_mode=True)
        metrics = nr.get_infrastructure_metrics()
        assert metrics is not None
    
    def test_newrelic_get_incidents(self):
        """Test getting incidents."""
        nr = NewRelicClient(mock_mode=True)
        incidents = nr.get_incidents()
        assert isinstance(incidents, (list, dict))
    
    def test_newrelic_get_operational_health_summary(self):
        """Test getting operational health summary."""
        nr = NewRelicClient(mock_mode=True)
        summary = nr.get_operational_health_summary()
        assert isinstance(summary, dict)


class TestDynatraceClientComprehensive:
    """Comprehensive tests for Dynatrace client."""
    
    def test_all_mock_methods_return_data(self):
        """Test all mock methods return valid data."""
        dt = DynatraceClient()
        
        # Application metrics
        app = dt.get_application_metrics()
        assert isinstance(app, dict)
        assert "applications" in app or "overall" in app
        
        # Infrastructure health
        infra = dt.get_infrastructure_health()
        assert isinstance(infra, dict)
        
        # Problems
        problems = dt.get_problems()
        assert isinstance(problems, dict)
        
        # Service health
        services = dt.get_service_health()
        assert isinstance(services, dict)
        
        # User experience
        ux = dt.get_user_experience()
        assert isinstance(ux, dict)
    
    def test_problems_filtering(self):
        """Test problems filtering by state."""
        dt = DynatraceClient()
        
        open_problems = dt.get_problems(state="OPEN")
        all_problems = dt.get_problems(state="ALL")
        
        assert isinstance(open_problems, dict)
        assert isinstance(all_problems, dict)
    
    def test_mock_data_has_realistic_values(self):
        """Test mock data has realistic values."""
        dt = DynatraceClient()
        app = dt.get_application_metrics()
        
        # Check overall metrics exist
        if "overall" in app:
            assert app["overall"]["response_time_avg_ms"] > 0
            assert 0 <= app["overall"]["error_rate"] <= 1
            assert 0 <= app["overall"]["apdex_score"] <= 1


class TestConvivaClientComprehensive:
    """Comprehensive tests for Conviva client."""
    
    def test_initialization(self):
        """Test Conviva client initialization."""
        conviva = ConvivaClient(mock_mode=True)
        assert conviva.mock_mode is True
    
    def test_get_qoe_metrics(self):
        """Test getting QoE metrics."""
        conviva = ConvivaClient(mock_mode=True)
        metrics = conviva.get_qoe_metrics()
        assert isinstance(metrics, dict)
    
    def test_get_buffering_hotspots(self):
        """Test getting buffering hotspots."""
        conviva = ConvivaClient(mock_mode=True)
        hotspots = conviva.get_buffering_hotspots()
        assert isinstance(hotspots, (list, dict))


class TestFigmaClientComprehensive:
    """Comprehensive tests for Figma client."""
    
    def test_figma_component_dataclass(self):
        """Test FigmaComponent dataclass."""
        component = FigmaComponent(
            key="comp-123",
            name="Button",
            description="Primary button"
        )
        assert component.name == "Button"
        assert component.key == "comp-123"
    
    def test_figma_variable_dataclass(self):
        """Test FigmaVariable dataclass."""
        variable = FigmaVariable(
            id="var-123",
            name="primary-color",
            resolved_type="COLOR",
            value_by_mode={"default": "#0066FF"}
        )
        
        # Test basic properties
        assert variable.name == "primary-color"
        assert variable.id == "var-123"
    
    def test_figma_client_all_methods(self):
        """Test all Figma client methods in mock mode."""
        figma = FigmaClient(mock_mode=True)
        
        # Design tokens
        tokens = figma.get_design_tokens(file_id="test")
        assert isinstance(tokens, dict)
        
        # Dashboard design system
        system = figma.get_dashboard_design_system()
        assert isinstance(system, dict)
        
        # File components
        components = figma.get_file_components(file_id="test")
        assert isinstance(components, list)
        
        # File styles
        styles = figma.get_file_styles(file_id="test")
        assert isinstance(styles, dict)
        
        # Local variables
        variables = figma.get_local_variables(file_id="test")
        assert isinstance(variables, list)
        
        # CSS variables export
        css = figma.export_to_css_variables(file_id="test")
        assert isinstance(css, str)


class TestStreamingAPIEndpoints:
    """Test streaming API endpoints comprehensively."""
    
    def test_qoe_metrics_endpoint(self):
        """Test QoE metrics endpoint."""
        response = client.get("/api/streaming/qoe/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))
    
    def test_buffering_hotspots_endpoint(self):
        """Test buffering hotspots endpoint."""
        response = client.get("/api/streaming/qoe/buffering-hotspots")
        assert response.status_code == 200
    
    def test_service_health_endpoint(self):
        """Test service health endpoint."""
        response = client.get("/api/streaming/infrastructure/services")
        assert response.status_code == 200
    
    def test_incidents_endpoint(self):
        """Test incidents endpoint."""
        response = client.get("/api/streaming/infrastructure/incidents")
        assert response.status_code == 200
    
    def test_operational_health_endpoint(self):
        """Test operational health endpoint."""
        response = client.get("/api/streaming/infrastructure/operational-health")
        assert response.status_code == 200
    
    def test_streaming_health_check(self):
        """Test streaming health check."""
        response = client.get("/api/streaming/health")
        assert response.status_code == 200


class TestMCPProtocolEndpoints:
    """Test MCP protocol endpoints."""
    
    def test_list_resources_endpoint(self):
        """Test list resources endpoint."""
        response = client.get("/resources")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_tools_endpoint(self):
        """Test list tools endpoint."""
        response = client.get("/tools")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestCrossIntegrationConsistency:
    """Test consistency across integrations."""
    
    def test_all_clients_have_consistent_interface(self):
        """Test all clients follow consistent patterns."""
        nr = NewRelicClient(mock_mode=True)
        dt = DynatraceClient()
        conviva = ConvivaClient(mock_mode=True)
        figma = FigmaClient(mock_mode=True)
        
        # All should be able to return data without errors
        assert nr.get_apm_metrics() is not None
        assert dt.get_application_metrics() is not None
        assert conviva.get_qoe_metrics() is not None
        assert figma.get_dashboard_design_system() is not None

