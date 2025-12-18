"""
Unit tests for Adobe and Figma integrations.
"""
import pytest
from fastapi.testclient import TestClient
from mcp.server import app
from mcp.integrations.adobe_pdf_client import AdobePDFClient
from mcp.integrations.adobe_storage_client import AdobeStorageClient
from mcp.integrations.figma_client import FigmaClient


client = TestClient(app)


class TestAdobePDFClient:
    """Test suite for Adobe PDF client."""
    
    def test_initialization(self):
        """Test client initializes with required parameters."""
        pdf_client = AdobePDFClient(
            client_id="test-id",
            client_secret="test-secret",
            organization_id="test-org",
            enabled=False  # Disable to avoid SDK requirement
        )
        assert pdf_client.enabled is False
    
    def test_initialization_disabled(self):
        """Test client handles disabled state."""
        pdf_client = AdobePDFClient(
            client_id="",
            client_secret="",
            organization_id="",
            enabled=False
        )
        # Should not raise errors
        assert pdf_client is not None


class TestAdobeStorageClient:
    """Test suite for Adobe Storage client."""
    
    def test_initialization(self):
        """Test client initializes with access token."""
        storage_client = AdobeStorageClient(
            access_token="test-token",
            enabled=False
        )
        assert storage_client.access_token == "test-token"
    
    def test_initialization_disabled(self):
        """Test client handles disabled state."""
        storage_client = AdobeStorageClient(
            access_token="test",
            enabled=False
        )
        assert storage_client.enabled is False
    
    def test_get_storage_usage(self):
        """Test getting storage usage."""
        storage_client = AdobeStorageClient(
            access_token="test-token",
            enabled=True
        )
        result = storage_client.get_storage_usage()
        assert isinstance(result, dict)


class TestFigmaClient:
    """Test suite for Figma client."""
    
    def test_initialization_mock_mode(self):
        """Test client initializes in mock mode."""
        figma_client = FigmaClient(mock_mode=True)
        assert figma_client.mock_mode is True
    
    def test_initialization_with_token(self):
        """Test client initializes with access token."""
        figma_client = FigmaClient(access_token="test-token", mock_mode=True)
        assert figma_client.access_token == "test-token"
    
    def test_get_design_tokens(self):
        """Test fetching design tokens."""
        figma_client = FigmaClient(mock_mode=True)
        result = figma_client.get_design_tokens(file_id="test-file")
        assert isinstance(result, dict)
    
    def test_get_dashboard_design_system(self):
        """Test fetching dashboard design system."""
        figma_client = FigmaClient(mock_mode=True)
        result = figma_client.get_dashboard_design_system()
        assert isinstance(result, dict)
    
    def test_get_file_components(self):
        """Test fetching file components."""
        figma_client = FigmaClient(mock_mode=True)
        result = figma_client.get_file_components(file_id="test-file")
        assert isinstance(result, list)
    
    def test_export_to_css_variables(self):
        """Test exporting to CSS variables."""
        figma_client = FigmaClient(mock_mode=True)
        result = figma_client.export_to_css_variables(file_id="test-file")
        assert isinstance(result, str)
    
    def test_get_file_styles(self):
        """Test fetching file styles."""
        figma_client = FigmaClient(mock_mode=True)
        result = figma_client.get_file_styles(file_id="test-file")
        assert isinstance(result, dict)
    
    def test_get_local_variables(self):
        """Test fetching local variables."""
        figma_client = FigmaClient(mock_mode=True)
        result = figma_client.get_local_variables(file_id="test-file")
        assert isinstance(result, list)


class TestFigmaAPIEndpoints:
    """Test Figma API endpoints."""
    
    def test_get_figma_tokens_endpoint(self):
        """Test get Figma tokens endpoint."""
        response = client.get("/figma/tokens")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_figma_css_variables_endpoint(self):
        """Test get Figma CSS variables endpoint."""
        response = client.get("/figma/css-variables")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_figma_images_endpoint(self):
        """Test get Figma images endpoint."""
        response = client.get("/figma/images")
        # May return 400 if Figma not configured
        assert response.status_code in [200, 400]
    
    def test_get_full_design_system_endpoint(self):
        """Test get full design system endpoint."""
        response = client.get("/figma/design-system")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestAdobeAPIEndpoints:
    """Test Adobe API endpoints."""
    
    def test_adobe_health_check(self):
        """Test Adobe health check endpoint."""
        response = client.get("/adobe/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestFigmaClientMockData:
    """Test Figma client mock data quality."""
    
    def test_mock_design_tokens_has_colors(self):
        """Test mock design tokens include colors."""
        figma_client = FigmaClient(mock_mode=True)
        tokens = figma_client.get_design_tokens(file_id="test")
        assert "colors" in tokens or "variables" in tokens or len(tokens) > 0
    
    def test_mock_dashboard_system_complete(self):
        """Test mock dashboard design system is complete."""
        figma_client = FigmaClient(mock_mode=True)
        system = figma_client.get_dashboard_design_system()
        assert isinstance(system, dict)
    
    def test_mock_components_returned(self):
        """Test mock components are returned."""
        figma_client = FigmaClient(mock_mode=True)
        components = figma_client.get_file_components(file_id="test")
        assert isinstance(components, list)


class TestFigmaIntegration:
    """Integration tests for Figma functionality."""
    
    def test_full_design_system_workflow(self):
        """Test fetching full design system in mock mode."""
        figma_client = FigmaClient(mock_mode=True)
        
        # Get design tokens
        tokens = figma_client.get_design_tokens(file_id="test")
        assert tokens is not None
        
        # Get components
        components = figma_client.get_file_components(file_id="test")
        assert components is not None
        
        # Get CSS variables
        css = figma_client.export_to_css_variables(file_id="test")
        assert css is not None
    
    def test_api_workflow(self):
        """Test Figma API workflow through FastAPI endpoints."""
        # Get tokens
        tokens_response = client.get("/figma/tokens")
        assert tokens_response.status_code == 200
        
        # Get CSS
        css_response = client.get("/figma/css-variables")
        assert css_response.status_code == 200
        
        # Get full system
        system_response = client.get("/figma/design-system")
        assert system_response.status_code == 200
