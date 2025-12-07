# async_memory_and_summary_middleware.py
from langchain.agents.middleware import AgentMiddleware, AgentState
from typing import Optional
import time

class AsyncMemoryWriteMiddleware(AgentMiddleware):
    def __init__(self, memory: LongTermMemory, judge_model, bg_worker,
                 min_len: int = 6, pattern_filter: Optional[list] = None):
        """
        memory: LongTermMemory instance
        judge_model: chat model with .invoke()
        bg_worker: BackgroundWorker instance
        min_len: skip very short messages
        pattern_filter: list of lower-case patterns that trigger immediate store without LLM
        """
        self.memory = memory
        self.judge = judge_model
        self.bg = bg_worker
        self.min_len = min_len
        self.pattern_filter = pattern_filter or [
            "my name is", "i live in", "my birthday", "born on", "i work at",
            "i'm from", "i am from", "i like", "i love", "remember that", "my favorite"
        ]

    def after_agent(self, state: AgentState, runtime):
        # Non-blocking: gather info and submit to background worker
        print("🧠 MEMORY MIDDLEWARE HIT")

        self.memory.add("TEST_WRITE_FROM_ATOM", metadata={"test": True})
        print("✅ FORCED SYNC MEMORY WRITE EXECUTED")

        messages = state.get("messages", []) or []
        last_user = next((m for m in reversed(messages) if getattr(m, "type", None) == "human"), None)
        last_ai = next((m for m in reversed(messages) if getattr(m, "type", None) == "ai"), None)
        if not last_user or not last_ai:
            return None

        user_text = getattr(last_user, "content", "") or ""
        ai_text = getattr(last_ai, "content", "") or ""

        # heuristics: skip trivial or question-like content
        if len(user_text.strip()) < self.min_len:
            return None
        lowered = user_text.lower()
        # If any strong pattern matches, store immediately without LLM
        for p in self.pattern_filter:
            if p in lowered:
                # do simple add in background
                def add_job():
                    self.memory.add(user_text, metadata={"auto": True, "trigger": p, "timestamp": time.time()})
                self.bg.submit(add_job, job_meta={"type": "memory_direct", "trigger": p})
                return None

        # else schedule LLM judge in background
        def background_task():
            try:
                prompt = (f"You are a memory classifier. Decide if the user message below should be saved "
                          f"as long-term memory. Reply only 'yes' or 'no'.\n\nUser: {user_text}\n\nAssistant: {ai_text}")
                res = self.judge.invoke(prompt)
                decision = getattr(res, "content", "").lower().strip()
                if decision.startswith("yes"):
                    self.memory.add(user_text, metadata={"auto": False, "timestamp": time.time()})
            except Exception as e:
                print("[AsyncMemoryWriteMiddleware] background_task error:", e)

        self.bg.submit(background_task, job_meta={"type": "memory_judge"})
        return None


class AsyncSummarizationMiddleware(AgentMiddleware):
    def __init__(self, summary_model, bg_worker, token_threshold: int = 4000, tokenizer=None):
        """
        summary_model: Chat model with .invoke() to summarize text
        bg_worker: BackgroundWorker instance
        tokenizer: function(text) -> token_count. If None, summarization will run only if length > threshold chars
        token_threshold: integer
        """
        self.summary_model = summary_model
        self.bg = bg_worker
        self.token_threshold = token_threshold
        self.tokenizer = tokenizer

    def after_agent(self, state: AgentState, runtime):
        messages = state.get("messages", []) or []
        # build the conversation text (safe)
        text = "\n".join([getattr(m, "content", "") or "" for m in messages])

        # decide whether to summarize
        will_summarize = False
        if self.tokenizer:
            try:
                tokcount = self.tokenizer(text)
                will_summarize = tokcount > self.token_threshold
            except Exception:
                # fallback to character length
                will_summarize = len(text) > (self.token_threshold * 3)
        else:
            will_summarize = len(text) > (self.token_threshold * 3)

        if not will_summarize:
            return None

        # background summary job
        def summary_job():
            try:
                prompt = "Summarize the following conversation into a short concise summary suitable for long-term context:\n\n" + text
                res = self.summary_model.invoke(prompt)
                summary = getattr(res, "content", "")
                # Here: decide where to store the summary. TWO options:
                # 1) Append to LongTermMemory (if available elsewhere) — recommended
                # 2) Persist to a conversation DB or file, or call a callback that merges it into state
                # We'll call runtime.create_message only if runtime exposes a thread-safe callback.
                try:
                    # Attempt to persist summary to a file (append)
                    with open("conversation_summaries.txt", "a", encoding="utf-8") as f:
                        f.write(f"\n---\n{time.ctime()} SUMMARY:\n{summary}\n")
                except Exception as e:
                    print("[AsyncSummarizationMiddleware] failed to write summary file:", e)
            except Exception as e:
                print("[AsyncSummarizationMiddleware] summary_job error:", e)

        self.bg.submit(summary_job, job_meta={"type": "summarize"})
        return None
