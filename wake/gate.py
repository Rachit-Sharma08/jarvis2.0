"""Vosk ko chunk dene ka faisla — battery ka asli hissa.

Purana loop **har** 30 ms chunk Vosk ko deta tha, chahe koi na bol. Napi
napa 3.9% CPU chalu rehta tha (RAM 154 MB) — yahi laptop ki battery kha raha
tha. VAD pehle se bata raha tha *bol rahe ho ya nahi*, bas us faisla ki
upaj hi nahi thi.

Gate ye karta hai:

1. chunk ka RMS VAD ko deta hai (`wake/audio.py`, wahi VAD - naya nahi),
2. `VAD_SILENCE_BLOCKS` khamoshi ho gaye to **pending text flush** karta hai
   (`listener.flush()`) aur `on_text` se trigger ka faisla karata hai - **pheko
   nahi** (5-Oct ka asli bug: sirf `reset()` tha, to Vosk ka 'hello'/'yo' gayab
   ho jata tha aur wake word trigger hi nahi hota tha),
3. **sirf tab** `True` - yaani Vosk ko chunk chahiye. Khamoshi me `False`.

Mic ka stream kabhi band nahi hota (AGENTS ka duty-cycle niyam) - sirf
inference ruk jaati hai. Is liye "Hlo Jarvis" har waqt kaam karta hai.

`WAKE_VOSK_GATE = 0` (`.env` ke `JARVIS_VOSK_GATE=0`) se gate band ho jaata hai
— phir purana behaviour (har chunk Vosk ko), taaki debug me saaf dikh sake.

Pure hai: mic, thread, Vosk — teeno chahiye hi nahi. Test me seedha ye chalta
hai (`tests/test_wake_gate.py`), is liye battery ka fix bina mic ke pakda ja
sakta hai.
"""

import time

import config
from log_setup import get_logger
from wake import audio as audio_mod

log = get_logger("wake_gate")


class Gate:
    """VAD + khamoshi ka hisaab + 'Vosk ko ye chunk chahiye?' ka faisla.

    `skipped` aur `fed` sirf hisaab hain (log + `--wake-info` + test).
    """

    def __init__(self, vad=None, gate_on: bool = None, on_text=None):
        self.vad = audio_mod.Vad() if vad is None else vad
        self.gate_on = config.WAKE_VOSK_GATE if gate_on is None else bool(gate_on)
        self.on_text = on_text          # khamoshi par text mila -> ye call (policy
        self._silent = 0                # `wake/session.py` ka trigger faisla)
        self.fed = 0
        self.skipped = 0
        self.resets = 0
        self.flushes = 0
        self.pushes = 0          # kitne chunk aaye (fed + skipped se zyada nahi)
        self.last_rms = 0.0
        self.last_loud = False
        self._last_log = 0.0

    def push(self, listener, raw: bytes) -> bool:
        """Chunk do + uska RMS. -> Vosk ko ye chunk chahiye ya nahi?

        `listener` yahin pass hota hai taaki silence par flush/reset bhi isi ek
        jagah ho - loop me naya logic nahi.
        """
        self.pushes += 1
        rms = audio_mod.chunk_to_rms(raw)
        self.last_rms = rms
        loud = self.vad.push(rms)
        self.last_loud = loud
        self._silent = 0 if loud else self._silent + 1
        if self._silent >= config.VAD_SILENCE_BLOCKS:
            self._silent = 0
            self.resets += 1
            if self._flush(listener):
                return False         # text mila -> on_text ne faisla kar liya
            listener.reset()
        self._debug(listener)
        if self.gate_on and not loud:
            self.skipped += 1
            return False
        self.fed += 1
        return True

    def _flush(self, listener) -> bool:
        """Khamoshi par pending text nikaal do. -> kuch mila ya nahi.

        **Yehi se trigger hota hai** (`on_text`): 5-Oct tak yahan sirf
        `listener.reset()` tha, is liye Vosk ka text (aam taur par 'hello' ya
        'yo' - do tukde me aata hai) chup-chaap phenk diya jata tha aur "Hlo
        Jarvis" ke baad dobara kuch nahi sunai deta tha.

        Text nahi mila to `reset()` (purana behaviour) chalega - caller usi
        hisse me decide karta hai."""
        flush = getattr(listener, "flush", None)
        if flush is None:              # purana/fake listener - chup-chaap chhod do
            return False
        try:
            text = flush()
        except Exception as exc:
            log.warning("flush fail: %s: %s", type(exc).__name__, exc)
            return False
        if not text:
            return False
        self.flushes += 1
        log.info("khamoshi par text mila: %r", text[:60])
        if self.on_text is not None:
            try:
                self.on_text(text)
            except Exception as exc:
                log.warning("on_text crash: %s: %s", type(exc).__name__, exc)
        return True

    def _debug(self, listener) -> None:
        """`JARVIS_WAKE_DEBUG=1` par periodic hisaab — bug pakadne ke liye.

        Do alag galtiyan dono se ek jaisi dikhti hain (kuch nahi sunai deta):
        (a) chunk **aate hi nahi** — `pushes` nahi badhta, (b) chunk aate hain
        par VAD unhe khamoshi bolta hai — `pushes` badhta hai, `skipped` bhi.
        Isiliye dono counters ek saath chahiye."""
        if not config.WAKE_DEBUG:
            return
        now = time.monotonic()
        if now - self._last_log < config.WAKE_DEBUG_SECONDS:
            return
        self._last_log = now
        log.info("wake debug: chunk=%d loud=%s rms=%.4f fed=%d skip=%d "
                 "finals=%d", self.pushes, self.last_loud, self.last_rms,
                 self.fed, self.skipped, getattr(listener, "finals", 0))

    def reset(self) -> None:
        """Wake trigger ke baad — VAD ka pichhla bhool jao (purana behaviour)."""
        self.vad.reset()
        self._silent = 0
