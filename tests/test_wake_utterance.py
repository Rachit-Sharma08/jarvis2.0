"""`wake/utterance.py` + `wake/wav.py` ka test — pura fake, koi mic nahi.

Script: 30 ms ka ek chunk = `wakehelp.loud(1)` (awaaz) ya `quiet(1)` (khamoshi).
Config ke asli window (pre-roll 0.4s, end-silence 2.0s, max 30s, min 0.6s) use
hate hain. Sirf `COMMAND_WAIT_SECONDS` chhota karke test tez rakha gaya hai —
warna "kuch nahi bola" wala case 5 second leta. Patch `config` par hota hai
(`import config` se constant ki copy padhi jati hai, is liye `config_wake`
par patch kaam nahi karega).
"""

import contextlib
import io
import sys
import threading
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.wakehelp import FAILED, check, finish, loud, quiet, show, truthy  # noqa: E402

import config  # noqa: E402
from wake import utterance, wav  # noqa: E402

BLOCK_MS = config.BLOCK_MS


@contextlib.contextmanager
def window(**kw):
    """`config` ke constant test ke liye badlo, phir wapas (har baar)."""
    saved = {key: getattr(config, key) for key in kw}
    for key, value in kw.items():
        setattr(config, key, value)
    try:
        yield
    finally:
        for key, value in saved.items():
            setattr(config, key, value)


class DeadMic:
    """Queue khaali aur mic mara hua — capture turant lautna chahiye."""

    def __init__(self):
        import queue

        self.chunks = queue.Queue()
        self.alive = False
        self.error = "device hat gaya"


def test_capture_silence_only():
    show("capture: sirf khamoshi -> None")
    from tests.wakehelp import FakeMic

    mic = FakeMic([quiet(1) for _ in range(30)])
    with window(COMMAND_WAIT_SECONDS=0.4):
        check("khamoshi me kuch nahi", utterance.capture(mic), None)


def test_capture_speech():
    show("capture: awaaz + khamoshi -> chunk list (end-silence 2.0s)")
    from tests.wakehelp import FakeMic

    speech = [loud(1) for _ in range(25)]
    mic = FakeMic([quiet(1) for _ in range(10)] + speech + [quiet(1) for _ in range(100)])
    got = utterance.capture(mic)
    truthy("kuch mila", got)
    if got:
        # 10 pre-roll + 25 awaaz + 13 hangover + 67 end-silence = 115. Queue me
        # 135 chunk the, is liye 115 par rukna ka matlab **khamoshi par band**.
        truthy("sab se kam 35 chunk", len(got) >= 35)
        check("khamoshi par band hua (queue khaali nahi hui)", len(got) <= 116, True)
        ms = utterance.duration_ms(got)
        truthy("duration 700-3500ms", 700 <= ms <= 3500)


def test_capture_too_short():
    show("capture: bahut chhoti awaaz -> None (min 0.6s)")
    from tests.wakehelp import FakeMic

    mic = FakeMic([loud(1)] + [quiet(1) for _ in range(60)])
    check("2 chunk se kam nahi maana", utterance.capture(mic), None)


def test_capture_max_seconds():
    show("capture: COMMAND_MAX_SECONDS par hi kaat-ta hai (safety limit)")
    from tests.wakehelp import FakeMic

    # FakeMic ki queue sirf 400 chunk rakh sakti hai, is liye asli 30s (1000
    # chunk) preload nahi ho sakta. Window chhota karke wahi niyam test karte
    # hain: 1.5 s = 50 chunk, aur mic poori der bolta rahe.
    mic = FakeMic([loud(1) for _ in range(400)])
    with window(COMMAND_MAX_SECONDS=1.5):
        got = utterance.capture(mic)
    truthy("mila", got)
    if got:
        check("1.5s = 50 chunk par hi ruka", len(got), 50)


def test_capture_stop_event():
    show("capture: app band ho raha hai -> None")
    from tests.wakehelp import FakeMic

    stop = threading.Event()
    stop.set()
    mic = FakeMic([loud(1) for _ in range(10)])
    check("stop set hai to None", utterance.capture(mic, stop), None)


def test_capture_dead_mic():
    show("capture: mic mar gaya, queue khaali -> None (ruk na paye)")
    check("dead mic", utterance.capture(DeadMic()), None)


def test_helpers():
    show("helpers: duration_ms / pcm / is_stop_command")
    chunks = [loud(1)] * 10
    check("duration 10 chunk = 300ms", utterance.duration_ms(chunks), 10 * BLOCK_MS)
    check("pcm jodi", len(utterance.pcm(chunks)), len(chunks[0]) * 10)
    check("ruk jao", utterance.is_stop_command("ruk jao bhai"), True)
    check("thanks", utterance.is_stop_command("Thanks!"), True)
    check("normal command", utterance.is_stop_command("WhatsApp kholo"), False)


def test_wav():
    show("wav: PCM -> WAV header + frames")
    check("khaali PCM", wav.to_wav(b""), b"")
    pcm = loud(20)
    data = wav.to_wav(pcm)
    truthy("RIFF se shuru", data.startswith(b"RIFF"))
    truthy("WAVE me hai", b"WAVE" in data[:12])
    with wave.open(io.BytesIO(data), "rb") as got:
        check("channels", got.getnchannels(), 1)
        check("sample width", got.getsampwidth(), 2)
        check("rate", got.getframerate(), config.SAMPLE_RATE)
        check("frames byte me wahi", got.readframes(got.getnframes()), pcm)
    check("header 44 byte", len(data), 44 + len(pcm))


test_capture_silence_only()
test_capture_speech()
test_capture_too_short()
test_capture_max_seconds()
test_capture_stop_event()
test_capture_dead_mic()
test_helpers()
test_wav()
finish("wake utterance + wav theek")