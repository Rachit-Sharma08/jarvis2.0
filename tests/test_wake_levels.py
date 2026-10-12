"""S-2: Chuppi 0.7 s + har command ka **level** log (peak RMS + clipping %).

S-1 audit ka saboot: real app ke peek RMS ka median **0.107** tha (VAD threshold
0.0075 se 14x upar) aur 7% cases **0.5+** — matlab mic ya to bahut tez hai
(clipping) ya bahut dheere. Usi bad audio me Whisper koi bhi bhasha bana deta
hai (`Hva er etta?` = Icelandic).

Is liye har command ke log me **do number** aate hain:

    command capture: 113 chunk = 3389ms | peak_rms=0.6210 clip=3.40%

Sirf number — audio kahin save nahi hoti (privacy ka pakkaura).

**Koi asli mic nahi** — `FakeMic` + numpy tone.
"""

import logging
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

import config
import config_wake
from log_setup import ascii_text, get_logger
from tests.wakehelp import FakeMic, check, finish, loud, quiet
from wake import pcm
from wake import utterance


def tone(blocks=1, amp=6000):
    """`wakehelp.loud()` jaisa chunk, par amplitude apni marzi."""
    raw = b""
    for _ in range(blocks):
        raw += (np.sin(np.arange(480) * 0.4) * amp).astype("<i2").tobytes()
    return raw


def square(blocks=1):
    """Full-scale **square** wave — har sample clip par. Asli clip ka model."""
    raw = b""
    for _ in range(blocks):
        wave = np.sign(np.sin(np.arange(480) * 0.4)) * 32767
        raw += wave.astype("<i2").tobytes()
    return raw


class TestQualityPure(unittest.TestCase):
    """`wake/pcm.py` ka `quality()` — pure, mic ke bina."""

    def test_empty(self):
        check("None", pcm.quality(None), (0.0, 0.0))
        check("khali list", pcm.quality([]), (0.0, 0.0))
        check("sirf khali chunk", pcm.quality([b""]), (0.0, 0.0))

    def test_known_rms(self):
        """Amp 6000 int16 -> RMS = 6000/sqrt(2)/32768 ~ 0.129 (log me bhi yahi
        test ka signature dikhta tha)."""
        peak, clip = pcm.quality([tone(2, 6000)])
        check("peak RMS ~0.129", round(peak, 2), 0.13)
        check("clip nahi", clip, 0.0)

    def test_peak_is_max_not_mean(self):
        quiet_rms, _ = pcm.quality([tone(1, 3000)])
        loud_rms, _ = pcm.quality([tone(1, 3000), tone(1, 24000)])
        check("peak = sabse bada chunk", loud_rms > quiet_rms, True)

    def test_clipping_detected(self):
        """Full-scale sine (amp 32767): RMS ~0.707 (1.0 nahi — sine ka RMS
        amplitude/sqrt(2) hota hai), par kuch samples clip par hain."""
        peak, clip = pcm.quality([tone(4, 32767)])
        check("clip pakda", clip > 0, True)
        check("RMS sine ka 0.707 hai", round(peak, 2), 0.71)

    def test_hard_clip_almost_all_samples(self):
        """Square wave full-scale — yani mic **poori tarah** clip kar raha hai.
        Square ka RMS = amplitude (constant), is liye peak 1.0."""
        peak, clip = pcm.quality([square(4)])
        check("clip ~100%", clip > 99.0, True)
        check("square ka RMS = peak", round(peak, 1), 1.0)

    def test_normal_speech_no_clip(self):
        """Asli bol-chal ka level (RMS ~0.02-0.2) clip nahi hona chahiye —
        S-1 ka yahi nuksan tha."""
        _, clip = pcm.quality([tone(20, 6000)])
        check("normal level me clip 0", clip, 0.0)


class TestCaptureLog(unittest.TestCase):
    """`wake/utterance.py` ki log line me dono number aane chahiye."""

    def lines(self, fn):
        """Ek capture chala kar `wake_utterance` ki nayi log lines de."""
        logger = get_logger("wake_utterance")
        box = []

        class Grab(logging.Handler):
            def emit(self, record):
                box.append(ascii_text(record.getMessage()))

        handler = Grab()
        logger.addHandler(handler)
        try:
            fn()
        finally:
            logger.removeHandler(handler)
        return box

    def test_success_line_has_levels(self):
        mic = FakeMic([loud(40) for _ in range(40)] + [quiet(40) for _ in range(40)])
        got = self.lines(lambda: utterance.capture(mic, None))
        cap = [ln for ln in got if ln.startswith("command capture:")]
        check("capture line mili", len(cap), 1)
        check("peak_rms log hua", "peak_rms=" in cap[0], True)
        check("clip log hua", "clip=" in cap[0], True)

    def test_small_line_also_has_levels(self):
        """Chhoti capture par bhi — wahi nateeja dekhna hai (kya sunai diya)."""
        mic = FakeMic([loud(2)] + [quiet(60)])
        got = self.lines(lambda: utterance.capture(mic, None))
        cap = [ln for ln in got if ln.startswith("command capture:")]
        check("chhota wala line mili", len(cap), 1)
        check("chhote me bhi peak_rms", "peak_rms=" in cap[0], True)
        check("chhote me bhi clip", "clip=" in cap[0], True)

    def test_log_me_audio_nahi(self):
        """Sirf number — raw bytes kabhi log me na aayein (privacy)."""
        mic = FakeMic([tone(40, 12000)] + [quiet(40)])
        got = self.lines(lambda: utterance.capture(mic, None))
        joined = " ".join(got)
        check("log me 'chunk =' sirf count hai",
              "chunk =" in joined or "chhota (" in joined, True)
        check("raw int16 marker nahi", "\\x00" in joined, False)


class TestSilenceDefault(unittest.TestCase):
    """End-silence 0.7 s (pehle 0.9). `.env` se badalna waise hi chalta hai."""

    def test_default_is_07(self):
        check("default 0.7", config_wake.COMMAND_END_SILENCE_SECONDS, 0.7)
        check("purane 0.9 se tez", config_wake.COMMAND_END_SILENCE_SECONDS < 0.9, True)
        check("0.6 s se lamba (voice-start bhi na kaate)",
              config_wake.COMMAND_END_SILENCE_SECONDS > 0.6, True)
        check("config me bhi wahi", config.COMMAND_END_SILENCE_SECONDS, 0.7)

    def test_env_override_still_works(self):
        import importlib
        import os
        saved = os.environ.get("PRABH_CMD_SILENCE")
        os.environ["PRABH_CMD_SILENCE"] = "1.2"
        try:
            importlib.reload(config_wake)
            check("env se 1.2", config_wake.COMMAND_END_SILENCE_SECONDS, 1.2)
        finally:
            if saved is None:
                os.environ.pop("PRABH_CMD_SILENCE", None)
            else:
                os.environ["PRABH_CMD_SILENCE"] = saved
            importlib.reload(config_wake)

    def test_other_windows_unchanged(self):
        """Sirf **end** ki chuppi — beech ka hangover aur min/max waise hi."""
        check("hangover", config.COMMAND_HANGOVER_SECONDS, 0.4)
        check("min", config.COMMAND_MIN_SECONDS, 0.6)
        check("max", config.COMMAND_MAX_SECONDS, 30)
        check("pre-roll", config.COMMAND_PRE_ROLL_SECONDS, 0.6)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("chuppi 0.7 + level log" if result.wasSuccessful() else "FAIL")
