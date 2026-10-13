"""`wake/command.py` ke **pure guard** — `_safe`, `_allowed`, `_is_sleep`.

Ye file 15-Oct raat me bani (`wake/command.py` 200 cross kar gaya tha).

Ye teenon helpers:
- **koi mic nahi** chhute,
- **koi brain nahi** chhuta,
- sirf `config` aur `log` chahiye.

Is liye inhe `command.py` se nikalna aasan tha — in par koi source-scan test
nahi hai (saare scan `run()` ke andar hain: `hold_for_command`, `mark_hot`,
stage names, `settled_by`, `voice_answer`).

**`_is_sleep` duplicate hai jaan-boojh kar.** `desktop/sleep.py` ka `matches()`
ka bhi wahi guard hai, par `wake/` ko `desktop/` ka import nahi karwana (project
ka niyam). `tests/test_desktop_sleep.py` har `config.SLEEP_WORDS` shabd **dono**
guard me check karta hai, taaki ek jagah shabd add karne par doosri chup na ho.

`command.py` me `from wake.guard import _safe, _allowed, _is_sleep` likha hai —
is liye `command._is_sleep(...)` bhi chalta hai (do test waise hi call karte
hain), matlab purane callers kuch nahi toote.
"""

import config
from log_setup import get_logger

log = get_logger("wake.guard")


def _safe(callback, *args) -> None:
    """Callback ka crash hamara crash nahi hai (HUD open, busy pill...)."""
    if callback is None:
        return
    try:
        callback(*args)
    except Exception as exc:
        log.warning("callback crash: %s: %s", type(exc).__name__, exc)


def _allowed(allowed) -> tuple:
    """`allowed()` se faisla. Default (koi callback nahi) = sab theek."""
    if allowed is None:
        return True, ""
    try:
        ok, reason = allowed()
    except Exception as exc:
        log.error("allowed() crash: %s: %s", type(exc).__name__, exc)
        return False, "guard crash"
    return bool(ok), str(reason or "")


def _is_sleep(text: str) -> bool:
    """'So jao' hai kya? Yahi guard `desktop/sleep.py` me hai — `wake/` ko
    `desktop/` ka import nahi karwana (`tests/test_desktop_sleep.py` dono check
    karta hai, taaki dono alag na ho jaayein).

    Chhota-text guard zaroori hai (4 shabd se kam): warna "band ho jao kya
    matlab hai" jaisa vaakya sun kar app galti se so jaa dega."""
    low = (text or "").strip().lower()
    if not low or len(low.split()) > 4:
        return False
    return any(word in low for word in config.SLEEP_WORDS)