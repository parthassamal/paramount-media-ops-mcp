"""
Server-Sent Events (SSE) endpoint for real-time dashboard updates.

Streams events to the frontend for live data refresh without polling.
"""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import structlog

from config import settings

logger = structlog.get_logger()
router = APIRouter(tags=["Real-time Events"])

_event_queue: asyncio.Queue = asyncio.Queue(maxsize=100)


async def push_event(event_type: str, data: dict) -> None:
    """Push an event to all SSE listeners (call from any API handler)."""
    try:
        _event_queue.put_nowait({
            "event": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
    except asyncio.QueueFull:
        pass


async def _event_generator() -> AsyncGenerator[str, None]:
    """Yield SSE-formatted messages from the queue, with keep-alive pings."""
    yield "event: connected\ndata: {\"status\": \"ok\"}\n\n"

    while True:
        try:
            event = await asyncio.wait_for(_event_queue.get(), timeout=15.0)
            payload = json.dumps(event["data"])
            yield f"event: {event['event']}\ndata: {payload}\n\n"
        except asyncio.TimeoutError:
            yield ": keepalive\n\n"


@router.get(
    "/events/stream",
    summary="Real-time SSE event stream",
    description="Server-Sent Events endpoint for live dashboard updates. "
                "Connect with EventSource in the browser.",
)
async def sse_stream():
    """Stream real-time events to the frontend."""
    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
