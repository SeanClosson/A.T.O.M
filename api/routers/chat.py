# api/routers/chat.py

from fastapi import APIRouter
from llm import LLM

router = APIRouter()
brain = LLM()

@router.post("/")
def chat(payload: dict):
    user_input = payload.get("message", "")
    full_output = ""

    for chunk in brain.generate_chunks(user_input):
        full_output += chunk

    return {"response": full_output}
