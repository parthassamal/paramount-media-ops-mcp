"""
Paramount Media Operations MCP Server.

FastAPI-based MCP server providing resources and tools for streaming operations intelligence.
Implements the Model Context Protocol (MCP) for LLM integration with Pareto-driven insights.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
from datetime import datetime

from config import settings
from mcp.resources import (
    create_churn_signals,
    create_complaints_topics,
    create_production_issues,
    create_content_catalog,
    create_international_markets,
    create_revenue_impact,
    create_retention_campaigns,
    create_operational_efficiency,
    create_pareto_analysis
)
from mcp.tools import (
    create_analyze_churn,
    create_analyze_complaints,
    create_analyze_production,
    create_forecast_revenue,
    create_generate_campaign
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer() if settings.log_format == "json" else structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger()

# Initialize resources (lazy loaded for faster startup)
RESOURCES: Dict[str, Any] = {}
TOOLS: Dict[str, Any] = {}


def _initialize_resources() -> Dict[str, Any]:
    """Initialize all MCP resources."""
    return {
        "churn_signals": create_churn_signals(),
        "complaints_topics": create_complaints_topics(),
        "production_issues": create_production_issues(),
        "content_catalog": create_content_catalog(),
        "international_markets": create_international_markets(),
        "revenue_impact": create_revenue_impact(),
        "retention_campaigns": create_retention_campaigns(),
        "operational_efficiency": create_operational_efficiency(),
        "pareto_analysis": create_pareto_analysis()
    }


def _initialize_tools() -> Dict[str, Any]:
    """Initialize all MCP tools."""
    return {
        "analyze_churn_root_cause": create_analyze_churn(),
        "analyze_complaint_themes": create_analyze_complaints(),
        "analyze_production_risk": create_analyze_production(),
        "forecast_revenue_with_constraints": create_forecast_revenue(),
        "generate_retention_campaign": create_generate_campaign()
    }


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators.
    """
    # Startup
    global RESOURCES, TOOLS
    
    logger.info(
        "server_starting",
        name=settings.mcp_server_name,
        version=settings.mcp_server_version,
        environment=settings.environment,
        mock_mode=settings.mock_mode,
        host=settings.mcp_server_host,
        port=settings.mcp_server_port
    )
    
    # Initialize resources and tools
    RESOURCES = _initialize_resources()
    TOOLS = _initialize_tools()
    
    logger.info(
        "server_ready",
        resources_count=len(RESOURCES),
        tools_count=len(TOOLS)
    )
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("server_shutting_down")


