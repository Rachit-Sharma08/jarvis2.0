"""KAAM 5: hot window — jawab ke baad "Jarvis" na bole follow-up.

**DEFAULT OFF** (`JARVIS_HOT_WINDOW=0`) — is suite ka sabse bada check yahi hai:
flag band par **purana raasta** chalta hai, yaani follow-up ke liye "jarvis"
shabd zaroori hai.

On karne par: jawab ke baad `HOT_WINDOW_SECONDS` (12 s) tak **sirf bolna**
kaafi hai. Follow-up par window **dobara** lagta hai, is liye teen follow-up
chain kar sakte hain.

Do guard jo hamesha pehle chalte hain (is liye apni awaaz kabhi follow-up
nahi ban sakti):

1. `suppressing()` — cooldown/tail guard (KAAM 2).
2. `is_utterance()` — "uh"/"hmm"/"Thank you." follow-up nahi hai; guard wahi
   jo STT ke liye hai (`voice/stt_guard.py`).

**Koi asli mic/Vosk nahi** — sirf `Trigger` (pure time + fake callback).
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


class TestFollowUps(unittest.TestCase):
    """(on) ek wake ke baad teen follow-up."""

    def setUp(self):
        self.saved = config.HOT_WINDOW_ENABLED
        config.HOT_WINDOW_ENABLED = True

    def tearDown(self):
        config.HOT_WINDOW_ENABLED = self.saved

    def test_three_followups_no_wake_word(self):
        t = fresh(True)
        check("pehla 'jarvis'", t.maybe("jarvis"), True)
        check("window khula", t.mark_hot(12.0), True)
        for text in ("aur mausam batao", "kya kar raha hai", "ek kaam kar do"):
            t._cool_until = 0.0                       # cooldown nikal do
            check(f"follow-up: {text[:16]}", t.maybe(text), True)
        check("4 baar fired (1 wake + 3 follow-up)", len(t.fired), 4)

    def test_window_rearms_on_followup(self):
        t = fresh(True)
        t.mark_hot(12.0)
        t._cool_until = 0.0
        t.maybe("aur mausam batao")
        check("dobara khula", t.hot_active(), True)

    def test_window_expires(self):
        t = fresh(True)
        t.mark_hot(0.05)
        time.sleep(0.12)
        check("0.05 s baad band", t.hot_active(), False)
        check("phir 'jarvis' chahiye", t.maybe("aur mausam batao"), False)
        check("'jarvis' phir se chalega", t.maybe("jarvis"), True)

    def test_own_voice_never_becomes_followup(self):
        """KAAM 2 ka guard pehle hai — apni TTS follow-up nahi ban sakti."""
        t = fresh(True)
        t.mark_hot(12.0)
        t._cool_until = 0.0
        t.mark_tail(0.5)                              # hum bol rahe hain
        check("tail me follow-up nahi", t.maybe("Ji, boliye. Mausam kaisa hai?"),
              False)
        check("kuch nahi fired", t.fired, [])

    def test_cooldown_also_blocks_followup(self):
        t = fresh(True)
        t.mark_hot(12.0)
        t._cool_until = time.monotonic() + 5
        check("cooldown me follow-up nahi", t.maybe("aur mausam batao"), False)

    def test_silence_never_followup(self):
        t = fresh(True)
        t.mark_hot(12.0)
        for text in ("Thank you.", "hmm uh", "Bye."):
            t._cool_until = 0.0
            check(f"{text!r} follow-up nahi", t.maybe(text), False)

    def test_config_defaults(self):
        check("12 second", config.HOT_WINDOW_SECONDS, 12.0)
        check("sane range", 5 <= config.HOT_WINDOW_SECONDS <= 30, True)


class TestWiring(unittest.TestCase):
    """`command.py` -> `worker.mark_hot()` -> `Session.set_hot()`."""

    def test_command_calls_mark_hot(self):
        src = (ROOT / "wake" / "command.py").read_text(encoding="utf-8")
        check("finally me mark_hot", "wake_worker.mark_hot()" in src, True)
        check("release ke BAAD", src.index("wake_worker.mark_hot()") >
              src.index("release_from_command()"), True)

    def test_session_delegates(self):
        made = {}

        class Grab(trigger_mod.Trigger):
            def mark_hot(self, seconds=None):
                made["seconds"] = seconds
                return True

        from wake import session as session_mod
        session = session_mod.Session.__new__(session_mod.Session)
        session._trig = Grab()
        check("set_hot delegate", session.set_hot(12.0), True)
        check("value gaya", made.get("seconds"), 12.0)

    def test_worker_delegates(self):
        called = {}

        class FakeSession:
            def set_hot(self, seconds=None):
                called["seconds"] = seconds
                return True

        saved = worker._SESSION
        worker._SESSION = FakeSession()
        try:
            check("worker.mark_hot", worker.mark_hot(9.0), True)
            check("value gaya", called.get("seconds"), 9.0)
        finally:
            worker._SESSION = saved

    def test_env_override(self):
        check("env key ka naam",
              'os.getenv("JARVIS_HOT_WINDOW"' in
              (ROOT / "config_wake.py").read_text(encoding="utf-8"), True)
        check("seconds bhi env se",
              'os.getenv("JARVIS_HOT_WINDOW_SECONDS"' in
              (ROOT / "config_wake.py").read_text(encoding="utf-8"), True)

    def test_describe_includes_flag(self):
        """`config.describe()` me dikhna chahiye — flag kahan se aaya."""
        text = config.describe()
        check("describe me yaad hai", "hot" in text.lower(), True)



if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("hot window (default off)" if result.wasSuccessful() else "FAIL")
