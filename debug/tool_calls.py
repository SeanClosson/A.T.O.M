# debug/tool_calls.py

TOOL_CALL_LOG = []

import datetime

def _sanitize(value):
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    return value


def record_tool_call(tool_name, metadata=None, success=True):
    if metadata is None:
        metadata = {}

    metadata = _sanitize(metadata)

    entry = {
        "tool": tool_name,
        "metadata": {
            "success": success,
            "tags": metadata.get("tags", "General"),
            **{k: v for k, v in metadata.items() if k != "tags"}
        },
        "timestamp": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    }

    TOOL_CALL_LOG.insert(0, entry)

    if len(TOOL_CALL_LOG) > 50:
        TOOL_CALL_LOG.pop()

def get_tool_log():
    return TOOL_CALL_LOG
