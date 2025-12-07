from memory.background_worker import run_in_background
from langchain.agents.middleware import AgentMiddleware, AgentState
import time

class AsyncMemoryWriteMiddleware(AgentMiddleware):
    def __init__(self, memory, judge_model):
        self.memory = memory
        self.judge = judge_model

    def after_agent(self, state: AgentState, runtime):
        print("✅ AsyncMemoryWriteMiddleware fired")

        messages = state.get("messages", [])
        if not messages:
            return None

        last_user = next((m for m in reversed(messages) if m.type == "human"), None)
        last_ai = next((m for m in reversed(messages) if m.type == "ai"), None)

        if not last_user or not last_ai:
            return None

        user_text = last_user.content
        ai_text = last_ai.content

        print("🧠 MEMORY CANDIDATE:", user_text)

        # # ✅ ALWAYS SYNC SAVE FOR PREFERENCES
        # if any(x in user_text.lower() for x in ["my favourite", "my favorite", "i like", "i love"]):
        #     print("🔥 HIGH PRIORITY MEMORY SAVED SYNC")
        #     self.memory.add(
        #         user_text,
        #         metadata={"priority": "high", "timestamp": time.time()}
        #     )
        #     return None

        # ✅ EVERYTHING ELSE ASYNC
        def background_task():
            print("⚙️ BACKGROUND MEMORY TASK RUNNING")

            prompt = f"""
You are a strict long-term memory filter.

Save ONLY:
- Personal preferences (likes, favourites)
- Personal identity (name, location)
- Long-term goals
- Ongoing personal projects

DO NOT save:
- Questions
- Commands
- Casual conversation
- General knowledge
- Temporary information

Reply with ONLY one word:
yes or no

User: {user_text}
"""
# Assistant: {ai_text}
            result = self.judge.invoke(prompt)

            raw = result.content.lower()
            decision = "yes" if "yes" in raw else "no"

            print("🧪 JUDGE RAW:", result.content)
            print("✅ PARSED DECISION:", decision)

            if decision == "yes":
                print("✅ Passed Decision to save memory.")
                self.memory.add(
                    user_text,
                    metadata={"priority": "normal", "timestamp": time.time()}
                )
                print("✅ BACKGROUND MEMORY SAVED")
            else:
                print("❌ MEMORY REJECTED")

        run_in_background(background_task)
