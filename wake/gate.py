"""Vosk ko chunk dene ka faisla — battery ka asli hissa.

Purana loop **har** 30 ms chunk Vosk ko deta tha, chahe koi na bol. Napi
napa 3.9% CPU chalu rehta tha (RAM 154 MB) — yahi laptop ki battery kha raha
tha. VAD pehle se bata raha tha *bol rahe ho ya nahi*, bas us faisla ki
upaj hi nahi thi.

Gate ye karta hai:

1. chunk ka RMS VAD ko deta hai (`wake/audio.py`, wahi VAD — naya nahi),
2. `VAD_SILENCE_BLOCKS` khamoshi ho gaye to listener ka pichhla bhool jao
   (`listener.reset()` — purana behaviour, bas yahan se),
3. **sirf tab** `True` — yaani Vosk ko chunk chahiye. Khamoshi me `False`.

Mic ka stream kabhi band nahi hota (AGENTS ka duty-cycle niyam) — sirf
inference ruk jaati hai. Is liye "Hlo Jarvis" har waqt kaam karta hai.

`WAKE_VOSK_GATE = 0` (`.env` ke `PRABH_VOSK_GATE=0`) se gate band ho jaata hai
— phir purana behaviour (har chunk Vosk ko), taaki debug me saaf dikh sake.

Pure hai: mic, thread, Vosk — teeno chahiye hi nahi. Test me seedha ye chalta
hai (`tests/test_wake_gate.py`), is liye battery ka fix bina mic ke pakda ja
sakta hai.
"""

import config
from wake import audio as audio_mod


class Gate:
    """VAD + khamoshi ka hisaab + 'Vosk ko ye chunk chahiye?' ka faisla.

    `skipped` aur `fed` sirf hisaab hain (log + `--wake-info` + test).
    """

    def __init__(self, vad=None, gate_on: bool = None):
        self.vad = audio_mod.Vad() if vad is None else vad
        self.gate_on = config.WAKE_VOSK_GATE if gate_on is None else bool(gate_on)
        self._silent = 0
        self.fed = 0
        self.skipped = 0
        self.resets = 0

    def push(self, listener, raw: bytes) -> bool:
        """Chunk do + uska RMS. -> Vosk ko ye chunk chahiye ya nahi?

        `listener` yahin pass hota hai taaki khamoshi ke pichhle bhoolne ka
        `reset()` bhi isi ek jagah ho — loop me naya logic nahi.
        """
        loud = self.vad.push(audio_mod.chunk_to_rms(raw))
        self._silent = 0 if loud else self._silent + 1
        if self._silent >= config.VAD_SILENCE_BLOCKS:
            self._silent = 0
            self.resets += 1
            listener.reset()
        if self.gate_on and not loud:
            self.skipped += 1
            return False
        self.fed += 1
        return True

    def reset(self) -> None:
        """Wake trigger ke baad — VAD ka pichhla bhool jao (purana behaviour)."""
        self.vad.reset()
        self._silent = 0
