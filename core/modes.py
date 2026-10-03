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
    """Message 'Jarvis...' ya 'Prabh...' se shuru ho to mode badal do.

    `config.SUNDAY_ONLY` on hai to PRABH ka switch **band** hai — koi bhi
    message se prabh mode nahi jayega. Prabh ka code yahan maujood hai,
    hataya nahi gaya; sirf ek flag se band hai (Phase 5, sirf ek mode).

    Returns (mode, message_without_prefix).
    """
    if not text:
        return current_mode, text

    match = PREFIX_RE.match(text)
    if not match:
        return current_mode, text

    mode = ALIASES[match.group(1).lower()]
    rest = text[match.end():].strip()
    if config.SUNDAY_ONLY and mode != config.DEFAULT_MODE:
        # Blocked switch: text waise hi aage jayega, sirf mode nahi badlega.
        return current_mode, rest or text.strip()
    return mode, rest or text.strip()


def persona_for(mode: str) -> str:
    """Mode ka persona file. Naam `config.PERSONA_FILES` se aata hai — mode id
    `"sunday"` hai par file `jarvis.txt` (Step 1: naam badla, id nahi)."""
    name = config.PERSONA_FILES.get(mode, "%s.txt" % mode)
    path = config.PERSONAS_DIR / name
    return path.read_text(encoding="utf-8")


def display_name(mode: str) -> str:
    """Jo **user ko dikhta** hai.

    Default mode (id `"sunday"`) ka dikhne wala naam app ka naam hai —
    `config.ASSISTANT_NAME` = "Jarvis". Is liye jawab ke upar "SUNDAY" nahi,
    "JARVIS" aata hai, jabki andar ka id wahi rehta hai. Baaki mode (prabh)
    apna naam rakhta hai — wo dormant hai.
    """
    if mode == config.DEFAULT_MODE:
        return config.ASSISTANT_NAME
    return NAMES.get(mode, config.ASSISTANT_NAME)


def label(mode: str) -> str:
    """Jawab ke upar dikhne wala label: JARVIS ya PRABH."""
    return display_name(mode).upper()