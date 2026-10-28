"""User ke baare me pakki baatein — local `data/profile.json` (chhota, insaan padh sake).

`core/memory.py` **baat-cheet** yaad rakhta hai (aakhri 12 turn, khud mit jaate
hain). Yahan **pakki baatein** hain: naam, sheher, pasand, routine — jo har
prompt me jaati hain, is liye Jarvis user ko pehchanta hai.

Likhta sirf `remember` tool hai (LLM user ki baat se), aur `forget`. Path kabhi
bahar se nahi aata — is liye koi file-system raasta yahan khulta hi nahi.
"""

import json
import os
import tempfile
from pathlib import Path

import config
from log_setup import get_logger

log = get_logger("profile")

DATA_DIR = Path(config.BASE_DIR) / "data"
PFILE = DATA_DIR / "profile.json"

MAX_FACTS = 40          # iske baad naya fact purane ko replace karega
MAX_KEY = 40
MAX_VALUE = 300
MAX_BLOCK = 600         # prompt me itna hi text (tokens bachane ke liye)


def _clean(text, limit: int) -> str:
    """Ek line, koi newline/control nahi — warna prompt ka dhaancha toot jaata hai."""
    raw = " ".join(str(text or "").split())
    return raw[:limit]


def load() -> dict:
    try:
        if PFILE.exists():
            data = json.loads(PFILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if k and v}
    except Exception as exc:
        log.warning("profile load fail: %s", exc)
    return {}


def _save(facts: dict) -> None:
    """Atomic: temp file + replace — beech me crash ho to purana profile bacha rahe."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(DATA_DIR), prefix="profile-", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(facts, handle, ensure_ascii=False, indent=2)
        os.replace(tmp, PFILE)
    except Exception as exc:
        log.error("profile save fail: %s", exc)


def remember(key: str, value: str) -> str:
    name = _clean(key, MAX_KEY).lower().replace(" ", "_")
    text = _clean(value, MAX_VALUE)
    if not name or not text:
        return "Key aur value dono chahiye."
    facts = load()
    if name not in facts and len(facts) >= MAX_FACTS:
        return (f"Profile full hai ({MAX_FACTS} baatein). Pehle `forget` se "
                f"koi purani baat hatao.")
    facts[name] = text
    _save(facts)
    return f"Yaad rakh liya: {name} = {text}"


def forget(key: str) -> str:
    name = _clean(key, MAX_KEY).lower().replace(" ", "_")
    facts = load()
    if name not in facts:
        return f"'{name}' profile me tha hi nahi."
    facts.pop(name)
    _save(facts)
    return f"Bhula diya: {name}"


def facts() -> list:
    return list(load().items())


def block() -> str:
    """Prompt ka hissa. Khaali ho to `""` — tab prompt badalta nahi."""
    items = facts()
    if not items:
        return ""
    lines = ["[USER PROFILE - user ke baare me yaad rakhi baatein; inhe sach maano]"]
    used = 0
    for key, value in items:
        line = f"- {key}: {value}"
        if used + len(line) > MAX_BLOCK:
            break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines)
