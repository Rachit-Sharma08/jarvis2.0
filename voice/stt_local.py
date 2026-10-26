"""Local STT — faster-whisper, free aur offline. Groq key na ho to yahi sunta hai.

CPU par `small` int8 ~2x realtime chalta hai (i5-1145G7: 2.8 s audio = 5.9 s),
is liye model **startup par** background thread me load hota hai
(`warm_async`), warna pehli command 4 s extra leti hai.

`language="en"` jaan-boojh kar: language detection ~5 s khaata hai aur Hindi
audio ko Devanagari me likh deta hai; "en" par Hinglish Latin me rehti hai
(wahi jo brain samajhta hai).

Audio kahin disk par nahi jaati — WAV bytes memory me numpy ban jaate hain.
"""

import io
import os
import threading
import wave

import numpy as np

import config
from log_setup import get_logger

log = get_logger("stt_local")

_MODEL = None
_LOCK = threading.Lock()
_BROKEN = ""


def available() -> bool:
    """Model + library dono maujood hain? (call par load nahi hota)."""
    if _BROKEN:
        return False
    if config.STT_LOCAL in ("0", "off", "false", "no", "disabled"):
        return False
    if not os.path.isdir(config.STT_LOCAL_MODEL):
        return False
    try:
        import faster_whisper  # noqa: F401
    except Exception:
        return False
    return True


def _load():
    global _MODEL, _BROKEN
    with _LOCK:
        if _MODEL is not None:
            return _MODEL
        if _BROKEN:
            raise RuntimeError(_BROKEN)
        try:
            from faster_whisper import WhisperModel
            log.info("local stt load: %s", config.STT_LOCAL_MODEL)
            _MODEL = WhisperModel(config.STT_LOCAL_MODEL, device="cpu",
                                  compute_type="int8",
                                  cpu_threads=config.STT_LOCAL_THREADS)
        except Exception as exc:
            # Yaad rakho: toota model har command par dobara load karne ki
            # koshish nahi karta (har baar 4 s barbaad + wahi error).
            _BROKEN = f"{type(exc).__name__}: {exc}"
            log.error("local stt load fail: %s", _BROKEN)
            raise
        return _MODEL


def warm_async() -> None:
    """Startup par model load karo — thread daemon hai, app rukta nahi."""
    if not available():
        return
    threading.Thread(target=_warm, name="stt-warm", daemon=True).start()


def _warm() -> bool:
    try:
        _load()
        log.info("local stt ready")
        return True
    except Exception:
        return False


def _source(audio: bytes):
    """16 kHz mono WAV -> numpy (tez raasta). Baaki (webm/opus) av ko do."""
    if audio[:4] != b"RIFF":
        return io.BytesIO(audio)
    try:
        with wave.open(io.BytesIO(audio), "rb") as w:
            rate, channels = w.getframerate(), w.getnchannels()
            raw = w.readframes(w.getnframes())
    except Exception:
        return io.BytesIO(audio)
    if rate != 16000 or channels != 1 or not raw:
        return io.BytesIO(audio)
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def transcribe(audio: bytes) -> str:
    model = _load()
    segments, _info = model.transcribe(
        _source(audio), beam_size=1, language=config.STT_LANGUAGE or None,
        vad_filter=False, condition_on_previous_text=False,
        without_timestamps=True)
    return " ".join(seg.text.strip() for seg in segments).strip()
