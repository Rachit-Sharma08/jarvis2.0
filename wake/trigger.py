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
        self._tail_until = 0.0    # tail guard: apni hi TTS ka pichhla hissa

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
        """Naye `start()` par cooldown **aur** tail guard saaf.

        Pichle session ka wait naya session rokega to trigger hi na ho (restart
        ke baad pehla "Jarvis" na chubke). Tail bhi saaf karna zaroori hai —
        warna app restart ke turant baad pehle 0.4 s ka "Jarvis" hi chhoot
        jayega."""
        self._cool_until = 0.0
        self._tail_until = 0.0

    def cooling(self) -> bool:
        """Abhi cooldown chal raha hai? (ek trigger ke baad ~1.5 s)"""
        return time.monotonic() < self._cool_until

    def mark_tail(self, seconds=None) -> None:
        """Hold chhoda — `seconds` tak **koi** chunk trigger na kar sake.

        **Apni hi awaaz se WAKE HIT** ka pakkaura (KAAM 2). `drain()` sirf
        `MAX_QUEUE_BLOCKS` (400 chunk ≈ 12 s) tak phenkta hai, par jawab 18 s
        me banta hai — to mic queue me hamari TTS bachi rehti hai. Purana
        `take_fresh()` sirf **ek** chunk bachata tha, uske baad Vosk ko wahi
        shor chala jaata tha. Ab poora tail window ignore hota hai.

        `seconds` na diya to `config.PLAYBACK_TAIL_GUARD_SECONDS` (0.4 s)."""
        span = config.PLAYBACK_TAIL_GUARD_SECONDS if seconds is None else float(seconds)
        self._tail_until = time.monotonic() + max(0.0, span)
        log.info("tail guard: %.2fs tak wake nahi", span)

    def tail_active(self) -> bool:
        """Abhi tail guard chal raha hai?"""
        return time.monotonic() < self._tail_until

    def suppressing(self) -> bool:
        """Chunk phenko, suno nahi — cooldown **ya** tail guard.

        `Session._loop` sirf yahi check karta hai. Do alag baatein hain: cooldown
        ek trigger ke baad hai, tail guard apni TTS ke baad."""
        return self.cooling() or self.tail_active()

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
        """Wake shabd hai? -> cooldown + `fire()`. -> trigger hua ya nahi.

        **`suppressing()` yahin bhi check hota hai**, sirf `_loop` me nahi —
        kyunki `gate.on_flush()` bhi `maybe()` ko **gate thread** se bulata
        hai, aur wahan `_loop` ka check nahi lagta. Gate ne text ko tail window
        me pakda ho to us flush par bhi trigger nahi hona chahiye (warna apni
        hi TTS se WAKE HIT). `_loop` ka check tez raasta hai (Vosk tak audio
        jaata hi nahi); ye aakhri zid hai."""
        if self.suppressing():
            log.info("suppressed (cooldown/tail): %r", text[:60])
            return False
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