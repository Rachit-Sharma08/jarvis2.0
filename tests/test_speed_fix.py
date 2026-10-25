"""Wake path ki do aur speed fix — warm-up overlap + chhoti chuppi (Step 2).

Log me kya tha (3 Oct):
    TIME wake_command: TOTAL 18450ms | ack=3520ms warmup=1036ms capture=8088ms
    brain: 1097-1692ms   (brain tez tha — der wake path me thi)

1. **Warm-up ab ack ke saath** (`wake/listen.py: warmup(deadline=...)`). Mic
   hamesha chalta hai (duty cycle), is liye "Ji, boliye" bolte waqt bhi settle
   ho jaata hai. Pehle har baar 1 s ka **dead time** tha, jabki ack ki awaaz
   2 s chal chuki hoti thi. Ab `wake/command.py` ack shuru karne ka time
   `settled_by` deta hai aur jitna poora hua utna hi wait hota hai.
2. **Chuppi 2.0 s -> 1.2 s** (`config_wake.COMMAND_END_SILENCE_SECONDS`). 2.0 s
   sirf ek intezaar me jaata tha. 1.2 s abhi bhi ek natural sentence-gap se
   lamba hai. `.env` ke `JARVIS_CMD_SILENCE` se badal sakte ho — Step 2 (STT)
   isi knob ko tune karega (zyada chuppi = thoda sa slow par pakka text).

Ack ka cache alag suite me hai (`tests/test_tts_cache.py`) — ye dono
production file nahi chalaate, sirf `listen.warmup` ke pure timing ko naapte
hain (fake mic queue, koi audio nahi).
"""

import queue
import sys
import time
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from core import timing
from wake import listen
from wakehelp import check, finish


class FakeMic:
    """Sirf `.chunks` queue chahiye `drain()` ko (wahi `wake/audio.py` ka raasta)."""

    alive = True

    def __init__(self, n=3):
        self.chunks = queue.Queue()
        for _ in range(n):
            self.chunks.put(b"chunk")


class TestWarmupDeadline(unittest.TestCase):
    """Warm-up: deadline diya to jitna bacha wait, warna poora."""

    def test_full_wait_without_deadline(self):
        mic = FakeMic()
        start = time.perf_counter()
        dropped = listen.warmup(mic, None)
        took = time.perf_counter() - start
        check("purana wait hua", took >= config.COMMAND_WARMUP_SECONDS * 0.5, True)
        check("queue khaali", dropped, 3)

    def test_deadline_gone_is_almost_free(self):
        """Ack 2 s chala, deadline nikal chuka -> warm-up lagbhag 0."""
        mic = FakeMic()
        start = time.perf_counter()
        dropped = listen.warmup(mic, None, deadline=time.monotonic() - 1)
        took = time.perf_counter() - start
        check("wait nahi kiya", took < 0.05, True)
        check("phir bhi queue khaali", dropped, 3)

    def test_partial_deadline_waits_only_remaining(self):
        mic = FakeMic()
        start = time.perf_counter()
        listen.warmup(mic, None, deadline=time.monotonic() + 0.3)
        took = time.perf_counter() - start
        check("sirf bacha hua wait", 0.2 < took < 0.8, True)


class TestSilenceWindow(unittest.TestCase):
    """Chuppi 0.7 s (pehle 2.0 -> 1.2 -> 0.9 -> 0.7, 13-Oct) — na bahut jaldi,
    na bahut der. Har 0.1 s seedha wake ke total me judta hai."""

    def test_silence_window(self):
        check("chuppi 0.7 s", config.COMMAND_END_SILENCE_SECONDS, 0.7)
        check("purane 0.9 se tez", config.COMMAND_END_SILENCE_SECONDS < 0.9, True)
        check("sentence gap se lamba", config.COMMAND_END_SILENCE_SECONDS > 0.6, True)

    def test_speech_limits_unchanged(self):
        """Sirf **end** ki chuppi badli — beech ka 0.4 s hangover aur 30 s max
        waise hi hain, warna beech ka vaakya kat jaata."""
        check("hangover", config.COMMAND_HANGOVER_SECONDS, 0.4)
        check("max seconds", config.COMMAND_MAX_SECONDS, 30)
        check("min seconds", config.COMMAND_MIN_SECONDS, 0.6)

    def test_env_can_override(self):
        """`.env` se badal sakte ho — Step 2 is knob ko tune karega."""
        import os
        os.environ["JARVIS_CMD_SILENCE"] = "1.6"
        try:
            import importlib
            import config_wake
            importlib.reload(config_wake)
            check("env se 1.6", config_wake.COMMAND_END_SILENCE_SECONDS, 1.6)
        finally:
            os.environ.pop("JARVIS_CMD_SILENCE", None)
            import importlib
            import config_wake
            importlib.reload(config_wake)


class TestTimingStages(unittest.TestCase):
    """Step 2c ka contract: stage time ek hi `TIME` line me."""

    def test_stopwatch_runs(self):
        w = timing.Stopwatch("fake")
        for name in ("ack", "warmup", "capture", "stt", "brain", "speak"):
            w.stage(name, time.perf_counter())
        w.total()   # crash nahi hona chahiye

    def test_command_uses_those_stages(self):
        """`wake/command.py` ke stage naam wahi hone chahiye — warna log me koi
        stage hi na dikhe aur speed ka hisaab hi na ban paaye."""
        src = (ROOT / "wake" / "command.py").read_text(encoding="utf-8")
        for name in ("ack", "warmup", "capture", "stt", "brain", "speak"):
            check('stage("%s")' % name, 'watch.stage("%s"' % name in src, True)

    def test_command_passes_deadline(self):
        """Warm-up ka deadline `command.py` hi deta hai — warna fix chup-chaap
        kaam hi nahi karega (default raasta poora wait kar leta hai)."""
        src = (ROOT / "wake" / "command.py").read_text(encoding="utf-8")
        check("settled_by bana", "settled_by" in src, True)
        check("deadline diya", "deadline=settled_by" in src, True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("speed fix (warmup + silence) theek"
           if result.wasSuccessful() else "FAIL")