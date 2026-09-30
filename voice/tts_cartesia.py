import httpx

import config
from log_setup import get_logger

log = get_logger("tts_cartesia")
URL = "https://api.cartesia.ai/tts/bytes"


class TtsError(Exception):
    pass


async def speak(text: str, mode: str) -> bytes:
    if not config.has_cartesia():
        raise TtsError("CARTESIA_API_KEY missing")

    voice = config.voice_id("cartesia", mode)
    if not voice:
        raise TtsError("CARTESIA_VOICE id missing")

    headers = {
        "X-API-Key": config.CARTESIA_API_KEY,
        "Cartesia-Version": config.CARTESIA_VERSION,
    }
    payload = {
        "model_id": config.CARTESIA_MODEL,
        "transcript": text,
        "language": "hi",
        "output_format": "mp3",
        "voice": {"mode": "id", "id": voice},
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            reply = await client.post(URL, json=payload, headers=headers)
            reply.raise_for_status()
            audio = reply.content
    except Exception as exc:
        log.error("cartesia failed: %s: %s", type(exc).__name__, exc)
        raise TtsError(f"Cartesia error: {exc}") from exc

    if not audio:
        raise TtsError("Cartesia ne khaali audio diya")

    log.info("cartesia ok: %d bytes", len(audio))
    return audio