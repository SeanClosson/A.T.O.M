from langchain.agents.middleware import AgentMiddleware
from langchain.messages import SystemMessage

import re

def strip_memory_noise(results, max_len=200):
    """
    Handles:
    - list of strings
    - list of Documents
    - single string
    """

    # 🔥 if it's a single string, wrap it so we don't iterate characters
    if isinstance(results, str):
        results = [results]

    clean_memories = []

    for item in results:

        # Works with LangChain Docs or plain strings
        if hasattr(item, "page_content"):
            text = item.page_content
        else:
            text = str(item)

        if not text.strip():
            continue

        # remove (source={...}) junk
        text = re.sub(r"\(source=\{.*?\}\)", "", text, flags=re.DOTALL)

        # remove any {...} metadata blobs
        text = re.sub(r"\{.*?\}", "", text, flags=re.DOTALL)

        # remove [ ... ] metadata blobs
        text = re.sub(r"\[.*?\]", "", text)

        # collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # optional truncation
        if len(text) > max_len:
            text = text[:max_len].rstrip() + "..."

        if text:
            clean_memories.append(text)

    return clean_memories

# class MemoryInjectionMiddleware(AgentMiddleware):
#     def __init__(self, memory_store):
#         self.memory_store = memory_store

#     def before_model(self, state, runtime):
#         print("\n🧠 [Middleware] before_model triggered")

#         messages = state["messages"]
#         print(f"📝 Total messages in state: {len(messages)}")

#         # ---- find last user message ----
#         user_msg = None
#         for m in reversed(messages):
#             typ = getattr(m, "type", getattr(m, "role", None))
#             if typ in ("human", "user"):
#                 user_msg = m
#                 break

#         if not user_msg:
#             print("⚠️ No user message found. Skipping.")
#             return None

#         print(f"👤 Last user message: {user_msg.content}")

#         # retrieve contextual memory
#         # mem_text = self.memory_store.retrieve_context(user_msg.content)
#         memories = self.memory_store.similarity_search(user_msg.content, k=1)

#         mem_text = "\n".join(
#             f"- {doc.page_content} (source={doc.metadata})"
#             for doc in memories
#         )

#         if not mem_text or mem_text.strip() == "":
#             print("ℹ️ No relevant memory retrieved. Continuing without injection.")
#             return None
        
#         # clean = strip_memory_noise(mem_text)
#         # mem_text = "\n".join(f"- {m}" for m in clean)

#         print("✅ Memory retrieved successfully.")
#         print(f"✏️ Raw Memory: {mem_text}")
#         print(f"📦 Memory content length: {len(mem_text)} characters")
#         preview = mem_text[:300].replace("\n", " ")
#         print(f"🔍 Memory preview: {preview}...")

#         # injected = SystemMessage(
#         #     content=f"Relevant long-term memory:\n{mem_text}",
#         #     name="memory_context"
#         # )

#         # ---- Build the injected memory message ----
#         injected = SystemMessage(
#             name="memory_context",
#             content=f"Relevant long-term memory:\n{mem_text}"
#         )

#         new_messages = messages + [injected]

#         print("📎 Injected memory message into model context.")

#         return {
#             "messages": new_messages,
#             "injected_memory": True
#         }

#     def after_model(self, state, runtime):
#         print("\n🧠 [Middleware] after_model triggered")

#         msgs = state["messages"]

#         # check if we even injected anything
#         has_memory = any(
#             hasattr(m, "name") and m.name == "memory_context"
#             for m in msgs
#         )

#         if not has_memory:
#             print("ℹ No memory_context found. Nothing to clean.")
#             return None

#         print("🧹 Cleaning injected memory from state messages...")

#         cleaned = [
#             m for m in msgs
#             if not (hasattr(m, "name") and m.name == "memory_context")
#         ]

#         removed = len(msgs) - len(cleaned)
#         print(f"🗑️ Removed {removed} injected memory messages.")

#         return {
#             "messages": cleaned
#         }

