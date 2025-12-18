"""
Figma Design System Integration Client.

Connects to Figma's REST API and leverages Enterprise features:
- Design tokens extraction (colors, typography, spacing)
- Component library access
- Variables API (Enterprise)
- File versioning and branching
- Comments and annotations
- Design system analytics

Enterprise Features: https://www.figma.com/enterprise/
Figma MCP: https://www.figma.com/ - connects Figma to AI coding tools

API Documentation: https://www.figma.com/developers/api
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog
import httpx

from config import settings

logger = structlog.get_logger()


@dataclass
class FigmaColor:
    """Represents a Figma color token."""
    name: str
    hex_value: str
    rgba: Dict[str, float]
    opacity: float = 1.0
    description: str = ""
    
    def to_css(self) -> str:
        """Convert to CSS rgba value."""
        r = int(self.rgba.get('r', 0) * 255)
        g = int(self.rgba.get('g', 0) * 255)
        b = int(self.rgba.get('b', 0) * 255)
        return f"rgba({r}, {g}, {b}, {self.opacity})"


@dataclass
class FigmaTypography:
    """Represents a Figma typography style."""
    name: str
    font_family: str
    font_size: float
    font_weight: int
    line_height: float
    letter_spacing: float = 0.0
    description: str = ""
    
    def to_css(self) -> Dict[str, str]:
        """Convert to CSS properties."""
        return {
            "font-family": f"'{self.font_family}', sans-serif",
            "font-size": f"{self.font_size}px",
            "font-weight": str(self.font_weight),
            "line-height": f"{self.line_height}px",
            "letter-spacing": f"{self.letter_spacing}px"
        }


@dataclass
class FigmaComponent:
    """Represents a Figma component."""
    key: str
    name: str
    description: str = ""
    component_set_id: Optional[str] = None
    containing_frame: Optional[str] = None
    thumbnail_url: Optional[str] = None


@dataclass
class FigmaVariable:
    """Represents a Figma variable (Enterprise feature)."""
    id: str
    name: str
    resolved_type: str  # COLOR, FLOAT, STRING, BOOLEAN
    value_by_mode: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    collection_id: str = ""


class FigmaClient:
    """
    Figma Design System Integration Client.
    
    Provides access to Figma's REST API for design system integration,
    component libraries, and design token extraction.
    
    Enterprise Features:
    - Variables API for design tokens
    - Branching and version control
    - Design system analytics
    - Team libraries
    
    Example:
        >>> client = FigmaClient()
        >>> tokens = client.get_design_tokens("file-id")
        >>> print(tokens["colors"][0].hex_value)
        "#0066FF"
    """
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        mock_mode: Optional[bool] = None
    ):
        """
        Initialize Figma client.
        
        Args:
            access_token: Figma Personal Access Token (optional, uses settings if not provided)
            mock_mode: Use mock data instead of real API (optional, uses settings if not provided)
        """
        self.access_token = access_token or settings.figma_access_token
        self.mock_mode = mock_mode if mock_mode is not None else settings.mock_mode
        self.base_url = "https://api.figma.com/v1"
        self.timeout = settings.figma_request_timeout
        
        logger.info(
            "figma_client_initialized",
            mode="mock" if self.mock_mode else "live",
            has_token=bool(self.access_token)
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers."""
        return {
            "X-Figma-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    async def _make_request_async(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make async API request to Figma."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error("figma_api_error", endpoint=endpoint, error=str(e))
            raise
    
    def _make_request_sync(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous wrapper for API requests."""
        return asyncio.get_event_loop().run_until_complete(
            self._make_request_async(endpoint, method, params)
        )
    
    # =========================================================================
    # File Operations
    # =========================================================================
    
    def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        Get Figma file data.
        
        Args:
            file_id: Figma file ID
        
        Returns:
            File data including document structure
        """
        if self.mock_mode:
            return self._get_mock_file(file_id)
        
        return self._make_request_sync(f"files/{file_id}")
    
    def get_file_components(self, file_id: str) -> List[FigmaComponent]:
        """
        Get all components from a Figma file.
        
        Args:
            file_id: Figma file ID
        
        Returns:
            List of FigmaComponent objects
        """
        if self.mock_mode:
            return self._get_mock_components()
        
        response = self._make_request_sync(f"files/{file_id}/components")
        components = []
        
        for meta in response.get("meta", {}).get("components", []):
            components.append(FigmaComponent(
                key=meta.get("key", ""),
                name=meta.get("name", ""),
                description=meta.get("description", ""),
                component_set_id=meta.get("component_set_id"),
                containing_frame=meta.get("containing_frame", {}).get("name"),
                thumbnail_url=meta.get("thumbnail_url")
            ))
        
        return components
    
    def get_file_styles(self, file_id: str) -> Dict[str, Any]:
        """
        Get all styles (colors, typography, effects) from a Figma file.
        
        Args:
            file_id: Figma file ID
        
        Returns:
            Dictionary of styles by type
        """
        if self.mock_mode:
            return self._get_mock_styles()
        
        return self._make_request_sync(f"files/{file_id}/styles")
    
    # =========================================================================
    # Image Operations
    # =========================================================================
    
    def get_images(self, file_id: str, ids: str, format: str = "png", scale: float = 1.0) -> Dict[str, str]:
        """
        Get URLs for images exported from Figma nodes.
        
        Args:
            file_id: Figma file ID
            ids: Comma-separated list of node IDs to export
            format: "png", "jpg", "svg", or "pdf"
            scale: Image scale (1 to 4)
            
        Returns:
            Dictionary mapping node IDs to image URLs
        """
        if self.mock_mode:
            return {id: "https://figma.com/sample-image.png" for id in ids.split(",")}
            
        response = self._make_request_sync(
            f"images/{file_id}",
            params={"ids": ids, "format": format, "scale": scale}
        )
        return response.get("images", {})

    # =========================================================================
    # Design Tokens
    # =========================================================================
    
    def get_design_tokens(self, file_id: str) -> Dict[str, Any]:
        """
        Extract design tokens from a Figma file.
        
        This extracts colors, typography, spacing, and other design tokens
        that can be used to generate CSS variables or design system documentation.
        
        Args:
            file_id: Figma file ID
        
        Returns:
            Dictionary with colors, typography, spacing tokens
        """
        if self.mock_mode:
            return self._get_mock_design_tokens()
        
        # Get file styles
        styles_response = self.get_file_styles(file_id)
        
        # Parse and categorize styles
        tokens = {
            "colors": [],
            "typography": [],
            "spacing": [],
            "effects": [],
            "extracted_at": datetime.now().isoformat()
        }
        
        for style in styles_response.get("meta", {}).get("styles", []):
            style_type = style.get("style_type")
            
            if style_type == "FILL":
                tokens["colors"].append({
                    "name": style.get("name"),
                    "key": style.get("key"),
                    "description": style.get("description", "")
                })
            elif style_type == "TEXT":
                tokens["typography"].append({
                    "name": style.get("name"),
                    "key": style.get("key"),
                    "description": style.get("description", "")
                })
            elif style_type == "EFFECT":
                tokens["effects"].append({
                    "name": style.get("name"),
                    "key": style.get("key"),
                    "description": style.get("description", "")
                })
        
        return tokens
    
    # =========================================================================
    # Variables API (Enterprise Feature)
    # =========================================================================
    
    def get_local_variables(self, file_id: str) -> List[FigmaVariable]:
        """
        Get local variables from a Figma file.
        
        This is an Enterprise feature that provides access to design tokens
        defined as variables in Figma.
        
        Args:
            file_id: Figma file ID
        
        Returns:
            List of FigmaVariable objects
        """
        if self.mock_mode:
            return self._get_mock_variables()
        
        response = self._make_request_sync(f"files/{file_id}/variables/local")
        variables = []
        
        for var_id, var_data in response.get("meta", {}).get("variables", {}).items():
            variables.append(FigmaVariable(
                id=var_id,
                name=var_data.get("name", ""),
                resolved_type=var_data.get("resolvedType", ""),
                value_by_mode=var_data.get("valuesByMode", {}),
                description=var_data.get("description", ""),
                collection_id=var_data.get("variableCollectionId", "")
            ))
        
        return variables
    
    def get_variable_collections(self, file_id: str) -> Dict[str, Any]:
        """
        Get variable collections from a Figma file.
        
        Variable collections group related variables (e.g., "Colors", "Spacing").
        
        Args:
            file_id: Figma file ID
            
        Returns:
            Dictionary of variable collections
        """
        if self.mock_mode:
            return self._get_mock_variable_collections()
        
        return self._make_request_sync(f"files/{file_id}/variables/local")
    
    # =========================================================================
    # Team Library (Enterprise Feature)
    # =========================================================================
    
    def get_team_components(self, team_id: Optional[str] = None) -> List[FigmaComponent]:
        """
        Get shared components from team library.
        
        Args:
            team_id: Figma team ID (uses settings if not provided)
        
        Returns:
            List of shared FigmaComponent objects
        """
        team_id = team_id or settings.figma_team_id
        
        if self.mock_mode or not team_id:
            return self._get_mock_components()
        
        response = self._make_request_sync(f"teams/{team_id}/components")
        components = []
        
        for meta in response.get("meta", {}).get("components", []):
            components.append(FigmaComponent(
                key=meta.get("key", ""),
                name=meta.get("name", ""),
                description=meta.get("description", ""),
                thumbnail_url=meta.get("thumbnail_url")
            ))
        
        return components
    
    def get_team_styles(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get shared styles from team library.
        
        Args:
            team_id: Figma team ID (uses settings if not provided)
            
        Returns:
            Dictionary of shared styles
        """
        team_id = team_id or settings.figma_team_id
        
        if self.mock_mode or not team_id:
            return self._get_mock_styles()
        
        return self._make_request_sync(f"teams/{team_id}/styles")
    
    # =========================================================================
    # Comments API
    # =========================================================================
    
    def get_file_comments(self, file_id: str) -> List[Dict[str, Any]]:
        """
        Get comments from a Figma file.
        
        Useful for getting design feedback and annotations.
        
        Args:
            file_id: Figma file ID
        
        Returns:
            List of comments
        """
        if self.mock_mode:
            return self._get_mock_comments()
        
        response = self._make_request_sync(f"files/{file_id}/comments")
        return response.get("comments", [])
    
    # =========================================================================
    # Dashboard Design System (Project-Specific)
    # =========================================================================
    
    def get_dashboard_design_system(self) -> Dict[str, Any]:
        """
        Get the complete design system for the Paramount+ Operations Dashboard.
        
        Returns:
            Complete design system including tokens, components, and specs
        """
        file_id = settings.figma_file_id
        
        if self.mock_mode or not file_id:
            return self._get_mock_dashboard_design_system()
        
        # Fetch all design system elements
        tokens = self.get_design_tokens(file_id)
        components = self.get_file_components(file_id)
        variables = self.get_local_variables(file_id)
        
        return {
            "name": "Paramount+ Operations Dashboard",
            "version": "1.0.0",
            "figma_file_id": file_id,
            "tokens": tokens,
            "components": [
                {
                    "key": c.key,
                    "name": c.name,
                    "description": c.description,
                    "thumbnail_url": c.thumbnail_url
                }
                for c in components
            ],
            "variables": [
                {
                    "id": v.id,
                    "name": v.name,
                    "type": v.resolved_type,
                    "values": v.value_by_mode
                }
                for v in variables
            ],
            "breakpoints": {
                "mobile": 375,
                "tablet": 768,
                "laptop": 1024,
                "desktop": 1280
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def export_to_css_variables(self, file_id: Optional[str] = None) -> str:
        """
        Export design tokens as CSS custom properties.
        
        Args:
            file_id: Figma file ID (uses settings if not provided)
            
        Returns:
            CSS string with custom properties
        """
        file_id = file_id or settings.figma_file_id
        
        if self.mock_mode or not file_id:
            tokens = self._get_mock_design_tokens()
        else:
            tokens = self.get_design_tokens(file_id)
        
        css_lines = [":root {"]
        
        # Colors
        for color in tokens.get("colors", []):
            var_name = color["name"].lower().replace(" ", "-").replace("/", "-")
            css_lines.append(f"  --color-{var_name}: {color.get('hex', '#000000')};")
        
        # Typography
        for typo in tokens.get("typography", []):
            var_name = typo["name"].lower().replace(" ", "-").replace("/", "-")
            css_lines.append(f"  --font-{var_name}-size: {typo.get('size', 16)}px;")
            css_lines.append(f"  --font-{var_name}-weight: {typo.get('weight', 400)};")
        
        # Spacing
        for spacing in tokens.get("spacing", []):
            var_name = spacing["name"].lower().replace(" ", "-")
            css_lines.append(f"  --spacing-{var_name}: {spacing.get('value', 0)}px;")
        
        css_lines.append("}")
        
        return "\n".join(css_lines)
    
    # =========================================================================
    # Mock Data Generators
    # =========================================================================
    
    def _get_mock_file(self, file_id: str) -> Dict[str, Any]:
        """Generate mock Figma file data."""
        return {
            "name": "Paramount+ Operations Dashboard",
            "lastModified": datetime.now().isoformat(),
            "thumbnailUrl": "https://figma.com/thumbnail.png",
            "version": "1234567890",
            "document": {
                "id": "0:0",
                "name": "Document",
                "type": "DOCUMENT",
                "children": []
            }
        }
    
    def _get_mock_components(self) -> List[FigmaComponent]:
        """Generate mock Figma components."""
        return [
            FigmaComponent(
                key="kpi-card",
                name="KPI Card",
                description="Displays a key performance indicator with value and trend",
                containing_frame="Components"
            ),
            FigmaComponent(
                key="pareto-bar",
                name="Pareto Bar",
                description="Visualizes Pareto distribution with filled/empty segments",
                containing_frame="Components"
            ),
            FigmaComponent(
                key="priority-list",
                name="Priority List",
                description="Ranked list of priorities with impact values",
                containing_frame="Components"
            ),
            FigmaComponent(
                key="status-badge",
                name="Status Badge",
                description="Status indicator (Healthy, Warning, Critical)",
                containing_frame="Components"
            ),
            FigmaComponent(
                key="metric-card",
                name="Metric Card",
                description="Compact metric display with icon",
                containing_frame="Components"
            ),
            FigmaComponent(
                key="data-table",
                name="Data Table",
                description="Sortable data table with pagination",
                containing_frame="Components"
            ),
            FigmaComponent(
                key="chart-line",
                name="Line Chart",
                description="Time series visualization",
                containing_frame="Charts"
            ),
            FigmaComponent(
                key="chart-bar",
                name="Bar Chart",
                description="Comparison visualization",
                containing_frame="Charts"
            )
        ]
    
    def _get_mock_styles(self) -> Dict[str, Any]:
        """Generate mock Figma styles."""
        return {
            "meta": {
                "styles": [
                    {"name": "Primary/Blue", "style_type": "FILL", "key": "color-primary"},
                    {"name": "Primary/Navy", "style_type": "FILL", "key": "color-navy"},
                    {"name": "Success/Green", "style_type": "FILL", "key": "color-success"},
                    {"name": "Warning/Yellow", "style_type": "FILL", "key": "color-warning"},
                    {"name": "Critical/Red", "style_type": "FILL", "key": "color-critical"},
                    {"name": "Neutral/Gray", "style_type": "FILL", "key": "color-neutral"},
                    {"name": "Heading/H1", "style_type": "TEXT", "key": "text-h1"},
                    {"name": "Heading/H2", "style_type": "TEXT", "key": "text-h2"},
                    {"name": "Heading/H3", "style_type": "TEXT", "key": "text-h3"},
                    {"name": "Body/Regular", "style_type": "TEXT", "key": "text-body"},
                    {"name": "Body/Small", "style_type": "TEXT", "key": "text-small"},
                    {"name": "Metric/Large", "style_type": "TEXT", "key": "text-metric"},
                    {"name": "Shadow/Card", "style_type": "EFFECT", "key": "shadow-card"},
                    {"name": "Shadow/Modal", "style_type": "EFFECT", "key": "shadow-modal"}
                ]
            }
        }
    
    def _get_mock_design_tokens(self) -> Dict[str, Any]:
        """Generate mock design tokens."""
        return {
            "colors": [
                {"name": "primary-blue", "hex": "#0066FF", "description": "Primary brand color"},
                {"name": "deep-navy", "hex": "#1A1F36", "description": "Background, dark mode"},
                {"name": "success-green", "hex": "#34D399", "description": "Healthy metrics"},
                {"name": "warning-yellow", "hex": "#FBBF24", "description": "Warning states"},
                {"name": "critical-red", "hex": "#EF4444", "description": "Critical alerts"},
                {"name": "neutral-gray", "hex": "#6B7280", "description": "Secondary text"},
                {"name": "background-light", "hex": "#F9FAFB", "description": "Light background"},
                {"name": "border", "hex": "#E5E7EB", "description": "Borders and dividers"}
            ],
            "typography": [
                {"name": "h1", "family": "Inter", "size": 32, "weight": 700, "lineHeight": 40},
                {"name": "h2", "family": "Inter", "size": 24, "weight": 600, "lineHeight": 32},
                {"name": "h3", "family": "Inter", "size": 18, "weight": 500, "lineHeight": 28},
                {"name": "body", "family": "Inter", "size": 14, "weight": 400, "lineHeight": 20},
                {"name": "caption", "family": "Inter", "size": 12, "weight": 400, "lineHeight": 16},
                {"name": "metric", "family": "JetBrains Mono", "size": 28, "weight": 700, "lineHeight": 36}
            ],
            "spacing": [
                {"name": "xs", "value": 4},
                {"name": "sm", "value": 8},
                {"name": "md", "value": 16},
                {"name": "lg", "value": 24},
                {"name": "xl", "value": 32},
                {"name": "2xl", "value": 48},
                {"name": "3xl", "value": 64}
            ],
            "effects": [
                {"name": "shadow-sm", "value": "0 1px 2px rgba(0,0,0,0.05)"},
                {"name": "shadow-md", "value": "0 4px 6px rgba(0,0,0,0.1)"},
                {"name": "shadow-lg", "value": "0 10px 15px rgba(0,0,0,0.1)"}
            ],
            "extracted_at": datetime.now().isoformat()
        }
    
    def _get_mock_variables(self) -> List[FigmaVariable]:
        """Generate mock Figma variables."""
        return [
            FigmaVariable(
                id="var-1",
                name="color/primary",
                resolved_type="COLOR",
                value_by_mode={"light": "#0066FF", "dark": "#3B82F6"},
                collection_id="colors"
            ),
            FigmaVariable(
                id="var-2",
                name="color/success",
                resolved_type="COLOR",
                value_by_mode={"light": "#34D399", "dark": "#10B981"},
                collection_id="colors"
            ),
            FigmaVariable(
                id="var-3",
                name="spacing/md",
                resolved_type="FLOAT",
                value_by_mode={"default": 16},
                collection_id="spacing"
            ),
            FigmaVariable(
                id="var-4",
                name="radius/card",
                resolved_type="FLOAT",
                value_by_mode={"default": 8},
                collection_id="radius"
            )
        ]
    
    def _get_mock_variable_collections(self) -> Dict[str, Any]:
        """Generate mock variable collections."""
        return {
            "meta": {
                "variableCollections": {
                    "colors": {
                        "id": "colors",
                        "name": "Colors",
                        "modes": [{"modeId": "light", "name": "Light"}, {"modeId": "dark", "name": "Dark"}]
                    },
                    "spacing": {
                        "id": "spacing",
                        "name": "Spacing",
                        "modes": [{"modeId": "default", "name": "Default"}]
                    },
                    "radius": {
                        "id": "radius",
                        "name": "Border Radius",
                        "modes": [{"modeId": "default", "name": "Default"}]
                    }
                }
            }
        }
    
    def _get_mock_comments(self) -> List[Dict[str, Any]]:
        """Generate mock file comments."""
        return [
            {
                "id": "comment-1",
                "message": "Consider using the Pareto visualization here",
                "created_at": "2025-12-01T10:00:00Z",
                "user": {"handle": "designer1"}
            },
            {
                "id": "comment-2",
                "message": "Updated color tokens for dark mode",
                "created_at": "2025-12-05T14:30:00Z",
                "user": {"handle": "designer2"}
            }
        ]
    
    def _get_mock_dashboard_design_system(self) -> Dict[str, Any]:
        """Generate mock dashboard design system."""
        return {
            "name": "Paramount+ Operations Dashboard",
            "version": "1.0.0",
            "figma_file_id": "mock-file-id",
            "tokens": self._get_mock_design_tokens(),
            "components": [
                {"key": c.key, "name": c.name, "description": c.description}
                for c in self._get_mock_components()
            ],
            "variables": [
                {"id": v.id, "name": v.name, "type": v.resolved_type, "values": v.value_by_mode}
                for v in self._get_mock_variables()
            ],
            "breakpoints": {
                "mobile": 375,
                "tablet": 768,
                "laptop": 1024,
                "desktop": 1280
            },
            "screens": [
                {"name": "Executive Dashboard", "description": "High-level KPIs and Pareto analysis"},
                {"name": "Churn Analysis", "description": "Cohort breakdown and risk scores"},
                {"name": "Production Ops", "description": "JIRA issues and delays"},
                {"name": "Streaming Health", "description": "Conviva QoE metrics"},
                {"name": "Campaign Manager", "description": "Retention campaigns and ROI"}
            ],
            "generated_at": datetime.now().isoformat()
        }
