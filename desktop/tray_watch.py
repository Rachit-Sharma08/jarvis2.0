r"""Tray icon ka **haal nikalne wala** (roadmap T-01, S6 step 3 + step 5)

**Live probe se pata chala (4-Oct):** `Shell_NotifyIconGetRect` is Windows par
`E_INVALIDARG` deta hai — chahe icon sahi ho. Naya throwaway pystray icon banaya:
shell ne uski registry entry bana di (matlab icon **accept** hua), par GetRect
phir bhi fail. Is liye GetRect **sach ka source nahi** — pystray ka `NIM_ADD`
ka return value bhi pystray ignore karta hai. Dono ka matlab: koi bhi code pehle
se nahi bata sakta ki icon dikh raha hai ya nahi.

**Sahi source:** Windows ka `HKCU\Control Panel\NotifyIconSettings`. Shell sirf
usi exe ke liye entry banata hai jiska icon uske paas hai. Do baatein padhi ja
sakti hain:

- entry hi nahi → icon shell me nahi hai (asli gadbad)
- entry hai par `IsPromoted` missing → icon **`^` (hidden icons)** me chhupa hai
- entry hai aur `IsPromoted=1` → icon taskbar me **dikhta** hai

Entry humari is liye pehchani jaati hai kyunki `InitialTooltip` hamesha
`ASSISTANT_NAME` se shuru hota hai (`Jarvis - sun raha hai` wagairah).

**App registry me KABHI kuch nahi likhta** — sirf padhta hai. `IsPromoted=1`
likhna owner ke confirm + `reg export` backup ke baad hota hai (AGENTS 8.2).

Ye watchdog roz chalta rehta hai aur **sirf tab log karta hai jab haal badle** —
is liye ek hi line per start, spam nahi.
"""

import threading
import time
import winreg

import config
from log_setup import get_logger

log = get_logger("tray_watch")

REG_PATH = r"Control Panel\NotifyIconSettings"
VISIBLE, HIDDEN, MISSING = "visible", "hidden", "missing"

MESSAGE = {
    # NOTE (4-Oct): ye **guess** hai, proof nahi. `NotifyIconSettings` entry
    # banna matlab shell ne icon **register** kiya - yehi `NIM_ADD` ke baad
    # hota hai, chahe icon invisible bhi ho. `pystray` ka `visible=False` bug
    # pakda tha, tab bhi ye yahan "dikh raha hai" bol raha tha. Is liye dono
    # message me "lagta hai" jaisa shabd hai - sach owner ki aankh par hai.
    VISIBLE: "tray icon shell me registered hai aur promoted bhi - taskbar me "
             "dikhta hua hai (pakka nahi, owner dekh le)",
    HIDDEN: "tray icon shell me registered hai par ^ (hidden icons) me hai - "
            "taskbar ke ^ par click karke is icon par 'Always show icons' karo",
    MISSING: "tray icon shell me registered nahi hai (registry entry hi nahi "
             "mili) - Ctrl+Alt+S se HUD kholo, ya app restart karo",
}


def _read_entries():
    """`{hash: (tooltip, exe, promoted)}`. Sirf padhta hai, kabhi nahi likhta."""
    out = {}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
        for i in range(winreg.QueryInfoKey(key)[0]):
            sub = winreg.EnumKey(key, i)
            with winreg.OpenKey(key, sub) as one:
                out[sub] = (_value(one, "InitialTooltip"),
                            _value(one, "ExecutablePath"),
                            _value(one, "IsPromoted"))
    return out


def _value(key, name):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except FileNotFoundError:
        return None


def find_our_entry(entries, name):
    """`(hash, promoted)` — tooltip se naam pakadta hai. Pure."""
    for sub, (tip, _exe, promoted) in entries.items():
        if tip and str(tip).startswith(name):
            return sub, promoted
    return None, None


def status(entries, name):
    """`VISIBLE` / `HIDDEN` / `MISSING`. Pure — test isi par chalta hai."""
    sub, promoted = find_our_entry(entries, name)
    if sub is None:
        return MISSING
    return VISIBLE if promoted else HIDDEN


class Watchdog:
    """Daemon thread. `entries_fn`/`sleep_fn` injectable — test me asli
    registry ya wait kabhi nahi."""

    def __init__(self, sleep_fn=None, clock=None, entries_fn=None, name=None):
        self._sleep = self._wait if sleep_fn is None else sleep_fn
        self._clock = time.monotonic if clock is None else clock
        self._entries = _read_entries if entries_fn is None else entries_fn
        self._name = config.ASSISTANT_NAME if name is None else name
        self._stop = threading.Event()
        self._thread = None
        self.state = None          # test + log

    def _wait(self, seconds):
        return self._stop.wait(seconds)

    def start(self):
        if not config.TRAY_WATCH_ENABLED:
            log.info("tray watchdog band (JARVIS_TRAY_WATCH=0)")
            return False
        if self._thread is not None:
            return True
        self._thread = threading.Thread(target=self.run, name="tray_watch",
                                        daemon=True)
        self._thread.start()
        log.info("tray watchdog chalu (pehle %.0fs, phir %.0fs me ek dekh)",
                 config.TRAY_WATCH_FIRST_SECONDS, config.TRAY_WATCH_SLOW_SECONDS)
        return True

    def stop(self):
        self._stop.set()

    def run(self):
        start = self._clock()
        while not self._stop.is_set():
            self._check()
            if self._sleep(delay(self._clock() - start)):
                return

    def _check(self):
        try:
            now = status(self._entries(), self._name)
        except Exception as exc:
            log.warning("tray check nahi chal paya: %s: %s", type(exc).__name__, exc)
            return
        if now != self.state:
            self.state = now
            if now == VISIBLE:
                log.info("%s", MESSAGE[now])
            else:
                log.warning("%s", MESSAGE[now])


def delay(elapsed):
    """Pehle phase tez-dekh, phir dheere. Pure."""
    if elapsed < config.TRAY_WATCH_FIRST_SECONDS:
        return config.TRAY_WATCH_FAST_SECONDS
    return config.TRAY_WATCH_SLOW_SECONDS


_STARTED = []


def start():
    """App se ek hi raasta: `desktop/app.py` yahin se watchdog chalu karta hai."""
    if not _STARTED:
        _STARTED.append(Watchdog())
    return _STARTED[0].start()


def stop():
    for dog in _STARTED:
        dog.stop()
    del _STARTED[:]