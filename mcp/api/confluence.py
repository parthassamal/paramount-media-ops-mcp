"""
Confluence REST API Endpoints with comprehensive Swagger documentation.

Provides knowledge base, documentation, and collaboration features.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime

from mcp.integrations import AtlassianClient
from config import settings
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/api/confluence", tags=["Confluence Knowledge Base"])

# Initialize Atlassian client
atlassian = AtlassianClient(mock_mode=settings.mock_mode)


# Pydantic Models
class ConfluencePage(BaseModel):
    """Confluence Page model for API responses."""
    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    space_key: str = Field(..., description="Space key (e.g., OPS)")
    content: Optional[str] = Field(None, description="Page content (HTML)")
    url: str = Field(..., description="Page URL")
    created: str = Field(..., description="Creation timestamp")
    updated: str = Field(..., description="Last updated timestamp")
    author: Optional[str] = Field(None, description="Page author")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123456",
                "title": "Production Runbook - Yellowstone S5",
                "space_key": "OPS",
                "content": "<h1>Production Guidelines</h1><p>...</p>",
                "url": "https://paramounthackathon.atlassian.net/wiki/spaces/OPS/pages/123456",
                "created": "2025-12-01T10:00:00Z",
                "updated": "2025-12-18T14:30:00Z",
                "author": "John Doe"
            }
        }


class CreatePageRequest(BaseModel):
    """Request model for creating a new Confluence page."""
    space_key: str = Field(..., description="Confluence space key")
    title: str = Field(..., description="Page title")
    content: str = Field(..., description="Page content (HTML or Confluence storage format)")
    parent_id: Optional[str] = Field(None, description="Parent page ID (for nested pages)")

    class Config:
        json_schema_extra = {
            "example": {
                "space_key": "OPS",
                "title": "Production Best Practices 2025",
                "content": "<h1>Best Practices</h1><ul><li>Always review color grading</li></ul>",
                "parent_id": None
            }
        }


class ConfluenceSpace(BaseModel):
    """Confluence Space model."""
    id: str = Field(..., description="Space ID")
    key: str = Field(..., description="Space key")
    name: str = Field(..., description="Space name")
    type: str = Field(..., description="Space type (global/personal)")
    url: str = Field(..., description="Space URL")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "12345",
                "key": "OPS",
                "name": "Operations Hub",
                "type": "global",
                "url": "https://paramounthackathon.atlassian.net/wiki/spaces/OPS"
            }
        }


# API Endpoints

@router.get(
    "/spaces",
    response_model=List[ConfluenceSpace],
    summary="Get Confluence Spaces",
    description="""
    Retrieve all Confluence spaces accessible to the current user.
    
    **Returns:**
    - List of spaces with their keys, names, and URLs
    
    **Use Case:** Navigation, space discovery, access verification.
    """
)
async def get_spaces() -> List[ConfluenceSpace]:
    """Get all Confluence spaces."""
    try:
        spaces = atlassian.get_spaces()
        return [ConfluenceSpace(**space) for space in spaces]
    except Exception as e:
        logger.error("confluence_spaces_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch spaces: {str(e)}")


@router.get(
    "/spaces/{space_key}/pages",
    response_model=List[ConfluencePage],
    summary="Get Pages in Space",
    description="""
    Retrieve all pages in a specific Confluence space.
    
    **Path Parameter:**
    - `space_key`: Space key (e.g., "OPS")
    
    **Query Parameters:**
    - `limit`: Maximum pages to return (default: 50)
    - `search`: Search term to filter pages by title
    
    **Use Case:** Documentation browsing, content discovery, search.
    """
)
async def get_pages(
    space_key: str,
    limit: int = Query(50, ge=1, le=500, description="Max pages to return"),
    search: Optional[str] = Query(None, description="Search term for filtering")
) -> List[ConfluencePage]:
    """Get pages in a Confluence space."""
    try:
        pages = atlassian.get_pages(space_key=space_key, limit=limit)
        
        # Filter by search term if provided
        if search:
            pages = [p for p in pages if search.lower() in p.get("title", "").lower()]
        
        return [ConfluencePage(**page) for page in pages]
    except Exception as e:
        logger.error("confluence_pages_failed", space_key=space_key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch pages: {str(e)}")


@router.get(
    "/pages/{page_id}",
    response_model=ConfluencePage,
    summary="Get Page by ID",
    description="""
    Retrieve a specific Confluence page by its ID.
    
    **Path Parameter:**
    - `page_id`: Confluence page ID
    
    **Query Parameters:**
    - `expand`: Comma-separated list of fields to expand (e.g., "body.storage,version")
    
    **Response:** Full page details including content.
    """
)
async def get_page(
    page_id: str,
    expand: str = Query("body.storage,version,history", description="Fields to expand")
) -> ConfluencePage:
    """Get a specific Confluence page."""
    try:
        pages = atlassian.get_pages(limit=100)
        page = next((p for p in pages if p["id"] == page_id), None)
        
        if not page:
            raise HTTPException(status_code=404, detail=f"Page {page_id} not found")
        
        return ConfluencePage(**page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("confluence_get_page_failed", page_id=page_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch page: {str(e)}")


@router.post(
    "/pages",
    response_model=ConfluencePage,
    status_code=201,
    summary="Create Confluence Page",
    description="""
    Create a new page in Confluence.
    
    **Required Fields:**
    - `space_key`: Target space
    - `title`: Page title
    - `content`: Page content (HTML or Confluence storage format)
    
    **Optional Fields:**
    - `parent_id`: Parent page ID for creating nested pages
    
    **Response:** Created page with generated ID and URL.
    
    **Use Case:** Documentation automation, runbook generation, incident reports.
    """
)
async def create_page(request: CreatePageRequest = Body(...)) -> ConfluencePage:
    """Create a new Confluence page."""
    try:
        logger.info("confluence_create_page", space=request.space_key, title=request.title)
        
        page = atlassian.create_page(
            space_key=request.space_key,
            title=request.title,
            content=request.content,
            parent_id=request.parent_id
        )
        
        return ConfluencePage(**page)
        
    except Exception as e:
        logger.error("confluence_create_page_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create page: {str(e)}")


@router.get(
    "/search",
    response_model=List[ConfluencePage],
    summary="Search Confluence",
    description="""
    Search across all Confluence spaces for pages matching a query.
    
    **Query Parameters:**
    - `q`: Search query (searches in title and content)
    - `space_key`: Optional space filter
    - `limit`: Maximum results to return
    
    **Use Case:** Knowledge discovery, documentation search, troubleshooting.
    """
)
async def search_pages(
    q: str = Query(..., description="Search query"),
    space_key: Optional[str] = Query(None, description="Filter by space"),
    limit: int = Query(25, ge=1, le=100, description="Max results")
) -> List[ConfluencePage]:
    """Search Confluence pages."""
    try:
        logger.info("confluence_search", query=q, space=space_key)
        
        # Get all pages and filter (simplified search)
        pages = atlassian.get_pages(space_key=space_key, limit=limit * 2)
        
        # Filter by search term
        results = [
            p for p in pages
            if q.lower() in p.get("title", "").lower() or
               q.lower() in p.get("content", "").lower()
        ]
        
        return [ConfluencePage(**page) for page in results[:limit]]
        
    except Exception as e:
        logger.error("confluence_search_failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get(
    "/health",
    summary="Confluence Health Check",
    description="Check Confluence API connectivity and configuration status."
)
async def confluence_health_check():
    """Check Confluence integration health."""
    return {
        "status": "healthy" if settings.atlassian_enabled else "disabled",
        "mock_mode": settings.mock_mode,
        "api_url": settings.atlassian_api_url if settings.atlassian_enabled else None,
        "timestamp": datetime.now().isoformat()
    }

