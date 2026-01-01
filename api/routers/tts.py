from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import tts.voice as voice
import yaml
from fastapi.responses import StreamingResponse, FileResponse
import io
import wave
import soundfile as sf
import tempfile
import os

router = APIRouter(prefix="/api/tts", tags=["TTS"])

class TTSRequest(BaseModel):
    text: str


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f) or {}

def get_tts_status():
    import tts.voice as voice

    # If user disabled TTS
    if not config.get("USE_TTS", False):
        return {
            "status": "Disabled",
            "mode": "Off"
        }

    if not voice.voiceEngine:
        return {
            "status": "Offline",
            "detail": "TTS engine not initialized in runtime"
        }

    running = getattr(voice.voiceEngine, "running", False)

    mode = "Edge-TTS" if hasattr(voice.voiceEngine, "VOICE") else "Piper"

    return {
        "status": "Online" if running else "Idle",
        "mode": mode
    }


@router.get("/health")
async def tts_health():
    import tts.voice as voice

    print("DEBUG TTS HEALTH — voiceEngine =", voice.voiceEngine)

    return get_tts_status()


@router.post("/speak")
async def tts_speak(req: TTSRequest):
    """
    Push text into the TTS speech queue.
    Will NOT block. Returns immediately.
    """
    if not voice.voiceEngine:
        raise HTTPException(status_code=503, detail="TTS engine not initialized")

    try:
        clean = voice.voiceEngine.clean_for_tts(req.text)

        # streaming system uses queue
        voice.voiceEngine.text_queue.put(clean)

        return {
            "status": "queued",
            "text": clean
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")

# @router.post("/generate")
# async def tts_generate(req: TTSRequest):
#     if not voice.voiceEngine:
#         raise HTTPException(status_code=503, detail="TTS engine not initialized")

#     try:
#         text = voice.voiceEngine.clean_for_tts(req.text)

#         # 1️⃣ create temp wav file
#         with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
#             wav_path = tmp.name

#         # 2️⃣ synthesize EXACTLY like your working function
#         with wave.open(wav_path, "wb") as wav_file:
#             voice.voiceEngine.voice.synthesize_wav(text, wav_file)

#         # 3️⃣ read bytes
#         with open(wav_path, "rb") as f:
#             audio_bytes = f.read()

#         # cleanup
#         os.remove(wav_path)

#         return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"TTS generate failed: {e}")

@router.post("/generate")
async def tts_generate(req: TTSRequest):
    if not voice.voiceEngine:
        raise HTTPException(status_code=503, detail="TTS engine not initialized")

    try:
        text = voice.voiceEngine.clean_for_tts(req.text)

        # temp wav file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name

        # --- EDGE TTS SUPPORT ---
        if hasattr(voice.voiceEngine, "VOICE"):
            # Edge-TTS
            import edge_tts
            communicate = edge_tts.Communicate(text, voice.voiceEngine.VOICE)
            await communicate.save(wav_path)
        else:
            # Piper fallback
            with wave.open(wav_path, "wb") as wav_file:
                voice.voiceEngine.voice.synthesize_wav(text, wav_file)

        # return wav bytes
        with open(wav_path, "rb") as f:
            audio_bytes = f.read()

        os.remove(wav_path)
        return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generate failed: {e}")
