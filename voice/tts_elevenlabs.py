import httpx

import config
from log_setup import get_logger

log = get_logger("tts_elevenlabs")
URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class TtsError(Exception):
    pass


async def speak(text: str, mode: str) -> bytes:
    if not config.has_elevenlabs():
        raise TtsError("ELEVENLABS_API_KEY missing")

    voice = config.voice_id("elevenlabs", mode) or config.ELEVENLABS_DEFAULT_VOICE
    payload = {"text": text, "model_id": config.ELEVENLABS_MODEL}
    headers = {"xi-api-key": config.ELEVENLABS_API_KEY}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            reply = await client.post(
                URL.format(voice_id=voice), json=payload, headers=headers
            )
            reply.raise_for_status()
            audio = reply.content
    except Exception as exc:
        log.error("elevenlabs failed: %s: %s", type(exc).__name__, exc)
        raise TtsError(f"ElevenLabs error: {exc}") from exc

    if not audio:
        raise TtsError("ElevenLabs ne khaali audio diya")

    log.info("elevenlabs ok: %d bytes", len(audio))
    return audio