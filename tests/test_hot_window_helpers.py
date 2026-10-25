"""Hot window ke pure helper + wiring (KAAM 5 ka doosra hissa).

`test_hot_window.py` ke saathi. Yahan teen baatein hain:

1. `is_utterance()` ab `wake/followup.py` me hai (trigger.py 200 cross kar
   gaya tha) — aur wahi silence list use karta hai jo STT.
2. Wiring: `command.py` ke `finally` -> `worker.mark_hot()` ->
   `Session.set_hot()` -> `Trigger.mark_hot()`, aur release ke **BAAD**.
3. Ek wake ke baad teen follow-up + apni awaaz se follow-up nahi.

Koi mic/Vosk nahi — sirf `Trigger` (pure time) aur source-check.
"""

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
from tests.wakehelp import check, finish
from tests.wakecmdhelp import patch
from wake import followup as followup_mod
from wake import trigger as trigger_mod
from wake import worker


def fresh(enabled=False):
    """`Trigger` + uska call log. Flag `enabled` par khola hua."""
    t = trigger_mod.Trigger()
    t.fired = []
    t.on_wake = lambda phrase, mic=None, stop=None: t.fired.append(phrase)
    if enabled:
        config.HOT_WINDOW_ENABLED = True
    return t


class TestDefaultOff(unittest.TestCase):
    """DEFAULT OFF — sabse zaroori check."""

    def setUp(self):
        self.saved = config.HOT_WINDOW_ENABLED

    def tearDown(self):
        config.HOT_WINDOW_ENABLED = self.saved

    def test_flag_is_off_by_default(self):
        check("default 0 hai", self.saved, False)
        check("source me bhi 0",
              'os.getenv("JARVIS_HOT_WINDOW", "0")' in
              (ROOT / "config_wake.py").read_text(encoding="utf-8"), True)

    def test_mark_hot_does_nothing_when_off(self):
        config.HOT_WINDOW_ENABLED = False
        t = fresh(False)
        check("mark_hot = False", t.mark_hot(12.0), False)
        check("hot_active = False", t.hot_active(), False)

    def test_no_followup_without_wake_word_when_off(self):
        """Band par "sabse bada test": sirf bolne par trigger NAHI hona chahiye."""
        config.HOT_WINDOW_ENABLED = False
        t = fresh(False)
        check("follow-up nahi", t.maybe("aur mausam batao"), False)
        check("kuch nahi fired", t.fired, [])
        check("waise 'jarvis' se hota hai", t.maybe("jarvis"), True)

    def test_reset_clears_hot(self):
        config.HOT_WINDOW_ENABLED = True
        t = fresh(True)
        t.mark_hot(12.0)
        check("hot tha", t.hot_active(), True)
        t.reset_cooldown()
        check("reset ke baad band", t.hot_active(), False)
        config.HOT_WINDOW_ENABLED = self.saved


class TestIsUtterance(unittest.TestCase):
    """Sirf asli baat follow-up hai."""

    def test_real_sentences_yes(self):
        for text in ("aur mausam batao", "kya kar raha hai", "ek kaam karo",
                     "subah ka reminder set kar do"):
            check(f"baat: {text[:18]}", followup_mod.is_utterance(text), True)

    def test_silence_and_short_no(self):
        for text in ("uh", "hmm", "um", "Thank you.", "Bye.", "okay.",
                     "", "   ", "haan", "ji", "a"):
            check(f"baat nahi: {text!r}", followup_mod.is_utterance(text), False)

    def test_reuses_stt_guard(self):
        """Ek hi silence list — STT aur follow-up dono wahi."""
        src = (ROOT / "wake" / "followup.py").read_text(encoding="utf-8")
        check("stt_guard use hota hai", "stt_guard.is_silence_phrase" in src, True)
        # Sirf ASSIGNMENT nahi - `stt_guard.SILENCE_PHRASES` ka **reference**
        # sahi hai (duplicate list banana hi galat hota).
        check("duplicate list nahi", "SILENCE_PHRASES =" in src, False)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("hot window helpers" if result.wasSuccessful() else "FAIL")
