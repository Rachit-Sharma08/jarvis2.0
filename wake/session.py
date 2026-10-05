"""Wake worker ka asal kaam - mic + Vosk + loop, ek thread me.

`wake/worker.py` sirf module-level raasta deta hai (poori app me ek hi worker).
Is file me us ek worker ka **session** hai: mic, listener aur state.
Test me asli mic/model kabhi nahi chalta - `detect.build` aur
`audio_mod.MicSource` patch hote hain.

Loop: chunk uthakar VAD se dekho bol rahe ho ya nahi -> **sirf tab** Vosk ko
chunk (`WAKE_VOSK_GATE`) -> text trigger ko bhejo.

Trigger ka faisla (`wake/trigger.py`) teeno raaste ek jagah karta hai - final,
partial aur gate ka flush. Zindagi ka hissa (mic band karna, state, callbacks)
`wake/lifecycle.py` me hai. 200-line ka seam yahi hai (AGENTS).
"""

import queue
import threading
import time

import config
from log_setup import get_logger
from wake import audio as audio_mod
from wake import detect
from wake import gate as gate_mod
from wake import lifecycle as life_mod
from wake import trigger as trigger_mod

log = get_logger("wake_session")

STATES = life_mod.STATES


class Session(life_mod.Lifecycle):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._paused = threading.Event()
        self._thread = None
        self._mic = None
        self._listener = None
        self._gate = None
        self._state = "off"
        self._failures = 0
        self._trig = trigger_mod.Trigger()   # ek hi instance - `wakes` reset nahi hota

    # ---- padhna ----
    def state(self) -> str:
        """Abhi ka haalat - wahi shabd jo `desktop/state.py` likhta hai."""
        return self._state

    def listening(self) -> bool:
        """Mic khula hai aur sun raha hai? Tray ka MUTE isko rokta hai."""
        return self._state in ("listening", "heard")

    def wakes(self) -> int:
        """Ab tak kitne trigger? Poore app ka count - restart par reset nahi."""
        return self._trig.wakes

    def describe(self) -> str:
        return "%s | state=%s wakes=%d" % (config.describe(), self._state,
                                           self.wakes())

    def set_paused(self, on: bool) -> None:
        """Tray ka MUTE yahan aata hai. Pause me mic khula rehta hai, sunta nahi."""
        if on:
            self._paused.set()
            log.info("wake pause (mute)")
        else:
            self._paused.clear()
            # Pichla partial text command ke pichle hisse ka hai - use **pheko**,
            # warna agli command me leak hoga. Vosk ka ek hi owner ye loop hai,
            # is liye flag set karke loop se karwaate hain (tray thread se nahi).
            self._trig.mark_unpaused()
            log.info("wake chalu (unmute)")

    def paused(self) -> bool:
        """Abhi sunna band hai? (tray ka MUTE ya command ka hold - dono)"""
        return self._paused.is_set()

    # ---- zindagi ----
    def start(self, on_wake=None, on_state=None) -> bool:
        """Model + mic kholo aur sunne wala thread chalao. -> chala ya nahi."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return True
            self._on_state = on_state      # `Lifecycle._end/_fail` yahi padhte hain
            ok, reason = config.wake_available()
            if not ok:
                log.info("wake chalu nahi: %s", reason)
                self._say(on_state, "off")
                return False
            self._trig.set_callbacks(on_wake=on_wake, on_state=self.say)
            self._trig.reset_cooldown()    # pichle session ka wait naya rokega
            try:
                self._listener = detect.build()
                self._mic = self._open_mic()
            except Exception as exc:      # model missing, mic busy, ya surprise
                self._fail(exc)
                return False
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="wake", daemon=True)
            self._thread.start()
        self._say(self._on_state, "listening")
        log.info("wake ready: %s | vosk gate: %s (khamoshi me Vosk nahi)",
                 config.describe(), "ON" if config.WAKE_VOSK_GATE else "OFF")
        return True

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=3.0)
            if thread.is_alive():
                # Loop abhi bhi `self._listener` / `self._mic` use kar raha hai -
                # `_close()` karna crash karega, aur `_thread = None` karne se
                # `start()` **doosra** loop chala dega (ek hi Session, do loop).
                log.warning("wake thread 3s me band nahi hua - chhod raha hai")
                return
        self._close()
        self._thread = None

    # ---- mic (retry) ----
    def _open_mic(self):
        """Mic kholo - koshish karke. `MicUnavailable` (device busy/permission)
        par `MIC_OPEN_ATTEMPTS` tak retry.

        5-Oct: ek koshish me app hamesha `wake: nahi chala` ho jati thi, jabki
        asli wajah sirf ye thi ki mic kisi aur app (Chrome/Teams) ne pakda hua
        tha. Sirf `MicUnavailable` retry hota hai - constructor ya model ka
        crash turant upar jaata hai (warna asli bug chup ho jayega)."""
        last = None
        for attempt in range(1, max(1, config.MIC_OPEN_ATTEMPTS) + 1):
            try:
                mic = audio_mod.MicSource()
                mic.start()
                if attempt > 1:
                    log.info("mic %d. koshish me khul gaya", attempt)
                return mic
            except audio_mod.MicUnavailable as exc:
                last = exc
                log.warning("mic kholne me galti (#%d/%d): %s", attempt,
                            config.MIC_OPEN_ATTEMPTS, exc)
                if attempt < config.MIC_OPEN_ATTEMPTS:
                    time.sleep(config.MIC_OPEN_RETRY_SECONDS)
        raise last

    # ---- andar (thread) ----
    def _loop(self) -> None:
        gate = self._gate = gate_mod.Gate(on_text=self._trig.on_flush)
        self._trig.bind(self._listener, self._mic, self._stop, gate)
        while not self._stop.is_set():
            try:
                raw = self._mic.chunks.get(timeout=0.5)
            except queue.Empty:
                if not self._mic.alive:            # mic mara, queue khaali
                    break
                continue
            if not self._mic.alive:
                break
            if self._paused.is_set() or self._trig.cooling():
                continue                             # chunk phenko, suno nahi
            if self._trig.take_fresh():
                self._trig.drop_pending(self._listener)
            if not gate.push(self._listener, raw):  # khamoshi: Vosk mat chalao
                continue
            text = self._listener.feed(raw)
            how = "final"
            if not text:
                text = self._listener.partial()     # abhi bol raha hai
                how = "partial"
            if not text:
                continue
            log.info("sun liya (%s): %r", how, text[:60])
            self._trig.maybe(text)
        self._end()