def compress_memory(mem_text: str, max_chars: int = 400):
    """
    1) Remove metadata junk
    2) Normalize to short bullet items
    3) Trim hard length (safety cap)
    """

    # remove metadata parentheses junk
    import re
    mem_text = re.sub(r"\(source=.*?\)", "", mem_text, flags=re.DOTALL)

    # normalize whitespace
    mem_text = mem_text.strip()
    mem_text = mem_text.replace("\n\n", "\n")

    # enforce bullet formatting
    lines = []
    for line in mem_text.split("\n"):
        line = line.strip("-• ")
        if not line:
            continue

        # keep only the meaningful statement, trim long sentences
        if len(line) > 140:
            line = line[:140] + "…"

        lines.append(f"• {line}")

    seen = set()
    unique = []
    for line in lines:
        key = line.lower()
        if key not in seen:
            seen.add(key)
            unique.append(line)
    lines = unique

    compressed = "Relevant long-term memory:\n" + "\n".join(lines[:4])

    # hard safety clamp
    if len(compressed) > max_chars:
        compressed = compressed[:max_chars] + "…"

    return compressed

class MemoryInjectionMiddleware(AgentMiddleware):
    def __init__(self, memory_store):
        self.memory_store = memory_store

    def before_model(self, state, runtime):
        print("\n🧠 [Middleware] before_model triggered")

        msgs = state["messages"]

        # ---- find last user message ----
        user_msg = None
        for m in reversed(msgs):
            typ = getattr(m, "type", getattr(m, "role", None))
            if typ in ("human", "user"):
                user_msg = m
                break

        if not user_msg:
            print("⚠️ No user message found. Skipping.")
            return None

        memories = self.memory_store.similarity_search(user_msg.content, k=3)

        mem_text = "\n".join(
            f"- {doc.page_content} (source={doc.metadata})"
            for doc in memories
        )

        if not mem_text or not mem_text.strip():
            print("ℹ️ No memory found")
            return None
        
        mem_text = compress_memory(mem_text)

        print("✅ Memory retrieved successfully.")
        print(f"✏️ Raw Memory: {mem_text}")
        print(f"📦 Memory content length: {len(mem_text)} characters")
        preview = mem_text[:300].replace("\n", " ")
        print(f"🔍 Memory preview: {preview}...")

        # ---- Build the injected memory message ----
        injected = SystemMessage(
            name="memory_context",
            content=f"Relevant long-term memory:\n{mem_text}"
        )

        # ---- REBUILD LIST WITHOUT OLD MEMORY ----
        cleaned = [
            m for m in msgs
            if not (hasattr(m, "name") and m.name == "memory_context")
        ]

        # ---- INSERT memory context RIGHT AFTER SYSTEM ----
        new_messages = []
        inserted = False

        for m in cleaned:
            new_messages.append(m)

            if not inserted and isinstance(m, SystemMessage):
                new_messages.append(injected)
                inserted = True

        if not inserted:
            # fallback if no system message existed
            new_messages.insert(0, injected)

        print("📎 Injected memory context (replacing old instead of appending).")

        return {
            "messages": new_messages,
            "injected_memory": True
        }

    def after_model(self, state, runtime):
        # DO. NOTHING.
        print("\n🧠 [Middleware] after_model triggered — nothing to clean.")
        return None

import threading

JUDGED_MEMORY_CACHE = {}     # session_id -> last judged memory text
TURN_COUNTERS = {}           # session_id -> turn counter

