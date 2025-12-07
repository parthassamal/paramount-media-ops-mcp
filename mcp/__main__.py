"""
Main entry point for running the MCP server.

Usage:
    python -m mcp.server
    
Or with uvicorn directly:
    uvicorn mcp.server:app --host 0.0.0.0 --port 8000 --reload
"""

from mcp.server import app, logger
from config import settings
import uvicorn

if __name__ == "__main__":
    logger.info(
        "starting_mcp_server",
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        environment=settings.environment
    )
    
    uvicorn.run(
        app,
        host=settings.mcp_server_host,
        port=settings.mcp_server_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
        access_log=True
    )
