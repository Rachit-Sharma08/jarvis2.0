"""Wake word — Phase 5 Step 1 ka module-level raasta (poori app me **ek** worker).

Sirf yahi file `desktop/app.py` se jodi hai (aur `desktop/actions.py` tray ke
MUTE se). Andar ka saala kaam `wake/session.py` ke `Session` me hai — yahan
bas ek singleton rakh kar aage bhej diya gaya hai.

Step 1 me ye **sirf sunta** hai: mic khula rehta hai, Vosk text laata hai,
"sunday" milte hi `on_wake(phrase)` + `on_state("heard")`. Koi recording, koi
STT call, koi brain call nahi — wo Step 2 hai (tab HUD ke saath command bhi
sunega aur "Ji, boliye" bolega).

`READY` abhi `True` hai, par Step 3a ke stub wala hissa ab bhi nahi — mic na
khule to `start()` `False` deta hai aur wajah `desktop/app.py` startup ki line
me bolti hai.
"""

from log_setup import get_logger
from wake import session as session_mod

log = get_logger("wake")

READY = True

_SESSION = session_mod.Session()


def start(on_wake=None, on_state=None) -> bool:
    """Worker chalao. -> chal gaya ya nahi (wajah log me)."""
    return _SESSION.start(on_wake, on_state)


def stop() -> None:
    """Band karo. Mic band, model chhoda, thread jodo."""
    _SESSION.stop()


def state() -> str:
    """off / listening / heard / error — `desktop/state.py` isi ko dikhata hai."""
    return _SESSION.state()


def listening() -> bool:
    """Sun raha hai? Tray ka MUTE isko rokta hai (`set_paused`)."""
    return _SESSION.listening()


def set_paused(on: bool) -> None:
    """Mic MUTE ON/OFF. Pause me mic khula rehta hai, sirf sunta nahi."""
    _SESSION.set_paused(on)


def wakes() -> int:
    """Ab tak kitne trigger — test + `--wake-info` ke liye."""
    return _SESSION.wakes()


def describe() -> str:
    """`config.describe()` + worker ka haalat — `--wake-info` ke liye."""
    return _SESSION.describe()
