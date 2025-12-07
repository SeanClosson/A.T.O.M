from langchain.agents.middleware import AgentMiddleware, AgentState
import json
import time


class TokenDebugMiddleware(AgentMiddleware):
    def __init__(self, tokenizer, verbose=True):
        self.tokenizer = tokenizer
        self.verbose = verbose

    def count_tokens(self, messages):
        """Token count for LC message objects."""
        if not messages:
            return 0

        text = ""
        for m in messages:
            role = getattr(m, "type", "unknown")
            content = getattr(m, "content", "")
            text += f"{role}: {content}\n"

        return self.tokenizer(text)

    # ---- HOOKS ---- #

    def before_agent(self, state: AgentState, runtime):
        msgs = state.get("messages", [])
        tok = self.count_tokens(msgs)

        if self.verbose:
            print("\n=== 🟧 TOKEN DEBUG (before agent) ===")
            print(f"Token count entering middleware chain: {tok}")

        return None

    def before_model(self, state: AgentState, runtime):
        msgs = state.get("messages", [])
        tok = self.count_tokens(msgs)

        if self.verbose:
            print("\n=== 🟦 TOKEN DEBUG (before model) ===")
            print(json.dumps({
                "event": "before_model",
                "tokens_before": tok,
                "messages_count": len(msgs),
                "timestamp": time.time(),
            }, indent=2))

        return None

    def after_model(self, state: AgentState, runtime):
        msgs = state.get("messages", [])
        tok = self.count_tokens(msgs)

        if self.verbose:
            print("\n=== 🟩 TOKEN DEBUG (after model) ===")
            print(json.dumps({
                "event": "after_model",
                "tokens_after": tok,
                "messages_count": len(msgs),
                "timestamp": time.time(),
            }, indent=2))

        return None

    def after_agent(self, state: AgentState, runtime):
        msgs = state.get("messages", [])
        tok = self.count_tokens(msgs)

        if self.verbose:
            print("\n=== 🟥 TOKEN DEBUG (after agent) ===")
            print(f"Token count after middleware chain: {tok}")

        return None
