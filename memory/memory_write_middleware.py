from memory.background_worker import run_in_background
from langchain.agents.middleware import AgentMiddleware
import time
import re
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class MemoryDecision(BaseModel):
    """Structured decision for whether something should become long-term memory"""

    store: bool = Field(
        description="Whether this information should be saved as long-term memory"
    )

    type: Optional[Literal[
        "project",
        "goal",
        "preference",
        "skill",
        "fact",
        "concern"
    ]] = Field(
        default=None,
        description="Category of memory. Required only if store=true"
    )

    importance: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="How important this memory is (1 = trivial, 5 = highly important). Required if store=true"
    )

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="How confident the judge is that this is correct memory (0–1). Required if store=true"
    )

    text: Optional[str] = Field(
        default=None,
        # description="Compressed single-sentence factual memory that should be stored. Required if store=true"
        description=("Exactly one short factual sentence summarizing the memory. "
                    "Plain English. Objective. Under ~20 words. "
                    "MUST NOT include metadata, timestamps, reasoning, opinions, or narrative text. "
                    "Example: 'User prefers the BMW M3 GTR.' "
                    "REQUIRED if store=true.")
    )

    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional short keywords for indexing the memory"
    )

class MemoryJudgeResult(BaseModel):
    store: bool = Field(description="Whether to store memory")
    type: Literal["project", "goal", "preference", "skill", "fact", "concern"] = Field(default="fact")
    importance: float = Field(description="Importance 1-5")
    confidence: float = Field(description="Confidence 0-1")
    text: str = Field(description="ONE short factual sentence")
    tags: List[str] = Field(default_factory=list)

class ConsolidationDecision(BaseModel):
    action: Literal["keep_existing", "add_new", "replace_best"]
    updated_text: str | None = Field(
        default=None,
        description="Required when action is replace_best"
    )

THINK_BLOCK_REGEX = re.compile(r"<think>.*?</think>", re.DOTALL)

def strip_think(text: str) -> str:
    """
    Removes all <think>...</think> blocks from model output.
    """
    if not text:
        return text
    return re.sub(THINK_BLOCK_REGEX, "", text).strip()

import json
import time

def strip_think(text: str):
    # Safe cleaner in case your judge wraps JSON
    if "<think>" in text:
        try:
            text = text.split("</think>")[-1]
        except:
            pass
    return text.strip()

def run_in_background(fn):
    import threading
    threading.Thread(target=fn, daemon=True).start()

