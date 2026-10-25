"""Wake suite ka shared helper (tests/poolhelp.py / desktophelp.py jaisa).

Yahan **asli mic, Vosk model aur `sounddevice` kabhi nahi** chalti. Sirf teen
fake: `FakeRecognizer` (Vosk jaisa JSON), `FakeListener` (text ki list) aur
`FakeMic` (chunk queue). Isi se worker ka poora loop test hota hai.
"""

import json
import queue
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def truthy(name, got):
    check(name, bool(got), True)


def show(name):
    print(f"       {name}")


def finish(title):
    print()
    if FAILED:
        print(f"{len(FAILED)} test fail: {FAILED}")
        sys.exit(1)
    print(title)
    sys.exit(0)


def use_fake_model() -> None:
    """`wake_available()` sirf folder ka **hona** dekhta hai - asli 40 MB Vosk
    model ki zarurat nahi. Test ke shuru me dono model path ek temp folder par
    point kar do, warna suite machine par depend karti hai (model ho to pass)."""
    import tempfile

    import config_wake

    folder = Path(tempfile.gettempdir()) / "jarvis-fake-vosk"
    folder.mkdir(parents=True, exist_ok=True)
    config_wake.WAKE_MODEL_DIR = config_wake.WAKE_MODEL_ALT_DIR = str(folder)


def wait(until, seconds: float = 2.0) -> bool:
    """Chhota intezaar — worker thread ke kaam ka (jaise `listener.reset()`)."""
    import time

    end = time.time() + seconds
    while time.time() < end:
        if until():
            return True
        time.sleep(0.02)
    return until()


def loud(blocks: int = 1) -> bytes:
    """'Bolo' jaisa chunk — RMS threshold se upar. (`wake/audio.py` ke bina)."""
    import numpy as np

    raw = b""
    for _ in range(blocks):
        tone = (np.sin(np.arange(480) * 0.4) * 6000).astype("<i2").tobytes()
        raw += tone
    return raw


def quiet(blocks: int = 1) -> bytes:
    return b"\x00\x00" * (480 * blocks)


class FakeRecognizer:
    """Vosk `KaldiRecognizer` ka nakli — script se text deta hai."""

    def __init__(self, texts=None, partial: str = "", raw_text=None, pending: str = ""):
        self.queue = list(texts or [])
        self.partial_text = partial
        self.pending = pending          # `FinalResult()` ka text (flush ke liye)
        self.raw_text = raw_text          # ajeeb JSON ke liye
        self.bytes_fed = 0
        self.resets = 0
        self.finalized = 0

    def AcceptWaveform(self, raw):
        self.bytes_fed += len(raw)
        return bool(self.queue)

    def Result(self):
        if self.raw_text is not None:
            return self.raw_text
        return json.dumps({"text": self.queue.pop(0) if self.queue else ""})

    def PartialResult(self):
        return json.dumps({"partial": self.partial_text})

    def FinalResult(self):
        """Vosk ka force-final: pending text de deta hai (`flush()` ka raasta)."""
        self.finalized += 1
        text, self.pending = self.pending, ""
        return json.dumps({"text": text})

    def Reset(self):
        self.resets += 1
        self.queue = []
        self.partial_text = ""
        self.pending = ""


def make_listener(texts=None, partial: str = "", raw_text=None, pending: str = ""):
    """`detect.Listener` + uska fake — `vosk.KaldiRecognizer` ko badal kar."""
    from wake import detect

    import vosk

    fake = FakeRecognizer(texts, partial, raw_text, pending)
    original = vosk.KaldiRecognizer
    vosk.KaldiRecognizer = lambda *a, **k: fake
    try:
        return detect.Listener(vosk_model=object()), fake
    finally:
        vosk.KaldiRecognizer = original


class FakeListener:
    """`detect.Listener` jaisa, lekin text ki list se. Worker test ke liye."""

    def __init__(self, texts=None, pending: str = "", partial: str = ""):
        self.queue = list(texts or [])
        self.pending = pending          # flush par ye milega
        self.partial_text = partial      # partial() ka jawab (trigger ka raasta)
        self.finals = 0
        self.resets = 0
        self.flushes = 0

    def feed(self, raw):
        if not self.queue:
            return ""
        self.finals += 1
        return self.queue.pop(0)

    def partial(self):
        return self.partial_text

    def flush(self):
        self.flushes += 1
        text, self.pending = self.pending, ""
        return text

    def reset(self):
        self.resets += 1
        self.pending = ""


class FakeMic:
    """`wake/audio.py` ka nakli — queue + `alive` + `stop()`."""

    def __init__(self, chunks=None):
        self.chunks: queue.Queue = queue.Queue(maxsize=400)
        for raw in chunks or []:
            self.chunks.put_nowait(raw)
        self.alive = True
        self.error = ""
        self.stopped = False

    def start(self):
        self.alive = True
        return True

    def stop(self):
        self.alive = False
        self.stopped = True

    def feed(self, raw):
        self.chunks.put_nowait(raw)
