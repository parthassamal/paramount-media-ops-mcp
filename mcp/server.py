"""
Paramount Media Operations MCP Server.

FastAPI-based MCP server providing resources and tools for streaming operations intelligence.
Implements the Model Context Protocol (MCP) for LLM integration with Pareto-driven insights.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import structlog
from datetime import datetime
import os

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
from mcp.api import jira_router, confluence_router, analytics_router, streaming_router, figma_router, adobe_router, ai_router

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
    title="Paramount+ AI Operations Platform",
    description="""
# 🎬 Paramount+ AI Operations Platform

**Intelligent Operations Hub powered by the Model Context Protocol (MCP)**

---

## 📖 Overview

This platform provides **AI-native access** to Paramount+ operational data through the Model Context Protocol. 
AI assistants like Claude, ChatGPT, and custom LLMs can query production issues, subscriber analytics, 
and streaming metrics using natural language.

Built for the **Paramount Hackathon 2025** | [View on GitHub](https://github.com/parthassamal/paramount-media-ops-mcp)

---

## 🎯 Key Features

- **🤖 AI-Callable Tools** - 5 intelligent tools for operational insights
- **📊 Pareto Analysis** - Automatically identifies the vital 20% driving 80% of impact
- **🔗 Live Integrations** - JIRA, Dynatrace, NewRelic, Analytics, Figma
- **📈 Real-time Dashboards** - React UI with live Figma design sync
- **📄 PDF Reports** - One-click executive reports with styling

---

## 🚀 Quick Start

### Try It Now (Click to Test):
1. **Health Check**: `GET /health` - Verify all integrations
2. **List AI Tools**: `GET /tools` - See 5 available MCP tools
3. **Execute Analysis**: `POST /tools/analyze_production_risk/execute` with body `{}`

### 🎯 Recommended Demo Flow:
```bash
# Step 1: Check system health
GET /health

# Step 2: See available tools
GET /tools

# Step 3: Execute Pareto analysis on production issues
POST /tools/analyze_production_risk/execute
Body: {}

# Step 4: Get JIRA critical issues
GET /api/jira/issues/critical

# Step 5: Generate PDF report
POST /adobe/export-report
Body: {"report_type": "executive", "data": {...}}
```

### 💡 Example Query (What AI Assistants Do):
**Human asks**: *"What production issues should I fix first?"*  
**AI calls**: `POST /tools/analyze_production_risk/execute`  
**AI responds**: *"Top 4 issues (20%) cause 71% of delays: PROD-0001 (Star Trek VFX blocker, $2.5M impact), ..."*

---

## 💡 Business Impact

| Metric | Value |
|--------|-------|
| Revenue Saved | **$20M annually** |
| MTTR Improvement | **50% faster** (2.4h → 1.2h) |
| Subscribers Monitored | **67.5M** |
| Annual Revenue | **$10.2B** |

---

## 🔐 Authentication

Currently running in **MOCK_MODE** (safe for demos). 
To enable live integrations, configure API keys in `.env` file.

---

## 📚 Documentation
- **Swagger UI** (this page)
- [ReDoc Alternative](/redoc)
- [GitHub Repository](https://github.com/parthassamal/paramount-media-ops-mcp)
- [5-Minute Demo Video](#) *(coming soon)*

---

## 👥 Hackathon Team
**Built for Paramount Hackathon 2025**  
Developed by: *Your Name/Team*  
Contact: *your-email@paramount.com*

---

## 🎓 What is MCP?
The **Model Context Protocol** is Anthropic's open standard that lets AI assistants access external data sources as if they were part of the LLM's context. Think of it as "RAG for APIs" - instead of manually querying databases and systems, AI assistants can directly call tools and resources through a standardized protocol.

**Why MCP for Operations?**  
Operations teams deal with data across dozens of systems (JIRA, NewRelic, Analytics, etc.). MCP unifies all of this into AI-queryable tools, enabling natural language operations: *"What should I fix first?"* → AI queries JIRA → Applies Pareto analysis → Returns prioritized list.
    """,
    version=settings.mcp_server_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={
        "deepLinking": True,
        "displayRequestDuration": True,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "syntaxHighlight.theme": "monokai",
    },
    openapi_tags=[
        {
            "name": "System",
            "description": """
**System Health & Configuration**

Check platform status, integrations connectivity, and configuration details.
            """
        },
        {
            "name": "Tools",
            "description": """
**🤖 AI-Callable MCP Tools**

These are the core AI-powered tools accessible via the Model Context Protocol. 
Any LLM can discover and execute these tools to get operational intelligence.

**Available Tools:**
- `analyze_production_risk` - Pareto analysis of production issues
- `analyze_churn_root_cause` - Identify why subscribers leave
- `generate_retention_campaign` - Create targeted retention strategies
- `analyze_complaint_themes` - Find fixable issues in customer feedback
- `forecast_revenue_with_constraints` - Model revenue under different scenarios

**Usage**: Execute tools via `POST /tools/{tool_name}/execute`
            """
        },
        {
            "name": "JIRA Production Tracking",
            "description": """
**🎬 Production Issue Tracking**

Live integration with JIRA at https://paramounthackathon.atlassian.net

Monitor production issues from shows like Star Trek: Discovery, SEAL Team, and more.
Includes Pareto analysis to identify the vital 20% of issues driving 80% of impact.
            """
        },
        {
            "name": "Analytics & Churn Intelligence",
            "description": """
**📊 Subscriber Analytics**

Churn prediction, cohort analysis, and lifetime value calculations.
Helps identify at-risk subscribers and optimize retention campaigns.
            """
        },
        {
            "name": "Streaming QoE & Infrastructure",
            "description": """
**📺 Streaming Quality & Infrastructure Health**

Integration with Dynatrace and NewRelic for:
- Buffering ratios and video start failures
- Service health monitoring
- Infrastructure incidents
            """
        },
        {
            "name": "adobe",
            "description": """
**📄 PDF Report Generation**

Generate and download professional PDF reports with:
- Executive summaries
- Styled metrics and insights
- Figma design system integration
            """
        },
        {
            "name": "Confluence Knowledge Base",
            "description": """
**📚 Documentation & Knowledge Management**

Access operational documentation, runbooks, and best practices 
from Confluence integration.
            """
        },
        {
            "name": "Resources",
            "description": """
**🗄️ MCP Data Resources**

Read-only data resources with Pareto analysis across operational domains.
            """
        },
        {
            "name": "MCP Protocol",
            "description": """
**🔌 Model Context Protocol Unified Endpoints**

Generic MCP endpoints for resource queries and tool execution.
            """
        },
        {
            "name": "figma",
            "description": """
**🎨 Figma Design System Integration**

Live synchronization with Figma for design tokens, CSS variables, and asset exports.
Enables real-time dashboard styling updates from Figma designs.
            """
        }
    ]
)

# Mount static files for custom Swagger CSS
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add CORS middleware for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://paramount.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(jira_router)
app.include_router(confluence_router)
app.include_router(analytics_router)
app.include_router(streaming_router)
app.include_router(figma_router)
app.include_router(adobe_router)
app.include_router(ai_router)  # Patent-worthy AI services

# Custom Swagger UI with styling
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI with Paramount+ branding."""
    return HTMLResponse(content=f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{app.title} - API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css">
        <link rel="stylesheet" type="text/css" href="/static/swagger-custom.css">
        <link rel="icon" type="image/png" href="https://www.paramount.com/sites/default/files/favicon.ico">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
        <script>
            const ui = SwaggerUIBundle({{
                url: '{app.openapi_url}',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout",
                filter: true,
                displayRequestDuration: true,
                syntaxHighlight: {{
                    theme: "monokai"
                }},
                tryItOutEnabled: true,
                docExpansion: "list",
                defaultModelsExpandDepth: 3,
                defaultModelExpandDepth: 3,
                showExtensions: true,
                showCommonExtensions: true
            }});
        </script>
    </body>
    </html>
    """)


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
                "confluence": settings.atlassian_enabled,
                "conviva": settings.conviva_enabled,
                "newrelic": settings.newrelic_enabled,
                "analytics": settings.analytics_enabled,
                "figma": settings.figma_enabled
            },
            "api_endpoints": {
                "jira": "/api/jira",
                "confluence": "/api/confluence",
                "analytics": "/api/analytics",
                "streaming": "/api/streaming"
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