# Initialize FastAPI app with lifespan handler
app = FastAPI(
    title=settings.mcp_server_name,
    description="""
    ## Paramount+ Media Operations MCP Server
    
    AI-driven streaming operations platform with MCP protocol support.
    
    ### Features
    - **9 Data Resources**: Churn, complaints, production, content, markets, revenue, campaigns, efficiency, Pareto
    - **5 LLM Tools**: Root cause analysis, complaint themes, production risk, revenue forecast, retention campaigns
    - **Pareto Engine**: 80/20 rule applied across all domains
    
    ### Quick Start
    - Query resources: `POST /resources/{name}/query`
    - Execute tools: `POST /tools/{name}/execute`
    - Health check: `GET /health`
    """,
    version=settings.mcp_server_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://paramount.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class ResourceQueryRequest(BaseModel):
    """Request model for resource queries."""
    resource: str = Field(..., description="Resource name to query")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")


class ToolExecuteRequest(BaseModel):
    """Request model for tool execution."""
    tool: str = Field(..., description="Tool name to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class MCPResponse(BaseModel):
    """Standard MCP response format."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing."""
    start_time = datetime.now()
    
    logger.info(
        "request_received",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else "unknown"
    )
    
    try:
        response = await call_next(request)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        return response
    except Exception as e:
        logger.error(
            "request_failed",
            method=request.method,
            path=request.url.path,
            error=str(e)
        )
        raise


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions globally."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        error_type=type(exc).__name__
    )
    
    return JSONResponse(
        status_code=500,
        content=MCPResponse(
            success=False,
            error=f"Internal server error: {str(exc)}"
        ).model_dump()
    )


# Health check endpoint
@app.get("/health", response_model=MCPResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns server status, configuration, and available resources/tools count.
    """
    return MCPResponse(
        success=True,
        data={
            "status": "healthy",
            "server_name": settings.mcp_server_name,
            "version": settings.mcp_server_version,
            "environment": settings.environment,
            "mock_mode": settings.mock_mode,
            "resources_available": len(RESOURCES),
            "tools_available": len(TOOLS),
            "integrations": {
                "jira": settings.jira_enabled,
                "conviva": settings.conviva_enabled,
                "newrelic": settings.newrelic_enabled,
                "analytics": settings.analytics_enabled,
                "figma": settings.figma_enabled
            },
            "timestamp": datetime.now().isoformat()
        }
    )


# Root endpoint
@app.get("/", response_model=MCPResponse, tags=["System"])
async def root():
    """
    Root endpoint with server information and navigation links.
    """
    return MCPResponse(
        success=True,
        data={
            "message": "Paramount+ Media Operations MCP Server",
            "description": "AI-driven streaming operations platform with Pareto intelligence",
            "version": settings.mcp_server_version,
            "environment": settings.get_environment_display(),
            "endpoints": {
                "docs": "/docs",
                "redoc": "/redoc",
                "health": "/health",
                "resources": "/resources",
                "tools": "/tools"
            }
        }
    )


# List available resources
@app.get("/resources", response_model=MCPResponse, tags=["Resources"])
async def list_resources():
    """
    List all available MCP resources with their descriptions.
    """
    resource_list = [
        {
            "name": name,
            "description": resource.__class__.__doc__.strip() if resource.__class__.__doc__ else "No description",
            "query_endpoint": f"/resources/{name}/query",
            "uri": f"paramount://{name}"
        }
        for name, resource in RESOURCES.items()
    ]
    
    return MCPResponse(
        success=True,
        data={
            "resources": resource_list,
            "total_count": len(resource_list)
        }
    )


# Query a specific resource
@app.post("/resources/{resource_name}/query", response_model=MCPResponse, tags=["Resources"])
async def query_resource(resource_name: str, params: Dict[str, Any] = {}):
    """
    Query a specific MCP resource.
    
    Args:
        resource_name: Name of the resource to query
        params: Query parameters (varies by resource)
    
    Returns:
        Resource data with Pareto analysis if applicable
    """
    if resource_name not in RESOURCES:
        raise HTTPException(
            status_code=404,
            detail=f"Resource '{resource_name}' not found. Available: {list(RESOURCES.keys())}"
        )
    
    try:
        logger.info(
            "resource_query",
            resource=resource_name,
            params=params
        )
        
        resource = RESOURCES[resource_name]
        result = resource.query(**params)
        
        return MCPResponse(
            success=True,
            data={
                "resource": resource_name,
                "result": result
            }
        )
    except Exception as e:
        logger.error(
            "resource_query_failed",
            resource=resource_name,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# List available tools
@app.get("/tools", response_model=MCPResponse, tags=["Tools"])
async def list_tools():
    """
    List all available LLM-callable tools with their descriptions.
    """
    tool_list = [
        {
            "name": name,
            "description": tool.__class__.__doc__.strip() if tool.__class__.__doc__ else "No description",
            "execute_endpoint": f"/tools/{name}/execute"
        }
        for name, tool in TOOLS.items()
    ]
    
    return MCPResponse(
        success=True,
        data={
            "tools": tool_list,
            "total_count": len(tool_list)
        }
    )


# Execute a specific tool
@app.post("/tools/{tool_name}/execute", response_model=MCPResponse, tags=["Tools"])
async def execute_tool(tool_name: str, params: Dict[str, Any] = {}):
    """
    Execute a specific LLM-callable tool.
    
    Args:
        tool_name: Name of the tool to execute
        params: Tool parameters (varies by tool)
    
    Returns:
        Tool execution result with analysis and recommendations
    """
    if tool_name not in TOOLS:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available: {list(TOOLS.keys())}"
        )
    
    try:
        logger.info(
            "tool_execute",
            tool=tool_name,
            params=params
        )
        
        tool = TOOLS[tool_name]
        result = tool.execute(**params)
        
        return MCPResponse(
            success=True,
            data={
                "tool": tool_name,
                "result": result
            }
        )
    except Exception as e:
        logger.error(
            "tool_execute_failed",
            tool=tool_name,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))


# Unified query endpoint for MCP protocol
@app.post("/query", response_model=MCPResponse, tags=["MCP Protocol"])
async def mcp_query(request: ResourceQueryRequest):
    """
    Unified MCP query endpoint for resources.
    
    This endpoint follows the MCP protocol pattern:
    ```json
    {"resource": "resource_name", "params": {...}}
    ```
    """
    return await query_resource(request.resource, request.params)


# Unified execute endpoint for MCP protocol
@app.post("/execute", response_model=MCPResponse, tags=["MCP Protocol"])
async def mcp_execute(request: ToolExecuteRequest):
    """
    Unified MCP execute endpoint for tools.
    
    This endpoint follows the MCP protocol pattern:
    ```json
    {"tool": "tool_name", "params": {...}}
    ```
    """
    return await execute_tool(request.tool, request.params)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "mcp.server:app",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )
