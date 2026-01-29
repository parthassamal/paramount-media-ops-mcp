"""Figma API endpoints for live design system integration."""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
from mcp.integrations.figma_client import FigmaClient
from config import settings
from mcp.utils.error_handler import ServiceError, ConnectionError, retry_with_backoff
from mcp.utils.logger import get_logger, log_performance

logger = get_logger(__name__)

router = APIRouter(prefix="/figma", tags=["figma"])

@router.get("/tokens")
async def get_figma_tokens(file_id: Optional[str] = None):
    """
    Fetch live design tokens from Figma.
    
    If no file_id is provided, uses the default from settings.
    """
    if not settings.figma_enabled:
        # Fallback to mock data if disabled, to avoid breaking frontend
        client = FigmaClient(mock_mode=True)
        return client.get_design_tokens("mock-id")

    try:
        client = FigmaClient()
        file_id = file_id or settings.figma_file_id
        
        if not file_id:
            raise HTTPException(status_code=400, detail="Figma File ID is not configured")
            
        tokens = client.get_design_tokens(file_id)
        return tokens
    except Exception as e:
        logger.error("figma_tokens_error", error=str(e))
        # Fallback to mock data on error
        client = FigmaClient(mock_mode=True)
        return client.get_design_tokens("mock-id")

@router.get("/css-variables")
async def get_figma_css(file_id: Optional[str] = None):
    """
    Get design tokens as CSS variables.
    """
    try:
        client = FigmaClient()
        css = client.export_to_css_variables(file_id)
        return {"css": css}
    except Exception as e:
        logger.error("figma_css_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/images")
async def get_figma_images(ids: Optional[str] = None, file_id: Optional[str] = None, format: str = "png"):
    """
    Fetch live images from Figma nodes.
    """
    try:
        client = FigmaClient()
        file_id = file_id or settings.figma_file_id
        ids = ids or settings.figma_hero_node_id
        
        if not file_id:
            raise HTTPException(status_code=400, detail="Figma File ID is not configured")
        if not ids:
            raise HTTPException(status_code=400, detail="Figma Node IDs are not provided")
            
        images = client.get_images(file_id, ids, format=format)
        return {"images": images}
    except Exception as e:
        logger.error("figma_images_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/design-system")
async def get_full_design_system():
    """
    Get the complete live design system metadata.
    """
    try:
        client = FigmaClient()
        return client.get_dashboard_design_system()
    except Exception as e:
        logger.error("figma_design_system_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