class AsyncMemoryWriteMiddleware(AgentMiddleware):
    def __init__(self, memory, judge_model):
        self.memory = memory
        self.judge = judge_model
        self.agent = None

    def after_agent(self, state, runtime):
        # print("✅ AsyncMemoryWriteMiddleware fired")

        messages = state.get("messages", [])
        if not messages:
            return None

        last_user = next((m for m in reversed(messages) if m.type == "human"), None)
        last_ai   = next((m for m in reversed(messages) if m.type == "ai"), None)

        if not last_user or not last_ai:
            return None

        user_text = last_user.content
        ai_text   = last_ai.content

        # print("🧠 MEMORY CANDIDATE:", user_text)

        def background_task():
            # print("⚙️ BACKGROUND MEMORY TASK RUNNING")

            # ----------------------------------------------------
            # JUDGE #1 — Is this memory-worthy at all?
            # ----------------------------------------------------
            prompt = f"""
You are a long-term memory formation engine for an AI assistant.

You must decide whether this interaction contains something worth remembering
for the user's future interactions.

Save ONLY if it is:
- a long-term goal
- a personal preference
- an identity fact
- an ongoing project
- an emotionally meaningful concern

DO NOT save:
- questions
- commands
- temporary info
- jokes
- general chit chat

If storing, compress it into ONE short factual sentence.
Assign:
- type: project | goal | preference | skill | fact | concern
- importance: 1 to 5
- confidence: 0 to 1
- tags: list of short keywords

IF store=true, YOU MUST INCLUDE:
- text: ONE short factual sentence describing the memory

Reply ONLY in JSON. 
If not worth saving, reply with:
{{ "store": false }}

User said:
{user_text}

Assistant replied:
{ai_text}
"""

            result = self.judge.invoke(prompt)
            clean = strip_think(result.content)

            # judge1 = self.judge.with_structured_output(MemoryJudgeResult)

            # result = judge1.invoke(prompt)

            # print("🧪 JUDGE RAW:", result.content)
            # print("🧽 CLEAN:", clean)

            try:
                data = json.loads(clean)
                # data = result["structured_response"]
            except Exception:
                # print("\n❌ Judge returned invalid JSON. Rejecting.\n")
                return

            if not data.get("store"):
                # print("\n❌ MEMORY REJECTED BY JUDGE\n")
                return

            required = ["type", "importance", "confidence", "text"]
            if not all(k in data for k in required):
                # print("\n❌ Judge missing required fields. Rejecting.\n")
                return

            tags = data.get("tags", [])
            if isinstance(tags, list):
                tags = ", ".join(tags)

            # ----------------------------------------------------
            # STEP 2 — Retrieve similar memories
            # ----------------------------------------------------
            try:
                similar = self.memory.search(
                    query=data["text"],
                    top_k=5
                )
            except Exception as e:
                # print("\n⚠️ Retrieval failed, fallback to normal save:\n", e)
                similar = []

            existing_memories = []
            for m in similar:
                existing_memories.append({
                    "id": m.get("id", None),
                    "text": m.get("text", ""),
                    "type": m.get("metadata", {}).get("type", ""),
                    "importance": m.get("metadata", {}).get("importance", 1),
                    "confidence": m.get("metadata", {}).get("confidence", 0),
                    "score": m.get("score", 0)
                })

            # ----------------------------------------------------
            # JUDGE #2 — Consolidation Decision
            # ----------------------------------------------------
            consolidation_prompt = (
f"You are a long-term memory consolidation engine.\n\n"
f"Here is a NEW candidate memory:\n"
f"{json.dumps(data, indent=2)}\n\n"
f"Here are EXISTING similar memories:\n"
f"{json.dumps(existing_memories, indent=2)}\n\n"
"Decide ONE of the following actions:\n"
"- \"keep_existing\"  → do nothing\n"
"- \"add_new\"        → store this as an additional memory\n"
"- \"replace_best\"   → replace the most relevant existing memory with an improved one\n\n"
"Rules:\n"
"- Prefer replacing if the new memory is higher importance or clearer.\n"
"- Prefer skipping if the new memory is weaker or redundant.\n"
"- Prefer adding if it is meaningfully different.\n\n"
"If replace_best:\n"
"Return a new compressed memory summary text.\n\n"
"Reply ONLY valid JSON like:\n"
"{\n"
"  \"action\": \"...\",\n"
"  \"updated_text\": \"...\"\n"
"}"
)

            decision = self.judge.invoke(consolidation_prompt)
            decision_clean = strip_think(decision.content)

            # judge2 = self.judge.with_structured_output(ConsolidationDecision)

            # decision = judge2.invoke(consolidation_prompt)


            # print("🧪 CONSOLIDATION RAW:", decision.content)
            # print("🧽 CLEAN:", decision_clean)

            try:
                decision_json = json.loads(decision_clean)
            except Exception:
                # print("\n❌ Consolidation judge JSON invalid, fallback to add_new\n")
                decision_json = {"action": "add_new"}

            action = decision_json.get("action", "add_new")
            updated_text = decision_json.get("updated_text", data["text"])

            # ----------------------------------------------------
            # APPLY DECISION
            # ----------------------------------------------------
            if action == "keep_existing":
                # print("\n🛑 Judge decided existing memory is better. Skipping save.\n")
                return

            elif action == "replace_best" and existing_memories:
                best = max(existing_memories, key=lambda x: x.get("score", 0))

                if not best.get("id"):
                    # print("\n⚠️ No memory ID available to update. Falling back to save new.\n")
                    pass
                else:
                    try:
                        self.memory.update(
                            id=best["id"],
                            new_text=updated_text
                        )
                        # print("\n♻️ Memory replaced and consolidated.\n")
                        return
                    except Exception as e:
                        # print("\n❌ Replace failed, fallback saving new:", e)
                        pass

            # print("\n➕ Judge approved NEW memory. Saving…\n")

            try:
                self.memory.add(
                    text=data["text"],
                    metadata={
                        "type": data["type"],
                        "importance": data["importance"],
                        "confidence": data["confidence"],
                        "tags": tags,
                        "timestamp": time.time()
                    }
                )
                # print("\n✅ MEMORY SAVED\n")
            except Exception as e:
                # print("\n❌ Memory write failed:", e)
                pass

        run_in_background(background_task)
        return None