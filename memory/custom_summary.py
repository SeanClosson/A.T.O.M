from langchain.agents.middleware import AgentMiddleware
from memory.background_worker import run_in_background

class AsyncSummarizationMiddleware(AgentMiddleware):
    def __init__(self, summary_model, threshold=4000):
        self.summary_model = summary_model
        self.threshold = threshold

    def after_agent(self, state, runtime):
        messages = state.get("messages", [])

        # compute token usage
        text = "\n".join(m.content for m in messages)
        token_count = self.summary_model.get_num_tokens(text)

        if token_count < self.threshold:
            return None

        def background_task():
            print("Starting BG Task")
            summary = self.summary_model.invoke(
                "Summarize this conversation:\n\n" + text
            ).content

            # Replace long history with summary
            state["messages"] = [runtime.create_message(
                role="system", content="Conversation summary:\n" + summary
            )]

        run_in_background(background_task)

        return None
