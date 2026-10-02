"""Wake worker ka asal kaam — mic + Vosk + trigger, ek thread me.

`wake/worker.py` sirf module-level raasta deta hai (poori app me ek hi worker).
Is file me us ek worker ka **session** hai: mic, listener, callbacks aur state.

Class is liye ki (a) global variable me kuch chhupa nahi hai, (b) test me
session ko dekh sakte hain. Test asli mic/model kabhi nahi chalate —
`detect.build` aur `audio_mod.MicSource` hi patch karte hain.

Loop: chunk uthakar VAD se dekho bol rahe ho ya nahi -> text nikaalo ->
`phrase.hit()` -> `on_wake`. Lambi khamoshi par recognizer reset (pichhla bhool
jao), aur wake hit ke baad `WAKE_COOLDOWN_SECONDS` tak chunk phenk-te rehne
wale (dobaara trigger na ho).
"""

import queue
import threading
import time

import config
from log_setup import get_logger
from wake import audio as audio_mod
from wake import detect
from wake import model as model_mod
from wake import phrase as phrase_mod

log = get_logger("wake_session")

STATES = ("off", "listening", "heard", "error")


class Session:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread = None
        self._mic = None
        self._listener = None
        self._on_wake = None
        self._on_state = None
        self._state = "off"
        self._wakes = 0
        self._failures = 0

    # ---- padhna ----
    def state(self) -> str:
        """Abhi ka haalat — wahi shabd jo `desktop/state.py` likhta hai."""
        return self._state

    def listening(self) -> bool:
        """Mic khula hai aur sun raha hai? Tray ka MUTE isko rokta hai."""
        return self._state in ("listening", "heard")

    def wakes(self) -> int:
        """Ab tak kitne trigger — test + `--wake-info` ke liye."""
        return self._wakes

    def describe(self) -> str:
        return "%s | state=%s wakes=%d" % (config.describe(), self._state, self._wakes)

    def set_paused(self, on: bool) -> None:
        """Tray ka MUTE yahan aata hai. Pause me mic khula rehta hai, sunta nahi."""
        if on:
            self._paused.set()
            log.info("wake pause (mute)")
        else:
            self._paused.clear()
            log.info("wake chalu (unmute)")

    # ---- chalao / band ----
    def start(self, on_wake=None, on_state=None) -> bool:
        """Model + mic kholo aur sunne wala thread chalao. -> chala ya nahi."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return True
            ok, reason = config.wake_available()
            if not ok:
                log.info("wake chalu nahi: %s", reason)
                self._say(on_state, "off")
                return False
            self._on_wake, self._on_state = on_wake, on_state
            try:
                self._listener = detect.build()
                self._mic = audio_mod.MicSource()
                self._mic.start()
            except Exception as exc:      # model missing, mic band, ya koi surprise
                self._fail(exc)
                return False
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="wake", daemon=True)
            self._thread.start()
        self._say(self._on_state, "listening")
        log.info("wake ready: %s", config.describe())
        return True

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=3.0)
        self._close()
        self._thread = None

    # ---- andar (thread) ----
    def _loop(self) -> None:
        vad = audio_mod.Vad()
        silent = 0
        cool_until = 0.0
        while not self._stop.is_set():
            try:
                raw = self._mic.chunks.get(timeout=0.5)
            except queue.Empty:
                continue
            if not self._mic.alive:                  # mic beech me mar gaya
                break
            if self._paused.is_set() or time.monotonic() < cool_until:
                continue                             # chunk phenko, suno nahi
            loud = vad.push(audio_mod.chunk_to_rms(raw))
            silent = 0 if loud else silent + 1
            if silent >= config.VAD_SILENCE_BLOCKS:
                silent = 0
                self._listener.reset()               # khamoshi ka pichhla bhool jao
            text = self._listener.feed(raw)
            if not text:
                continue
            log.info("sun liya: %r", text[:60])
            if not phrase_mod.hit(text):
                continue
            cool_until = time.monotonic() + config.WAKE_COOLDOWN_SECONDS
            self._fire(text, vad)
            silent = 0
        self._end()

    def _fire(self, text: str, vad) -> None:
        self._wakes += 1
        heard = phrase_mod.phrase(text)
        log.info("WAKE HIT #%d: %r (poora: %r)", self._wakes, heard, text[:60])
        self._say(self._on_state, "heard")
        if self._on_wake is not None:
            try:
                self._on_wake(heard)
            except Exception as exc:
                log.error("on_wake crash: %s: %s", type(exc).__name__, exc)
        self._listener.reset()
        vad.reset()

    def _end(self) -> None:
        """Loop khatam (band ya mic mara). Jo bhi haal — saaf jodo."""
        reason = self._mic.error if self._mic is not None else ""
        self._close()
        self._thread = None
        if reason and not self._stop.is_set():
            log.error("wake mic chala gaya: %s", reason)
            self._say(self._on_state, "error")
        else:
            log.info("wake band")
            self._say(self._on_state, "off")

    def _fail(self, exc: Exception) -> None:
        self._failures += 1
        log.error("wake start fail (#%d): %s: %s",
                  self._failures, type(exc).__name__, exc)
        self._close()
        self._say(self._on_state, "error")

    def _close(self) -> None:
        """Model chhodna + mic band. Crash nahi karta, baar baar safe hai.

        `_lock` yahan jaan-boojh kar nahi liya — `start()` usko pakde hue
        failure par ye call karta hai, aur dobara pakadna deadlock de deta."""
        mic, self._mic = self._mic, None
        if mic is not None:
            mic.stop()
        self._listener = None
        model_mod.clear()

    def _say(self, callback, value: str) -> None:
        """`on_state` ko haalat bhejo — uska crash hamara crash nahi hai."""
        self._state = value if value in STATES else "off"
        if callback is None:
            return
        try:
            callback(self._state)
        except Exception as exc:
            log.warning("on_state crash: %s: %s", type(exc).__name__, exc)
