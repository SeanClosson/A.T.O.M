# api/routers/chat.py

from fastapi import APIRouter
from core.llm import LLM
import yaml

router = APIRouter()
brain = LLM()

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file) or {}

@router.post("/")
def chat(payload: dict):
    user_input = payload.get("message", "")
    full_output = ""

    for chunk in brain.generate_chunks(user_input, config['USER_ID']):
        full_output += chunk

    return {"response": full_output}
