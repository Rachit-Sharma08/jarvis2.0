"""Local STT test ke fakes — `test_stt_local.py` aur engine test dono ke liye.

`WhisperModel` kabhi load nahi hota: `FakeModel` wahi do cheezein deta hai jo
`voice/stt_local.py` padhta hai (segments ka iterator + info).
"""

import io
import time
import wave

import numpy as np


def wav_bytes(samples, rate=16000, channels=1) -> bytes:
    """float32 (-1..1) -> WAV bytes (16-bit PCM)."""
    pcm = (np.clip(np.asarray(samples, dtype=np.float32), -1, 1) * 32767).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    return buf.getvalue()


class FakeSegment:
    def __init__(self, text):
        self.text = text


class FakeModel:
    """`WhisperModel` ka nakla — kwargs aur source pakadta hai."""

    def __init__(self, text="Jarvis WhatsApp kholo", sleep=0.0):
        self.text = text
        self.sleep = sleep
        self.calls = []

    def transcribe(self, source, **kw):
        self.calls.append({"source": source, "kw": kw})
        if self.sleep:
            time.sleep(self.sleep)
        return iter([FakeSegment(" " + self.text + " ")]), None
