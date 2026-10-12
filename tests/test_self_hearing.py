"""KAAM 2: apni hi awaaz se WAKE HIT nahi hona chahiye.

**Asli bug (verified, code padh kar):** command khatam hone par
`wake/command.py` `finally` me `listen.drain()` + `release_from_command()`
karta hai — order sahi hai. Par:

1. `drain()` sirf `MAX_QUEUE_BLOCKS` (400 chunk ≈ **12 s**) tak phenkta hai.
2. Jawab ka TTS **18 s** tak chalta hai (log: `speak 18530ms`), to mic queue
   me hamari awaaz ka ~6 s **bachi** rehta hai.
3. `Trigger.take_fresh()` sirf **ek** chunk bachata tha — uske baad `_loop`
   wahi shor Vosk ko de deta tha → `WAKE HIT` apni hi awaaz se.

**Fix:** tail guard — `release_from_command()` se pehle `set_tail(0.4 s)`, aur
`Session._loop` ab `Trigger.suppressing()` check karta hai (cooldown **ya**
tail). Tail me **koi** chunk trigger nahi kar sakta.

**Sab nakli:** mic queue `FakeMic` se, Vosk `FakeRecognizer` se, koi asli audio
ya speaker nahi. Test me `worker._SESSION` fake hota hai.
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
from wake import trigger as trigger_mod
from wake import worker


class TestTailGuardUnit(unittest.TestCase):
    """`Trigger.mark_tail` / `suppressing()` — pure time, koi mic nahi."""

    def setUp(self):
        self.t = trigger_mod.Trigger()

    def test_default_is_04(self):
        check("default 0.4 s", config.PLAYBACK_TAIL_GUARD_SECONDS, 0.4)
        check("sane range", 0.05 < config.PLAYBACK_TAIL_GUARD_SECONDS < 5.0, True)

    def test_no_tail_by_default(self):
        check("shuru me nahi", self.t.suppressing(), False)

    def test_tail_suppresses(self):
        self.t.mark_tail(0.4)
        check("tail me suppressing", self.t.suppressing(), True)
        check("tail_active bhi", self.t.tail_active(), True)
        check("cooling alag hai", self.t.cooling(), False)

    def test_tail_expires(self):
        self.t.mark_tail(0.05)
        time.sleep(0.12)
        check("0.05 s baad khatam", self.t.suppressing(), False)

    def test_zero_and_negative_safe(self):
        """0 ya negative diya to tail na chhude (crash nahi)."""
        for value in (0, -1, 0.0):
            self.t.mark_tail(value)
            check(f"{value} -> band nahi", self.t.suppressing(), False)

    def test_cooldown_still_works(self):
        """Tail ki wajah se cooldown to nahi mit gaya."""
        self.t._cool_until = time.monotonic() + 5
        check("cooldown se suppressing", self.t.suppressing(), True)
        self.t.mark_tail(0.4)
        check("dono saath", (self.t.cooling(), self.t.tail_active()), (True, True))

    def test_long_answer_needs_more_than_cooldown(self):
        """SABOOT:** cooldown sirf 1.5 s hai par jawab 18 s — is liye cooldown
        khatam hone par bhi apni awaaz trigger kar sakti thi."""
        check("cooldown 1.5 s", config.WAKE_COOLDOWN_SECONDS, 1.5)
        self.t._cool_until = time.monotonic() - 1      # cooldown khatam
        check("cooldown khatam", self.t.cooling(), False)
        check("tab bhi apni awaaz trigger karegi",
              self.t.suppressing(), False)


class TestSessionUsesSuppressing(unittest.TestCase):
    """`Session._loop` ab `cooling()` nahi, `suppressing()` check karta hai."""

    def test_loop_source_uses_suppressing(self):
        from wake import session as session_mod
        src = (ROOT / "wake" / "session.py").read_text(encoding="utf-8")
        check("_loop me suppressing()", "self._trig.suppressing()" in src, True)
        check("purana cooling() wala check gaya",
              "self._paused.is_set() or self._trig.cooling()" in src, False)

    def test_set_tail_delegates_to_trigger(self):
        from wake import session as session_mod
        made = {}

        class Grab(trigger_mod.Trigger):
            def mark_tail(self, seconds=None):
                made["seconds"] = seconds

        session = session_mod.Session.__new__(session_mod.Session)
        session._trig = Grab()
        session.set_tail(0.4)
        check("trigger ko gaya", made.get("seconds"), 0.4)


class FakeSession:
    """`worker._SESSION` ka nakli — call ka **order** bhi yaad rakhta hai.

    Order hi asli kaam hai: tail pehle, phir unpause — warna unpause ke baad
    loop turant apni hi TTS ka chunk utha leta hai."""

    def __init__(self):
        self.events = []
        self.tail = []
        self.paused = []

    def set_tail(self, seconds=None):
        self.tail.append(seconds)
        self.events.append("tail")

    def set_paused(self, on):
        self.paused.append(bool(on))
        self.events.append("unpause" if not on else "pause")


class TestReleaseOrder(unittest.TestCase):
    """Tail **hold chhodne se pehle** lagna chahiye."""

    def setUp(self):
        self.fake = FakeSession()
        self.saved = worker._SESSION
        self.saved_held = worker._HELD
        worker._SESSION = self.fake

    def tearDown(self):
        worker._SESSION = self.saved
        worker._HELD = self.saved_held

    def test_release_marks_tail_then_unpauses(self):
        worker._HELD = True
        worker.release_from_command()
        check("tail laga", self.fake.tail, [config.PLAYBACK_TAIL_GUARD_SECONDS])
        check("phir unpause", self.fake.paused, [False])
        check("order: tail PEHLE, phir unpause", self.fake.events,
              ["tail", "unpause"])

    def test_release_without_hold_does_nothing(self):
        worker._HELD = False
        worker.release_from_command()
        check("kuch nahi hua", (self.fake.tail, self.fake.paused), ([], []))

    def test_source_calls_set_tail(self):
        src = (ROOT / "wake" / "worker.py").read_text(encoding="utf-8")
        check("worker me set_tail hai", "_SESSION.set_tail(" in src, True)


class TestSelfHearingPath(unittest.TestCase):
    """Poora raasta: 18 s ki apni awaaz ke baad bhi trigger nahi."""

    def test_own_voice_ignored_after_long_tts(self):
        """Bade jawab ke baad: cooldown 1.5 s guzar chuka, par tail 0.4 s hai —
        isi der me aaya chunk pheka jana chahiye, trigger nahi."""
        t = trigger_mod.Trigger()
        fired = []
        t.on_wake = lambda phrase, mic=None, stop=None: fired.append(phrase)

        # Wake shabd 1.5 s pehle hua tha (cooldown khatam)
        t._cool_until = time.monotonic() - 1.0
        check("cooldown khatam", t.cooling(), False)

        # Command chala aur 18 s baad apni TTS khatam hui
        t.mark_tail(config.PLAYBACK_TAIL_GUARD_SECONDS)
        check("ab suppressing (cooldown khatam par bhi)", t.suppressing(), True)

        # Tail ke dauraan apni awaaz ka chunk aaya
        hit = t.maybe("jarvis aaj mausam kaisa hai")
        check("trigger NAHI hua", hit, False)
        check("koi wake nahi", fired, [])

    def test_after_tail_real_wake_works(self):
        """Guard hat jaye to asli "Jarvis" phir se pakadna chahiye — feature
        mar na jaye (is liye guard window chhota hi rakha)."""
        t = trigger_mod.Trigger()
        fired = []
        t.on_wake = lambda phrase, mic=None, stop=None: fired.append(phrase)
        t.mark_tail(0.05)
        time.sleep(0.12)
        check("tail khatam", t.tail_active(), False)
        check("asli wake pakdi", t.maybe("jarvis"), True)
        check("ek hi wake", len(fired), 1)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("apni awaaz se wake nahi" if result.wasSuccessful() else "FAIL")
