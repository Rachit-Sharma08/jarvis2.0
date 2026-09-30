import re

import config

PREFIX_RE = re.compile(
    r"^\s*("
    + "|".join(re.escape(a) for a in config.mode_aliases())
    + r")(?![ऀ-ॿ\w])[\s,.:!?-]*",
    re.IGNORECASE,
)

ALIASES = {a.lower(): m for m, names in config.MODE_ALIASES.items() for a in names}

NAMES = {"sunday": "Sunday", "prabh": "Prabh"}


def detect_mode(text: str, current_mode: str) -> tuple:
    """Message 'Sunday...' ya 'Prabh...' se shuru ho to mode badal do.

    Returns (mode, message_without_prefix).
    """
    if not text:
        return current_mode, text

    match = PREFIX_RE.match(text)
    if not match:
        return current_mode, text

    mode = ALIASES[match.group(1).lower()]
    rest = text[match.end():].strip()
    return mode, rest or text.strip()


def persona_for(mode: str) -> str:
    path = config.PERSONAS_DIR / f"{mode}.txt"
    return path.read_text(encoding="utf-8")


def display_name(mode: str) -> str:
    return NAMES.get(mode, NAMES[config.DEFAULT_MODE])