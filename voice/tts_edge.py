import edge_tts

import config
from log_setup import get_logger

log = get_logger("tts_edge")


class TtsError(Exception):
    pass


async def speak(text: str, mode: str) -> bytes:
    """Free, key nahi chahiye. Hinglish ke liye Hindi voice."""
    voice = config.EDGE_VOICES.get(mode, config.EDGE_VOICES[config.DEFAULT_MODE])
    buffer = bytearray()

    try:
        speaker = edge_tts.Communicate(text, voice)
        async for chunk in speaker.stream():
            if chunk["type"] == "audio":
                buffer.extend(chunk["data"])
    except Exception as exc:
        log.error("edge-tts failed: %s: %s", type(exc).__name__, exc)
        raise TtsError(f"edge-tts error: {exc}") from exc

    if not buffer:
        raise TtsError("edge-tts ne khaali audio diya")

    log.info("edge-tts ok (%s): %d bytes", voice, len(buffer))
    return bytes(buffer)