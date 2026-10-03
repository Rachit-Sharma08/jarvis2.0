"""Wake word — Phase 5 Step 1 ka module-level raasta (poori app me **ek** worker).

Sirf yahi file `desktop/app.py` se jodi hai (aur `desktop/actions.py` tray ke
MUTE se). Andar ka saala kaam `wake/session.py` ke `Session` me hai — yahan
bas ek singleton rakh kar aage bhej diya gaya hai.

Step 2 me ye worker sirf sunta hai: mic khula rehta hai, Vosk text laata hai,
wake shabd milte hi `on_wake(phrase, mic, stop)` + `on_state("heard")`.

Pause ke do **alag** kaam hain, is liye do alag khaali rakhi hain:

- `set_paused()` — tray ka MUTE. **User ka faisla**, hamesha rehta hai.
- `hold_for_command()` — command ke chalte waqt sunna rokna (apni hi TTS apne
  mic me na aaye). **Temporary** — `release_from_command()` se khud khulta hai.
  Beech me user ne MUTE kiya to `_HELD` clear ho jaata hai aur release kuch
  nahi chhedta — MUTE haar nahi maarta.

`stop()` `listen.stop()` bhi call karta hai: app band ho raha ho to command ka
capture aur uske aage ka TTS turant ruk jaane chahiye (`worker.stop()` ka join
sirf 3 second ka hai).
"""

from log_setup import get_logger
from wake import listen
from wake import session as session_mod

log = get_logger("wake")

READY = True

_SESSION = session_mod.Session()
_HELD = False            # command ka temporary hold (MUTE nahi)


def start(on_wake=None, on_state=None) -> bool:
    """Worker chalao. -> chal gaya ya nahi (wajah log me)."""
    return _SESSION.start(on_wake, on_state)


def stop() -> None:
    """Band karo. Pehle command ka capture/TTS, phir mic + model."""
    listen.stop()
    _SESSION.stop()


def state() -> str:
    """off / listening / heard / error — `desktop/state.py` isi ko dikhata hai."""
    return _SESSION.state()


def listening() -> bool:
    """Sun raha hai? Tray ka MUTE isko rokta hai (`set_paused`)."""
    return _SESSION.listening()


def set_paused(on: bool) -> None:
    """Mic MUTE ON/OFF. Pause me mic khula rehta hai, sirf sunta nahi."""
    global _HELD
    if on:
        _HELD = False          # MUTE ne hold ko absorb kar liya - release no-op
    _SESSION.set_paused(on)


def paused() -> bool:
    """Abhi sunna band hai? (MUTE ya command ka hold — dono yahan se dikhte hain)"""
    return _SESSION.paused()


def hold_for_command() -> bool:
    """Command shuru: apni TTS sun na aaye. -> kya chhodna bhi hamara kaam hai?

    `False` ka matlab kisi aur ne pehle se rok diya hai (ya MUTE) — us haal me
    `release_from_command()` kuch nahi karega, warna MUTE haar jayega."""
    global _HELD
    if _HELD:
        return False
    _HELD = True
    _SESSION.set_paused(True)
    return True


def release_from_command() -> None:
    """Command khatam — phir se sunne do (MUTE nahi kiya to)."""
    global _HELD
    if not _HELD:
        return
    _HELD = False
    _SESSION.set_paused(False)


def wakes() -> int:
    """Ab tak kitne trigger — test + `--wake-info` ke liye."""
    return _SESSION.wakes()


def describe() -> str:
    """`config.describe()` + worker ka haalat — `--wake-info` ke liye."""
    return _SESSION.describe()
