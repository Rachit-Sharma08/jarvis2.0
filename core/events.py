STATUS_VALUES = ("idle", "listening", "thinking", "speaking")


def status(value: str) -> dict:
    if value not in STATUS_VALUES:
        raise ValueError(f"bad status: {value}")
    return {"type": "status", "value": value}


def message(role: str, text: str) -> dict:
    return {"type": "message", "role": role, "text": text}


def log(text: str, level: str = "info", data: dict = None) -> dict:
    event = {"type": "log", "level": level, "text": text}
    if data:
        event["data"] = data
    return event