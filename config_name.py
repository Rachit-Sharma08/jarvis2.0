"""Assistant ka naam + usko bulane ke shabd. `config.py` inhe re-export karta hai.

Step 1 me app ka naam **Sunday → Jarvis** kiya gaya. Do hisse alag-alag:

1. **Jo user ko dikhta ya sunai deta hai** → `ASSISTANT_NAME` / `DISPLAY_NAME`
   se: HUD title, orb ka beech, tray tooltip, Edge window title, persona,
   spoken lines, Desktop shortcut, README/docs.
2. **Jo sirf andar hai → bilkul nahi badla.** Mode id `"sunday"`,
   `PRABH_*` env names, `DEFAULT_MODE`, `data/` ka lock — ye sab jaane
   chahiye taaki purana profile/lock na toote. Mode `"sunday"` ka **dikhne
   wala** naam ab `Jarvis` hai (`core/modes.display_name()`), isliye jawab ke
   upar "SUNDAY" nahi, "JARVIS" aata hai.

`DISPLAY_NAME` wo chhota-brand roop hai jo HUD ke upar bade akshar me hai.
Vosk grammar sirf active shabd banata hai — `[unk]` hamesha uske end me
(filler ko grammar me rakhna zaroori hai, warna Vosk ko `[unk]` nahi bolne deta).
"""

import json
import os

# ---- naam ----
# Jahan bhi app ka naam chahiye, yahan se lo. `.env` se badalna ho to
# PRABH_ASSISTANT_NAME; par persona/wake shabd tab bhi yahi ke shabd hain.
ASSISTANT_NAME = os.getenv("PRABH_ASSISTANT_NAME", "Jarvis").strip() or "Jarvis"
# Bade akshar wala brand: "Jarvis" -> "J.A.R.V.I.S"
DISPLAY_NAME = os.getenv("PRABH_DISPLAY_NAME", "J.A.R.V.I.S").strip() or "J.A.R.V.I.S"

# ---- wake shabd (Step 1: "Jarvis") ----
# Grammar me sirf ye teen shabd — isse galat trigger kam aur CPU halka
# (68 MB model me se sirf 4 shabd).
WAKE_PHRASES = ("hello jarvis", "hey jarvis", "jarvis")
# Purane "sunday" shabd alag list me, **default band**. Ek din wapas chahiye
# hon to `.env` me PRABH_WAKE_LEGACY=1 — dono saath chalte hain.
LEGACY_WAKE_PHRASES = (
    "hello sunday", "hey sunday", "hi sunday", "okay sunday", "sunday",
)

# Vosk grammar me filler shabd. Iske bina Vosk "unk" ko bhi bolne ki koshish
# karta hai. Ye list me rehna zaroori hai, sirf match karne ke liye nahi.
FILLER_WORD = "[unk]"


def legacy_enabled() -> bool:
    """Legacy wake shabd chalu hain? Env **har call** par padha jaata hai (test
    me `os.environ` badal kar turant dekh sakte hain)."""
    value = os.getenv("PRABH_WAKE_LEGACY", "0").strip().lower()
    return value not in ("0", "false", "no", "")


def active_wake_phrases() -> tuple:
    """Abhi kaun se shabd sun rahe hain (legacy chalu ho to dono)."""
    if legacy_enabled():
        return WAKE_PHRASES + LEGACY_WAKE_PHRASES
    return WAKE_PHRASES


def wake_words() -> tuple:
    """Har phrase ka **aakhri** shabd — `wake/phrase.py` yahi match karta hai.

    `"hey jarvis"` se `jarvis`. Duplicate hataye jaate hain, order wahi rehta hai.
    """
    words = []
    for phrase in active_wake_phrases():
        word = phrase.split()[-1]
        if word not in words:
            words.append(word)
    return tuple(words)


def wake_grammar() -> str:
    """Vosk grammar JSON. Phrase + `[unk]`, isse zyada kuch nahi."""
    return json.dumps(list(active_wake_phrases()) + [FILLER_WORD])
