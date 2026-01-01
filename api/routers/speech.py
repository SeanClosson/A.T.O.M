from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter(prefix="/api/speech", tags=["Speech"])

# Queue for speech events
speech_event_queue: asyncio.Queue = asyncio.Queue()

async def event_stream():
    while True:
        event = await speech_event_queue.get()

        # MUST be correct SSE format
        yield f"data: {json.dumps(event)}\n\n"


@router.get("/events")
async def speech_events():
    return EventSourceResponse(event_stream())

@router.get("/stream")
async def speech_stream():
    """
    SSE endpoint.
    """
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream"
    )