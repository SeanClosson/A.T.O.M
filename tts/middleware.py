from langchain.agents.middleware import AgentMiddleware, wrap_tool_call
from tts.voice import voiceEngine

class TTSMiddleware(AgentMiddleware):
    def __init__(self, engine = voiceEngine):
        self.tts = engine

    def after_model(self, state, runtime):
        from tts.voice import voiceEngine
        self.tts = voiceEngine

        if not voiceEngine:
            return   # TTS not ready yet, just skip safely

        latest_message = state["messages"][-1]

        if not latest_message.content:
            return
        
        # send text to TTS queue (safe & sequential)
        self.tts.text_queue.put(latest_message.content)

    @wrap_tool_call
    def silence_during_tool(request, handler):
        # don't speak during tool execution
        return handler(request)
