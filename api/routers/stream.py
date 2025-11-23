# api/routers/stream.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from llm import LLM
import json
import asyncio

router = APIRouter()
brain = LLM()

async def stream_generator(user_input: str):
    for chunk in brain.generate_chunks(user_input):
        event = f"data: {json.dumps({'delta': chunk})}\n\n"
        yield event
        await asyncio.sleep(0)

@router.get("")
def stream(message: str):
    return StreamingResponse(
        stream_generator(message),
        media_type="text/event-stream"
    )
