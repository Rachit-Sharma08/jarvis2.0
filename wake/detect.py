"""Vosk recognizer ka wrapper — chunk daalo, saaf text nikaalo.

Vosk thoda low-level hai: `AcceptWaveform()` tabhi `True` deta hai jab **final**
result tayyar ho, aur jawab JSON aata hai. Ye file sirf wahi saaf karta hai:

  `feed(raw)`    -> final text, warna `''`
  `partial()`    -> abhi bol rahe ka text (trigger + HUD/log ke liye)
  `flush()`      -> pending text **force** nikaal do (khamoshi par)
  `reset()`      -> purana bhool jao (wake hit ya lambi khamoshi par)
  `build()`      -> model + listener (worker ke liye ek hi raasta)

Test me asli model ki jagah `_FakeRecognizer` daala jaata hai — is liye ye class
recognizer ke sirf teen method use karti hai (`AcceptWaveform`, `Result`,
`PartialResult`, `Reset`).
"""

import json

import config
from log_setup import get_logger
from wake import model as model_mod

log = get_logger("wake_detect")


def _text(raw: str) -> str:
    """Vosk ka JSON -> saaf text. Kuch bhi ajeeb aaye to `''` (crash nahi)."""
    try:
        data = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return ""
    if not isinstance(data, dict):
        return ""
    return str(data.get("text") or data.get("partial") or "").strip()


class Listener:
    def __init__(self, vosk_model=None, rate: int = None, grammar: str = None):
        from vosk import KaldiRecognizer       # import late: startup tez rahe

        self.rate = config.SAMPLE_RATE if rate is None else int(rate)
        self.grammar = config.WAKE_GRAMMAR if grammar is None else grammar
        self.recognizer = KaldiRecognizer(vosk_model, self.rate, self.grammar)
        self.finals = 0          # kitni baar poora text mila
        self.resets = 0

    def feed(self, raw: bytes) -> str:
        """Chunk daalo. -> final text ya `''` (abhi poora nahi hua)."""
        if not raw:
            return ""
        try:
            ready = self.recognizer.AcceptWaveform(raw)
        except Exception as exc:
            log.warning("recognizer fail: %s: %s", type(exc).__name__, exc)
            return ""
        if not ready:
            return ""
        self.finals += 1
        return _text(self.recognizer.Result())

    def partial(self) -> str:
        try:
            raw = self.recognizer.PartialResult()
        except Exception as exc:
            log.warning("partial fail: %s: %s", type(exc).__name__, exc)
            return ""
        return _text(raw)

    def flush(self) -> str:
        """Pending text **force** nikaal do (`FinalResult`). -> text ya `''`.

        Zaruri kyun: gate khamoshi me Vosk ko chunk **nahi** deta (battery), to
        Vosk ko vo silence nahi milti jisse apna endpoint nikalta hai. Purana
        hissa yahan sirf `reset()` karta tha - matlab text chup-chaap gayab.
        Silence ke hisse par ye text wapas aata hai (`wake/gate.py` ke `_flush`
        se trigger tak jaata hai)."""
        try:
            raw = self.recognizer.FinalResult()
        except Exception as exc:
            log.warning("finalresult fail: %s: %s", type(exc).__name__, exc)
            return ""
        text = _text(raw)
        if text:
            self.finals += 1
        return text

    def reset(self) -> None:
        """Pichla text bhool jao. Wake hit ke baad aur lambi khamoshi par."""
        try:
            self.recognizer.Reset()
            self.resets += 1
        except Exception as exc:
            log.warning("reset fail: %s: %s", type(exc).__name__, exc)


def build(folder: str = "") -> Listener:
    """Model load + listener banao (worker ke liye ek hi raasta)."""
    return Listener(model_mod.load(folder))
