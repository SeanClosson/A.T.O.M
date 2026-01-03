from fastapi import APIRouter
from memory.chroma_store import get_chroma_store
from datetime import datetime

router = APIRouter(
    prefix="/api/memory",
    tags=["Memory"]
)

def normalize_timestamp(ts):
    if ts is None:
        return datetime.utcnow()

    # If timestamp is already datetime
    if isinstance(ts, datetime):
        return ts

    # If timestamp is numeric (unix)
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts)

    # If ISO string / any string
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts)
        except:
            try:
                # fallback if stored weirdly
                return datetime.utcfromtimestamp(float(ts))
            except:
                return datetime.utcnow()

    # Fallback
    return datetime.utcnow()


@router.get("")
async def get_recent_memory():
    try:
        store = get_chroma_store()

        results = store.get(
            include=["documents", "metadatas"]
        )

        documents = results.get("documents", []) or []
        metadatas = results.get("metadatas", []) or []

        memory_items = []

        for doc, meta in zip(documents, metadatas):
            raw_ts = (
                meta.get("timestamp")
                or meta.get("time")
            )

            ts = normalize_timestamp(raw_ts)

            memory_items.append({
                "content": doc,
                "timestamp": ts.isoformat(), # return clean ISO
                "_sort": ts                  # internal sort value
            })

        # sort newest → oldest
        memory_items.sort(
            key=lambda x: x["_sort"],
            reverse=True
        )

        # trim
        memory_items = memory_items[:15]

        return {"memory": memory_items}

    except Exception as e:
        print("MEMORY API ERROR:", e)
        return {
            "memory": [],
            "error": str(e)
        }
