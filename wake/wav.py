"""Raw PCM -> WAV bytes. Groq ko bhejne se pehle container chahiye.

Wake mic 16 kHz mono 16-bit little-endian deta hai (`wake/audio.py`), aur
Groq Whisper WAV samajhta hai — is liye yahi ek chhota wrapper kaafi hai.

Browser wala raasta alag hai (`ui/recorder.js` webm bhejta hai). Ye **sirf**
wake/command path ke liye hai, is liye chhota rakha gaya hai.

`wave` sirf header (44 byte) jodta hai, encoding nahi badalta — is liye
`duration_ms()` chunk count se hi sahi nikal jaata hai.
"""

import io
import wave

import config
from log_setup import get_logger

log = get_logger("wake_wav")

RATE = config.SAMPLE_RATE
CHANNELS = 1
SAMPLE_WIDTH = 2          # int16


def to_wav(pcm: bytes, rate: int = None) -> bytes:
    """16-bit mono PCM bytes -> WAV bytes. Khaali input par khaali output."""
    if not pcm:
        return b""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as out:
        out.setnchannels(CHANNELS)
        out.setsampwidth(SAMPLE_WIDTH)
        out.setframerate(int(rate or RATE))
        out.writeframes(pcm)
    data = buf.getvalue()
    log.info("wav banaya: %d bytes pcm -> %d bytes wav", len(pcm), len(data))
    return data