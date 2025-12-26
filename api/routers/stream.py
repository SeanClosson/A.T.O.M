# api/routers/stream.py

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from core.llm import LLM
import json
import asyncio
import yaml

router = APIRouter()
brain = LLM()

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file) or {}

async def stream_generator(user_input: str):
    try:
        for chunk in brain.generate_chunks(user_input, config['USER_ID']):
            event = f"data: {json.dumps({'delta': chunk})}\n\n"
            yield event
            await asyncio.sleep(0)
        # Send a final event to indicate completion
        yield "data: [DONE]\n\n"
    except Exception as e:
        # Send an error event
        error_event = f"data: {json.dumps({'error': str(e)})}\n\n"
        yield error_event

@router.get("")
def stream(message: str):
    return StreamingResponse(
        stream_generator(message),
        media_type="text/event-stream"
    )