class PeriodicJudgeMiddleware(AgentMiddleware):
    def __init__(self, judge_llm, memory_store, session_id: str, N=5):
        self.judge = judge_llm
        self.memory_store = memory_store
        self.session_id = session_id
        self.N = N

    def _get_turn_count(self):
        return TURN_COUNTERS.get(self.session_id, 0)

    def _set_turn_count(self, v):
        TURN_COUNTERS[self.session_id] = v

    def run_judge_sync(self, recent_messages):
        # print("⚙️ BACKGROUND JUDGE FOR MEMORY INJECTION RUNNING...")

        user_text = ""
        ai_text = ""

        for m in recent_messages:
            role = getattr(m, "type", getattr(m, "role", None))
            if role in ("human", "user"):
                user_text += f"{m.content}\n"
            else:
                ai_text += f"{m.content}\n"

        # ---- Pull vector DB relevant memories ----
        try:
            query = user_text.strip()[-500:] or user_text  # decent heuristic
            docs = self.memory_store.similarity_search(query, k=5)
            vector_memory_text = "\n".join(d.page_content for d in docs) if docs else "NONE"
        except Exception as e:
            print("❌ Vector DB lookup failed:", e)
            vector_memory_text = "NONE"

        # ---- Judge sees BOTH conversation + existing memories ----
        prompt = f"""
    You are a memory judge engine.

    You will receive:
    1) recent conversation context
    2) previously known long-term memories

    From BOTH sources, produce the BEST, CLEAN, RELEVANT
    memory context the assistant should keep in mind going forward.

    If there is real useful context, return a short set of bullet points.
    If nothing meaningful, reply with ONLY: NONE

    === Conversation Context ===
    User:
    {user_text}

    Assistant:
    {ai_text}

    === Existing Long-Term Memories ===
    {vector_memory_text}
    """
        from memory.memory_write_middleware import strip_think
        result = self.judge.invoke(prompt)

        # print(f'🧠 Judge Raw LLM Results: {result}')

        result = strip_think(result.content)

        # print(f'🧠 Judge Cleaned LLM Results: {result}')

        text = (
            result if isinstance(result, str)
            else getattr(result, "content", str(result))
        )

        if not text or text.strip().upper() == "NONE":
            print("ℹ️ Judge produced nothing useful")
            return

        JUDGED_MEMORY_CACHE[self.session_id] = text.strip()
        # print("💾 Cached judged+vector memory")


    def before_model(self, state, runtime):
        msgs = state["messages"]

        # count ONLY human turns
        last = msgs[-1]
        typ = getattr(last, "type", getattr(last, "role", None))

        if typ not in ("human", "user"):
            return None

        count = self._get_turn_count() + 1
        self._set_turn_count(count)

        if count % self.N != 0:
            # print(f"⏩ Not Judge Turn ({count})")
            return None

        # print(f"🧠 Judge Triggered at turn {count}")

        # Grab last N*2 to cover N exchanges safely
        recent = msgs[-(self.N * 2):]

        # 🔥 THIS was missing — launch judge in background thread 🔥
        threading.Thread(
            target=self.run_judge_sync,   # <-- your judge fn
            args=(recent,),
            daemon=True
        ).start()

        return None

    def after_model(self, state, runtime):
        return None
    
class JudgedMemoryInjectionMiddleware(AgentMiddleware):
    def __init__(self, session_id: str):
        self.session_id = session_id

    def before_model(self, state, runtime):
        msgs = state["messages"]

        # if no judged memory yet → skip
        mem_text = JUDGED_MEMORY_CACHE.get(self.session_id, None)
        if not mem_text:
            # print("ℹ️ No judged memory to inject yet")
            return None

        # consume once
        del JUDGED_MEMORY_CACHE[self.session_id]
        # print("📎 Injecting judged memory (one-time)")

        # print(f"✏️ Relevant judged context:\n{mem_text}")

        injected = SystemMessage(
            name="memory_context",
            content=f"Relevant judged context:\n{mem_text}"
        )

        # remove previous memory injection if exists
        cleaned = [
            m for m in msgs
            if not (hasattr(m, "name") and m.name == "memory_context")
        ]

        # insert after first system message
        new_messages = []
        inserted = False

        for m in cleaned:
            new_messages.append(m)
            if not inserted and isinstance(m, SystemMessage):
                new_messages.append(injected)
                inserted = True

        if not inserted:
            new_messages.insert(0, injected)

        return { "messages": new_messages }

    def after_model(self, state, runtime):
        return None