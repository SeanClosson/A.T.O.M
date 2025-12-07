from langchain.agents.middleware import AgentMiddleware, AgentState

class MemoryRetrievalMiddleware(AgentMiddleware):
    def __init__(self, memory, k=5):
        self.memory = memory
        self.k = k

    def before_model(self, state: AgentState, runtime):
        messages = state.get("messages", [])
        if not messages:
            return None

        # last user message
        last_user_msg = next(
            (m.content for m in reversed(messages) if getattr(m, "type", None) == "human"),
            None
        )

        if not last_user_msg:
            return None

        # retrieve relevant memories
        retrieved = self.memory.query(last_user_msg, k=self.k)
        if not retrieved:
            return None

        injected = runtime.create_message(  # IMPORTANT: create LCMessage object
            role="system",
            content="Relevant long-term memory:\n" + "\n".join(retrieved)
        )

        return {"messages": [injected]}
