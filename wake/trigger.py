"""Wake trigger ka **faisla** — teen raaste, ek jagah (5-Oct ka fix).

`wake/session.py` sirf sunta hai (mic + loop). "Ye text me wake shabd hai ya
nahi?" ka jawab yahan hai, is liye teen raaste ek hi jagah hain:

1. **final**   - `listener.feed()` se text aaya
2. **partial** - Vosk abhi bol raha hai, wake shabd usi text me hai
3. **flush**   - gate ne khamoshi par `FinalResult()` se pending text nikala

5-Oct ka asli bug: gate silence par `listener.reset()` karta tha, jisse Vosk ka
pending text (trigger ka hissa) **chhoot** jata tha - is liye "Hlo Jarvis" do
tukde me toot kar trigger hi nahi hota tha, aur dusra command kabhi nahi chalta.

Ye class **sirf** trigger ginti hai aur `on_wake` ko (phrase, mic, stop) deti hai.
`on_wake` wake thread par **synchronous** chalta hai - command poora chal jaane
tak sunna ruka rehta hai, is liye dobara trigger nahi hota.
"""

import time

import config
from log_setup import get_logger
from wake import phrase as phrase_mod

log = get_logger("wake_trigger")


class Trigger:
    """Cooldown + wake shabd ka pakora + `on_wake` ka call.

    **Ek hi instance** bana kar poori app me chalta hai (`Session.__init__`),
    is liye `wakes` count restart par **reset nahi** hota - `worker.wakes()`
    poore app ka count hai (test + `--wake-info` isi par bharosa karti hai).
    Har `start()` sirf callbacks aur mic/listener/gate dobara set karta hai.
    """

    def __init__(self, on_wake=None, on_state=None):
        self.on_wake = on_wake
        self.on_state = on_state
        self.listener = None      # `detect.Listener` (loop se)
        self.gate = None          # `gate.Gate` (loop se)
        self.mic = None           # `audio.MicSource` (trigger ke waqt)
        self.stop = None          # threading.Event (command ruk jaaye)
        self.wakes = 0
        self._cool_until = 0.0
        self._fresh = False       # unpause hua: pichla partial phek do

    def set_callbacks(self, on_wake=None, on_state=None) -> None:
        """Naye `start()` ke callbacks. Count (`wakes`) jaan-boojh kar **nahi** chhuta."""
        self.on_wake = on_wake
        self.on_state = on_state

    def bind(self, listener, mic, stop, gate=None) -> None:
        """Loop ne jo cheezein kholi hain, unka ref yahan (trigger ke liye)."""
        self.listener = listener
        self.mic = mic
        self.stop = stop
        if gate is not None:
            self.gate = gate

    def reset_cooldown(self) -> None:
        """Naye `start()` par cooldown saaf - pichle session ka wait naya
        session rokega to trigger hi na ho (restart ke baad pehla "Jarvis")."""
        self._cool_until = 0.0

    def cooling(self) -> bool:
        """Abhi cooldown chal raha hai? (ek trigger ke baad ~1.5 s)"""
        return time.monotonic() < self._cool_until

    def mark_unpaused(self) -> None:
        """MUTE hat gaya - pichle command ka partial agle me na leak ho."""
        self._fresh = True

    def take_fresh(self) -> bool:
        """Sirf **ek** chunk: unpause hone wala hai? (uske baad False)"""
        if not self._fresh:
            return False
        self._fresh = False
        return True

    def on_flush(self, text: str) -> bool:
        """Gate ka `on_text` — khamoshi par wapas aaya text. (gate thread)"""
        log.info("sun liya (khamoshi par): %r", text[:60])
        return self.maybe(text)

    def maybe(self, text: str) -> bool:
        """Wake shabd hai? -> cooldown + `fire()`. -> trigger hua ya nahi."""
        if not phrase_mod.hit(text):
            return False
        self._cool_until = time.monotonic() + config.WAKE_COOLDOWN_SECONDS
        self.fire(text)
        return True

    def fire(self, text: str) -> None:
        """WAKE HIT. `on_wake(phrase, mic, stop)` — mic/stop ka **sirf** raasta."""
        self.wakes += 1
        heard = phrase_mod.phrase(text)
        log.info("WAKE HIT #%d: %r (poora: %r)", self.wakes, heard, text[:60])
        if self.on_state is not None:
            self.on_state("heard")
        if self.on_wake is not None:
            try:
                self.on_wake(heard, self.mic, self.stop)
            except Exception as exc:
                log.error("on_wake crash: %s: %s", type(exc).__name__, exc)
        self.reset_after_fire()

    def reset_after_fire(self) -> None:
        """Trigger ke baad listener + gate saaf (na naya command, na naya wake)."""
        if self.listener is not None:
            self.listener.reset()
        if self.gate is not None:
            self.gate.reset()

    def drop_pending(self, listener=None) -> None:
        """Unpause ke baad bacha hua Vosk text phek do.

        Bina iske pichle command ka partial agle command me leak hota hai - aur
        queue me TTS ka shor bhi pada rehta hai (`wake/command.py` ke `finally`
        me drain hota hai, ye uske baad ka safety net hai)."""
        listener = self.listener if listener is None else listener
        if listener is None:
            return
        try:
            text = listener.flush()
        except Exception as exc:
            log.warning("flush fail: %s: %s", type(exc).__name__, exc)
            return
        if text:
            log.info("purana partial phek diya: %r", text[:40])
        listener.reset()