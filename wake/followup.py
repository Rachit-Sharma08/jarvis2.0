"""Follow-up window ka **faisla** — "Jarvis" bola hi nahi, phir bhi trigger? (KAAM 5)

`wake/trigger.py` 232 lines ho gaya tha (AGENTS ka 200-line niyam), aur hot
window ka hissa usme se alag concern hai — is liye yahi file bani. **Trigger
khud** wahi rehta hai; sirf dono pure helper yahan aaye:

- `is_utterance(text)` — ye asli **baat** hai, ya filler/khamoshi?
- `decide(trig, text)` — follow-up maara ya nahi?

Do guard jo **hamesha** pehle chalte hain (is liye apni awaaz kabhi follow-up
nahi ban sakti) `Trigger.suppressing()` aur `is_utterance()` hain — dono
`decide()` ke andar hain, matlab koi bhi raasta inke bina nikal hi nahi sakta.

**DEFAULT OFF**: `config.HOT_WINDOW_ENABLED=0` par `Trigger.hot_active()`
hamesha `False` rehta hai aur `decide()` turant `None` deta hai — yaani app
ka raasta bilkul purane jaisa, sirf ek dict lookup zyada.
"""

import config
from log_setup import get_logger
from voice import stt_guard

log = get_logger("wake_followup")


def is_utterance(text: str) -> bool:
    """Ye text **baat** hai (khamoshi/short filler nahi)?

    Follow-up window me sirf sunte rehna hai — is liye "jarvis" shabd ki
    zaroorat nahi, par "uh"/"hmm"/"Thank you." jaisa kuch bhi follow-up nahi
    hai. Guard wahi jo STT ke liye hai (`voice/stt_guard.py`) — ek hi jagah,
    do alag list nahi."""
    body = str(text or "").strip()
    if len(body) < 3 or len(body.split()) < 2:
        return False
    if stt_guard.is_silence_phrase(body):
        return False
    # Poore text ke shabd **saare** filler hue to bhi follow-up nahi — jaise
    # "hmm uh". `is_silence_phrase()` poora text ek shabd pakadta hai, is liye
    # yahan shabd-girdi ki. List wahi hai (duplicate nahi).
    words = {w.strip(".,!?।'\"") for w in body.split()}
    fillers = {p.strip(".") for p in stt_guard.SILENCE_PHRASES}
    if words and words <= fillers:
        return False
    return True


def decide(trig, text: str):
    """Follow-up window me ye text trigger karega? -> `'fire'` ya `None`.

    `Trigger.suppressing()` (cooldown + KAAM 2 ka tail guard) pehle hamesha
    check hota hai, is liye apni hi TTS is raaste se trigger nahi kar sakti.

    Trigger chala kar `True` return karta hai; warna `None` — taaki `None`
    par truthy na lage.
    """
    if not config.HOT_WINDOW_ENABLED or not trig.hot_active():
        return None
    if trig.suppressing():
        return None
    if not is_utterance(text):
        return None
    log.info("FOLLOW-UP HIT (bina 'Jarvis'): %r", str(text)[:60])
    trig.mark_hot()                     # agle follow-up ka window dobara
    return "fire"