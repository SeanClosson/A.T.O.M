import re, json
from memory.chroma_store import get_chroma_store
from memory.long_term_memory import LongTermMemory
from pathlib import Path
import yaml
from langchain.tools import tool
import threading
from pydantic import BaseModel
from typing import Literal, Optional

try:
    if not Path('config.yaml').exists():
        raise FileNotFoundError(f"Config file 'config.yaml' not found.")

    with open('config.yaml', "r") as file:
        config = yaml.safe_load(file) or {}
except Exception as e:
    print(f"[ERROR] Failed to load configuration: {e}")
    config = {}

vector_store = get_chroma_store()
long_term_memory = LongTermMemory(store=vector_store)

def _clean(text: str):
    text = re.sub(r"\(source=\{.*?\}\)", "", text, flags=re.DOTALL)
    text = re.sub(r"\{.*?\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\[.*?\]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def _compress(memories, max_chars=400):
    lines = []
    seen = set()

    for text, score in memories:
        t = text.strip("-• ")

        if len(t) > 140:
            t = t[:140] + "…"

        key = t.lower()
        if key in seen:
            continue

        seen.add(key)
        lines.append(f"• {t}")

    block = "\n".join(lines[:4])

    if len(block) > max_chars:
        block = block[:max_chars] + "…"

    return block

def retrieve_memory(query: str) -> str:
    """
    Retrieve relevant long-term memory from Chroma.
    Returns a short compressed memory block or empty string.
    """

    store = get_chroma_store()

    results = store.similarity_search_with_relevance_scores(query, k=4)

    filtered = []
    for doc, score in results:
        if not doc or not doc.page_content.strip():
            continue
        if score < 0.35:
            continue
        filtered.append((_clean(doc.page_content), score))

    if not filtered:
        return ""

    return "Relevant long-term memory:\n" + _compress(filtered)

THINK_BLOCK_REGEX = re.compile(r"<think>.*?</think>", re.DOTALL)

def strip_think(text: str):
    if not text:
        return text
    try:
        text = re.sub(THINK_BLOCK_REGEX, "", text)
        if "</think>" in text:
            text = text.split("</think>")[-1]
    except:
        pass
    return text.strip()

def _run_async(fn):
    threading.Thread(target=fn, daemon=True).start()

class MemoryDecision(BaseModel):
    action: Literal["add_new", "update_existing", "skip"]
    memory_id: Optional[str] = None

    class Config:
        extra = "forbid"

@tool
def write_memory_tool_async(memory_text: str, metadata: dict = None) -> str:
    """
    Asynchronously process and store long-term memory using a judge LLM.

    Flow (non-blocking):
    - Always treat incoming memory as valid
    - Search for similar existing memories
    - Ask judge LLM to decide:
        - add_new          -> store as separate memory
        - update_existing  -> replace an existing memory
        - skip             -> do nothing
    - Apply DB changes in the background
    - Tool returns immediately
    """

    if not memory_text or not memory_text.strip():
        return "⚠️ Skipping empty memory text"

    metadata = metadata or {}
    metadata.setdefault("type", "fact")
    metadata.setdefault("importance", 3)
    metadata.setdefault("confidence", 0.7)

    def _sanitize_metadata(meta: dict):
        def flat(v):
            if isinstance(v, list):
                return ", ".join(map(str, v)) if v else None
            if isinstance(v, dict):
                return json.dumps(v)
            return v

        clean = {}
        for k, v in (meta or {}).items():
            clean[k] = flat(v)

        # nuclear fix: guarantee tags can never be list
        if "tags" in clean and isinstance(clean["tags"], list):
            clean["tags"] = ", ".join(map(str, clean["tags"])) if clean["tags"] else None

        return clean


    def background_task():
        print("⚙️ BACKGROUND MEMORY TASK STARTED")

        from core.llm import LLM
        judge_model = LLM().summary_model
        # print("SUMMARY MODEL =", judge_model)

        # ----------------------------------
        # 1️⃣ Get Similar Memories
        # ----------------------------------
        similar = long_term_memory.search(
            query=memory_text,
            top_k=5
        )

        # ----------------------------------
        # 2️⃣ Ask Judge LLM
        # ----------------------------------
        prompt = f"""
You are a long-term memory controller.

NEW MEMORY:
{json.dumps({"text": memory_text, "metadata": metadata}, indent=2)}

SIMILAR EXISTING MEMORIES:
{json.dumps(similar, indent=2)}

Decide EXACTLY one action:
- "add_new"          → store this as an additional new memory
- "update_existing"  → replace/improve one existing similar memory
- "skip"             → do nothing

If update_existing, you MUST include the memory id:

{{
  "action": "...",
  "memory_id": "..."
}}
"""
        # agent = create_agent(judge_model, response_format=MemoryDecision)
        structured = judge_model.with_structured_output(MemoryDecision)
        decision = structured.invoke(prompt)

        action = decision.action
        mem_id = getattr(decision, "memory_id", None)

        def _final_metadata(meta):
            meta = meta or {}
            # FORCE TAGS TO VALID VALUE SO setdefault NEVER FIRES
            meta["tags"] = ", ".join(meta.get("tags", [])) if isinstance(meta.get("tags"), list) else (
                meta.get("tags") if isinstance(meta.get("tags"), (str, int, float, bool)) else ""
            )
            return meta

        # ----------------------------------
        # APPLY DECISION
        # ----------------------------------
        if action == "add_new":
            # print("➕ JUDGE → ADD NEW")
            long_term_memory.add(memory_text, _final_metadata(metadata))
            return

        if action == "update_existing":
            if not mem_id:
                # print("❌ Judge requested update but no memory_id provided")
                return

            # print(f"♻️ JUDGE → UPDATE MEMORY {mem_id}")
            long_term_memory.update(
                id=mem_id,
                new_text=memory_text,
                new_metadata=_final_metadata(metadata)
            )
            return

        # print("🛑 JUDGE → SKIP (No change)")
    
    _run_async(background_task) 
    return "🧠 Memory task scheduled asynchronously."