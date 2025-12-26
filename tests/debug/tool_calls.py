TOOL_CALL_LOG = []

def record_tool_call(name: str, payload=None):
    TOOL_CALL_LOG.append({
        "tool": name,
        "payload": payload
    })