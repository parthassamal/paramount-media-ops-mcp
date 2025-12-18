"""REST API routers for Paramount Media Operations Hub."""

from mcp.api.jira import router as jira_router
from mcp.api.confluence import router as confluence_router
from mcp.api.analytics import router as analytics_router
from mcp.api.streaming import router as streaming_router
from mcp.api.figma import router as figma_router
from mcp.api.adobe_exports import router as adobe_router

__all__ = ["jira_router", "confluence_router", "analytics_router", "streaming_router", "figma_router", "adobe_router"]


