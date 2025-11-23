# api/server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import chat, stream, stt, system

app = FastAPI(title="ATOM API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["chat"])  # Gives full output
app.include_router(stream.router, prefix="/api/chat/stream", tags=["stream"])      # Gives chunks in output for streaming
app.include_router(system.router, prefix="/api/system", tags=["system"])        
app.include_router(stt.router, prefix="/api/stt", tags=["stt"])
