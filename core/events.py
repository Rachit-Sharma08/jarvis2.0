STATUS_VALUES = ("idle", "listening", "transcribing", "thinking", "speaking")


def status(value: str) -> dict:
    if value not in STATUS_VALUES:
        raise ValueError(f"bad status: {value}")
    return {"type": "status", "value": value}


def message(role: str, text: str, label: str = "") -> dict:
    """Role ke saath message. `label` = SUNDAY / PRABH (jawab ke upar dikhta hai)."""
    event = {"type": "message", "role": role, "text": text}
    if label:
        event["label"] = label
    return event


def log(text: str, level: str = "info", data: dict = None) -> dict:
    event = {"type": "log", "level": level, "text": text}
    if data:
        event["data"] = data
    return event


def confirm(request_id: str, tool: str, detail: str, timeout: int, approval_hash: str) -> dict:
    """UI ka Allow/Deny card. Hash ke bina koi approve nahi ho sakta."""
    return {
        "type": "confirm",
        "id": request_id,
        "tool": tool,
        "detail": detail,
        "timeout": timeout,
        "hash": approval_hash,
    }


def activity(tool: str, decision: str, text: str) -> dict:
    """ACTIVITY panel ki ek line."""
    return {"type": "activity", "tool": tool, "decision": decision, "text": text}