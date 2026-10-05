"""`Session` ka **zindagi** hissa: mic/model chhodna, state, crash-safe callbacks.

`wake/session.py` 200 line cross kar raha tha, is liye 200-line ka seam yahi
rakha gaya hai (AGENTS ka niyam): **band karne ka faisla + state yahan, thread
ka loop + trigger wahan.** Split ka fayda: `Lifecycle` me mic/Vosk ka koi loop
nahi hai, is liye ye test me seedha chal sakta hai.

Class se is liye (function nahi, delegation nahi): `Session(Lifecycle)` me
`_end`/`_fail`/`_close`/`_say` bilkul waise hi rehte hain - koi caller badalta
hi nahi, sirf file badli hai.
"""

from log_setup import get_logger
from wake import model as model_mod

log = get_logger("wake_lifecycle")

STATES = ("off", "listening", "heard", "error")


class Lifecycle:
    """Mic + model + state. Thread **nahi** - wo `Session` ke paas hai.

    Class-level defaults is liye hain taaki ye class akeli bhi bana li jaaye
    (`_close()`/`_say()` kabhi bhi crash nahi karte).
    """

    _stop = None
    _thread = None
    _mic = None
    _listener = None
    _gate = None
    _state = "off"
    _failures = 0
    _on_state = None

    def _end(self) -> None:
        """Loop khatam - `off` ya `error`. Sirf `mic.error` kaafi nahi (unplug par
        wo khaali hota hai), is liye faisla `_stop` se."""
        mic = self._mic
        reason = mic.error if mic is not None else ""
        dead = mic is not None and not mic.alive
        self._close()
        self._thread = None
        if self._stop is not None and self._stop.is_set():
            log.info("wake band")
            value = "off"
        elif reason or dead:
            log.error("wake mic chala gaya: %s", reason or "device band (wajah nahi mili)")
            value = "error"
        else:
            log.info("wake band")
            value = "off"
        self._say(self._on_state, value)

    def _fail(self, exc: Exception) -> None:
        """Start fail (model missing / mic busy). Wajah log me, crash nahi."""
        self._failures += 1
        log.error("wake start fail (#%d): %s: %s",
                  self._failures, type(exc).__name__, exc)
        self._close()
        self._say(self._on_state, "error")

    def _close(self) -> None:
        """Model chhodna + mic band. Crash nahi karta, baar baar safe hai.

        `_lock` yahan jaan-boojh kar nahi liya - `start()` usko pakde hue
        failure par ye call karta hai, aur dobara pakadna deadlock de deta hai."""
        mic, self._mic = self._mic, None
        if mic is not None:
            mic.stop()
        self._listener = None
        self._gate = None
        model_mod.clear()

    def say(self, value: str) -> None:
        """`on_state` ko bhejo — sirf `_on_state` par (Trigger ke liye).

        `Trigger` ko seedha `self._say` nahi de sakte (2 args leta hai), is liye
        ye ek-arg wrapper hai. `_state` yahin update hota hai, is liye HUD ka
        `heard` pill bhi sahi chalta hai."""
        self._say(self._on_state, value)

    def _say(self, callback, value: str) -> None:
        """`on_state` ko haalat bhejo - uska crash hamara crash nahi hai."""
        self._state = value if value in STATES else "off"
        if callback is None:
            return
        try:
            callback(self._state)
        except Exception as exc:
            log.warning("on_state crash: %s: %s", type(exc).__name__, exc)