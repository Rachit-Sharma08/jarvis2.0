"""logs/actions.log — har tool call ka hisaab, secrets mask karke.

Do tarah se chhupaate hain:
1. Jo asli key abhi `os.environ` me hain (API_KEY/TOKEN/SECRET naam wale) — wo
   value hi jahan bhi dikhe, `***` ho jaata hai.
2. Key jaise pattern (gsk_, sk_, AIza, AQ., Bearer, api_key=...).
"""

import os
import re
import threading
from datetime import datetime
from pathlib import Path

import config

_lock = threading.Lock()
_MASK = "***"

_SECRET_ENV = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)
_SHAPES = (
    re.compile(r"gsk[_-][A-Za-z0-9]{10,}"),
    re.compile(r"nvapi[_-][A-Za-z0-9_\-]{10,}"),
    re.compile(r"sk[_-][A-Za-z0-9_\-]{10,}"),
    re.compile(r"AIza[A-Za-z0-9_\-]{10,}"),
    re.compile(r"\bAQ\.[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bbearer\s+[A-Za-z0-9._\-]{8,}", re.IGNORECASE),
    re.compile(r"(?i)\b(api[_-]?key|token|secret|password|authorization)\b\s*[=:]\s*\S{6,}"),
    re.compile(r"(?i)\b[a-z_]*key[a-z_]*\b\s*=\s*[^\s\"',;)]{8,}"),
)


def _live_values() -> tuple:
    """Abhi is waqt `os.environ` me jo asli keys hain. Har call par fresh padhta
    hai — taaki nayi key baad me daali jaaye to wo bhi mask ho."""
    out = []
    for name, value in os.environ.items():
        if len(value) >= 12 and _SECRET_ENV.search(name):
            out.append(value)
    return tuple(sorted(set(out), key=len, reverse=True))


def mask(text) -> str:
    """Har secret ko *** bana do. Text chhota bhi ho to koi crash nahi."""
    out = str(text)
    for value in _live_values():
        if value in out:
            out = out.replace(value, _MASK)
    for regex in _SHAPES:
        out = regex.sub(_MASK, out)
    return out


def _clean(value) -> str:
    text = mask(value)
    text = " ".join(text.split())
    return text[: config.TOOL_OUTPUT_LIMIT]


def log_action(mode: str, tool: str, args: dict, decision: str, result: str) -> str:
    """Ek line likho: samay, mode, tool, args, faisla, natija."""
    line = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | mode={mode} | tool={tool} | "
        f"args={_clean(args)} | decision={decision} | result={_clean(result)}"
    )
    with _lock:
        Path(config.ACTION_LOG).parent.mkdir(parents=True, exist_ok=True)
        with open(config.ACTION_LOG, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    return line
