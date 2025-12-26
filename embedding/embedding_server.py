from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from typing import List, Any
import uvicorn
import os
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Embedding Server", version="1.0.0")

# Load model (downloads automatically first time)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dims, fast
# MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"  # 768 dims, better quality
model = SentenceTransformer(MODEL_NAME)
logger.info(f"✅ Loaded model: {MODEL_NAME}")

class EmbeddingRequest(BaseModel):
    input: List[str]
    model: str = MODEL_NAME

class EmbeddingResponse(BaseModel):
    data: List[Any]
    model: str
    usage: dict

@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    try:
        if not request.input:
            raise HTTPException(status_code=400, detail="'input' must not be empty")
        
        texts = [str(text) for text in request.input]
        print(f"📝 Embedding texts: {texts[:1]}...")  # Debug log
        
        embeddings = model.encode(texts).tolist()
        
        # ✅ OpenAI EXACT response format
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "index": i,
                    "embedding": emb
                } 
                for i, emb in enumerate(embeddings)
            ],
            "model": request.model,
            "usage": {
                "prompt_tokens": len(texts) * 10,
                "total_tokens": len(texts) * 10
            }
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "model": MODEL_NAME}

@app.get("/models")
async def list_models():
    return [{"id": MODEL_NAME, "object": "model"}]

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")  # Bind to all interfaces
    port = int(os.getenv("PORT", 2000))
    logger.info(f"🚀 Starting embedding server on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")