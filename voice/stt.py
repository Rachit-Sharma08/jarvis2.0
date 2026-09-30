import asyncio
import io

from groq import Groq

import config
from log_setup import get_logger

log = get_logger("stt")


class SttError(Exception):
    pass


def _transcribe(audio: bytes) -> str:
    client = Groq(api_key=config.GROQ_API_KEY)
    reply = client.audio.transcriptions.create(
        file=("mic.webm", io.BytesIO(audio)),
        model=config.GROQ_STT_MODEL,
    )
    return (reply.text or "").strip()


async def transcribe(audio: bytes) -> str:
    """Browser ka recording -> text (Hindi + English dono samajhta hai)."""
    if not config.has_groq():
        raise SttError("GROQ_API_KEY missing hai. .env check karo.")
    if not audio:
        raise SttError("Recording khaali aayi.")

    try:
        text = await asyncio.to_thread(_transcribe, audio)
    except Exception as exc:
        log.error("stt failed: %s: %s", type(exc).__name__, exc)
        raise SttError(f"Sun nahi paya ({exc}).") from exc

    if not text:
        log.warning("stt ne khaali text diya")
        raise SttError("Sun nahi paya. Thoda loud bolke try karo.")

    log.info("stt ok: %d chars", len(text))
    return text