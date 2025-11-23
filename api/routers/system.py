# api/routers/system.py

from fastapi import APIRouter
import time

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}

@router.get("/version")
def version():
    return {"version": "1.0", "api": "ATOM API"}
