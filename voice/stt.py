import asyncio
import io
import time

from groq import Groq

import config
from log_setup import get_logger
from voice import stt_guard

log = get_logger("stt")


class SttError(Exception):
    pass


def _transcribe(audio: bytes) -> str:
    # `language` jaan-boojh kar NAHI bhejte. Romanized Hinglish (English
    # akshar + Hindi shabd) `language="hi"` par bigaad jata tha — saboot
    # ROUND2.md me. Whisper khud dono script pehchanta hai.
    client = Groq(api_key=config.GROQ_API_KEY, timeout=config.BRAIN_TIMEOUT_GROQ)
    reply = client.audio.transcriptions.create(
        file=("mic.webm", io.BytesIO(audio)),
        model=config.GROQ_STT_MODEL,
    )
    return (reply.text or "").strip()


async def transcribe(audio: bytes, duration_ms=None) -> str:
    """Browser ka recording -> text (Hindi + English dono samajhta hai)."""
    if not config.has_groq():
        raise SttError("GROQ_API_KEY missing hai. .env check karo.")
    if not audio:
        raise SttError("Recording khaali aayi.")
    # Size guard YAHAN hai, sirf route me nahi. Wake path (`wake/listen.py`)
    # bhi yahin se guzarta hai, aur 11 MB ka blob provider tak bhejne ki zaroorat
    # nahi — quota bachega aur test bhi asli network par nahi jaayega.
    if len(audio) > config.AUDIO_MAX_BYTES:
        raise SttError("Recording bahut badi hai.")

    # Chhoti recording (600ms se kam) me insaan ki awaaz nahi hoti — call
    # jyada kharch karega aur text ghalt aayega.
    short = stt_guard.bad_duration(duration_ms)
    if short:
        log.info("stt guard: %s", short)
        raise SttError("Bahut chhoti recording. Thodi der bolke try karo.")

    start = time.perf_counter()
    try:
        text = await asyncio.to_thread(_transcribe, audio)
    except Exception as exc:
        log.error("stt failed (%dms): %s: %s", int((time.perf_counter() - start) * 1000),
                  type(exc).__name__, exc)
        raise SttError(f"Sun nahi paya ({exc}).") from exc

    if not text:
        log.warning("stt ne khaali text diya")
        raise SttError("Sun nahi paya. Thoda loud bolke try karo.")

    # Khamoshi ka nishaan ya galat script — user ko text mat dikhao.
    bad = stt_guard.guard_text(text)
    if bad:
        log.info("stt guard: text reject — %s | %r", bad, text[:60])
        raise SttError("Sun nahi paya (awaz saaf nahi thi). Thoda loud bolke try karo.")

    log.info("TIME stt: %s %dms | %d chars", config.GROQ_STT_MODEL,
             int((time.perf_counter() - start) * 1000), len(text))
    return text