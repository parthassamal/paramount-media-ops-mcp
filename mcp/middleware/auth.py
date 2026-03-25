"""
API key authentication middleware.

Protects API endpoints with a configurable API secret key.
Public endpoints (health, docs, openapi) are exempt.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from config import settings

PUBLIC_PATHS = frozenset({
    "/", "/health", "/docs", "/redoc", "/openapi.json",
    "/static", "/favicon.ico",
})


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    for prefix in ("/static/", "/docs/", "/redoc/"):
        if path.startswith(prefix):
            return True
    return False


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Require X-API-Key header when API_SECRET_KEY is configured."""

    async def dispatch(self, request: Request, call_next) -> Response:
        secret = getattr(settings, "api_secret_key", "")
        if not secret:
            return await call_next(request)

        if _is_public(request.url.path):
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        provided = request.headers.get("X-API-Key", "")
        if provided != secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key. Provide X-API-Key header.",
            )

        return await call_next(request)
