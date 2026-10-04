"""Wake phrase pakadna — pure functions. Na audio, na model, na Vosk.

Grammar me sirf 4 shabd hain (`config_wake.WAKE_GRAMMAR`), is liye fuzzy match
ki zarurat nahi. Bas itna karna hai:

1. `normalize()` — punctuation hatao, case hatao, space theek karo
2. `tokens()`   — `[unk]` jaise filler hatao
3. `hit()`      — kya koi wake shabd hai?
4. `phrase()`   — wake shabd wala hissa (log + HUD ke liye)

Ye file sabse aasan hai — is ka pura test `hit()`/`phrase()` par hi hai.
"""

import config

FILLER = ("unk", "uh", "um", "hmm", "mm")

GREETING = ("hello", "hey", "hi", "hlo", "yo", "okay", "ok", "helo")


def normalize(text: str) -> str:
    """`"Hello, Jarvis!"` -> `"hello jarvis"`"""
    cleaned = str(text or "").lower()
    for ch in ".,!?;:-_\"'()[]":
        cleaned = cleaned.replace(ch, " ")
    return " ".join(cleaned.split())


def tokens(text: str) -> list:
    """Saaf shabd ki list — filler aur khali shabd hata kar.

    Grammar me `[unk]` ek literal shabd hai; `normalize()` bracket hata deta hai
    is liye yahan `unk` likha hai (warna filler list me koi entry bekaar hoti)."""
    return [word for word in normalize(text).split() if word not in FILLER]


def hit(text: str) -> bool:
    """Text me wake shabd hai? -> bool. `''`, None, 'xyz' sab False."""
    words = set(tokens(text))
    return any(word in words for word in config.WAKE_WORDS)


def phrase(text: str) -> str:
    """Wake shabd wala hissa — greeting sahit. `''` agar wake word hi na ho.

    `"hey jarvis kholo"` -> `"hey jarvis"` (trigger ke liye yahi chahiye).
    """
    words = tokens(text)
    for i, word in enumerate(words):
        if word not in config.WAKE_WORDS:
            continue
        start = i - 1 if i > 0 and words[i - 1] in GREETING else i
        return " ".join(words[start:i + 1])
    return ""
