# json_logging_middleware.py

import json
from datetime import datetime
from typing import Any

from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    wrap_model_call,
    wrap_tool_call,
)


def _serialize(x: Any):
    try:
        json.dumps(x)
        return x
    except Exception:
        return repr(x)


class JSONLoggingMiddleware(AgentMiddleware):
    """
    Logs agent lifecycle + tool calls in JSON.
    Works with create_agent().
    """

    def __init__(self, output_file: str | None = None):
        self.output_file = output_file

    def _emit(self, payload: dict):
        payload["timestamp"] = datetime.utcnow().isoformat() + "Z"

        text = json.dumps(
            payload,
            ensure_ascii=False,   # keep real characters instead of \u2019
            separators=(",", ":") # compact JSON, stable formatting
        )

        if self.output_file:
            with open(self.output_file, "a") as f:
                f.write(text + "\n")   # <-- one JSON per line
        else:
            print(text)

    # ---- BEFORE MODEL ----
    def before_model(self, state: AgentState, runtime) -> dict | None:
        self._emit({
            "phase": "before_model",
            "messages_count": len(state.get("messages", [])),
        })
        return None

    # ---- AFTER MODEL ----
    def after_model(self, state: AgentState, runtime) -> dict | None:
        last = None
        try:
            last = state["messages"][-1].content
        except Exception:
            pass

        self._emit({
            "phase": "after_model",
            "last_message": _serialize(last),
        })
        return None

    # ---- MODEL WRAP ----
    @wrap_model_call
    def log_model(self, request, handler):
        self._emit({
            "phase": "wrap_model_call_start",
            "model": _serialize(getattr(request, "model", None)),
            "inputs": _serialize(getattr(request, "inputs", None)),
        })

        result = handler(request)

        self._emit({
            "phase": "wrap_model_call_end",
            "outputs": _serialize(getattr(result, "output", None)),
        })

        return result

    # ---- TOOL WRAP ----
    @wrap_tool_call
    def log_tool(self, request, handler):
        self._emit({
            "phase": "wrap_tool_call_start",
            "tool_name": request.tool_call.get("name"),
            "tool_args": _serialize(request.tool_call.get("args", {})),
        })

        result = handler(request)

        self._emit({
            "phase": "wrap_tool_call_end",
            "tool_name": request.tool_call.get("name"),
            "tool_result": _serialize(getattr(result, "output", None)),
        })

        return result
