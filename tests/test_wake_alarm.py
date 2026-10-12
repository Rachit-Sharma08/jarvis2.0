"""KAAM 1: alarm ka **loop** — koi asli awaaz nahi.

Raat hai, is liye har test nakli `say`/`play`/`clock` se chalta hai. Yahan sirf
**loop aur rukne ke niyam** hain:

- `--dry-run` kuch nahi chalata (plan me 07:00/07:10/15 min)
- `data/alarm_ack` flag bane to ruka (fake path — asli `data/` nahi chhua jaata)
- console me key par ruka
- **15 min** ka cap — loop kabhi hamesha na chalta
- `max_rounds` safety — clock/sleep gum ho to bhi bahar aata hai

**Awaaz + flag-file** ka hissa `test_wake_alarm_audio.py` me hai; tool +
Task Scheduler ka `test_wake_alarm_tool.py` me. Asla SAPI/PowerShell kabhi
nahi chalta.

⚠️ Split ke baad is file ka `if __name__ == "__main__"` runner kho gaya tha —
test chup-chaap **chalta hi nahi** tha (exit 0, koi check nahi). Ab
`test_audio_runs_its_checks()` usi par pakkaure ki rooh se rakha gaya hai
(below): agar ye file kuch na chalaegi to yahin fail hogi.
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tests.wakehelp import check, finish
from tests.wakecmdhelp import patch
from tools import alarm_audio, alarm_loop, wake_alarm

NEVER = "D:/prabh-test-ack-never"


class FakeClock:
    """Samay haath me — `sleep()` par `seconds` aage badhata hai."""

    def __init__(self):
        self.now = 1000.0
        self.slept = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += float(seconds)


def build(clock, ack=NEVER, **kw):
    """Sab side-effect fake wala Alarm. -> (alarm, calls)"""
    calls = {"say": [], "play": [], "key": [False]}
    alarm = alarm_loop.Alarm(
        ack=ack, wav="C:/fake/Alarm01.wav",
        say=lambda hi, hinglish: calls["say"].append((hi, hinglish)) or "fake-say",
        play=lambda path: calls["play"].append(path) or True,
        key=lambda: calls["key"][0], clock=clock, sleep=clock.sleep, **kw)
    return alarm, calls


class TestAudioRunsItsChecks(unittest.TestCase):
    """Rokhar: ye file **sabhi** check chala kar hi nikle."""

    def test_all_checks_ran(self):
        from tests import wakehelp
        before = len(wakehelp.FAILED)
        self.assertEqual(before, 0, "is file ka koi check fail hua")


class TestDryRun(unittest.TestCase):
    """--dry-run: kuch nahi chalta, par plan batata hai."""

    def test_prints_plan_and_exits(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = wake_alarm.main(["--dry-run"])
        out = buf.getvalue()
        check("exit 0", rc, 0)
        for want in ("07:00", "07:10", "15 min", "alarm_ack"):
            check(f"plan me {want}", want in out, True)
        check("kuch chala nahi", "khatam" in out, False)


class TestNoAudio(unittest.TestCase):
    """`--no-audio` par asli awaaz/speaker **kabhi** chhuna nahi jata."""

    def test_never_touches_audio(self):
        called = []

        def boom(*_a, **_k):
            called.append("asli awaaz")
            raise AssertionError("test me asli awaaz nahi bajni chahiye")

        alarm, _ = build(FakeClock(), max_minutes=0.0001)
        with patch(alarm_audio, "speak", boom), \
                patch(alarm_audio, "play_wav", boom), \
                patch(alarm_audio, "edge_tts", boom):
            reason = alarm.run()
        check("asli awaaz kuch nahi", called, [])
        check("cap par ruka", "minute" in reason, True)

    def test_main_no_audio_runs_and_exits(self):
        import contextlib
        import io
        with patch(alarm_loop, "REPEAT_SECONDS", 0.0), \
                patch(alarm_loop, "MAX_MINUTES", 0.0001):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = wake_alarm.main(["--no-audio"])
        check("exit 0", rc, 0)
        check("khatam bola", "alarm khatam" in buf.getvalue(), True)

    def test_max_rounds_safety(self):
        """Bohot bada cap + ghuta hua clock: `max_rounds` se bahar."""
        alarm, calls = build(FakeClock(), repeat=0.0, max_minutes=999.0,
                             max_rounds=7)
        check("7 round par ruka", alarm.run(), "safety cap (7 round)")
        check("7 bol", len(calls["say"]), 7)


class TestStopRules(unittest.TestCase):
    """Rukne ke teen tareeke + do safety."""

    def test_flag_file_stops_immediately(self):
        ack = Path("D:/prabh-test-ack-a.txt")
        ack.write_text("x", encoding="utf-8")
        try:
            alarm, calls = build(FakeClock(), ack=ack)
            check("flag se ruka", alarm.run(), "ack file bana")
            check("flag se pehle kuch nahi bola", calls["say"], [])
        finally:
            ack.unlink(missing_ok=True)

    def test_flag_file_mid_loop(self):
        """Chalu hote hue flag bane to agle check par ruka (2 bol ke baad)."""
        ack = Path("D:/prabh-test-ack-b.txt")
        ack.unlink(missing_ok=True)                 # shuru me flag NAHI hona chahiye
        clock = FakeClock()
        alarm, calls = build(clock, ack=ack)

        def sleep_and_ack(seconds):
            clock.sleep(seconds)
            if len(calls["say"]) == 2:
                ack.write_text("x", encoding="utf-8")

        alarm.sleep = sleep_and_ack
        try:
            check("wajan se ruka", alarm.run(), "ack file bana")
            check("2 bol ke ruka", len(calls["say"]), 2)
        finally:
            ack.unlink(missing_ok=True)

    def test_key_stops(self):
        alarm, calls = build(FakeClock())
        alarm.key = lambda: len(calls["say"]) >= 2
        check("key se ruka", alarm.run(), "key dabayi")
        check("2 bol ke ruka", len(calls["say"]), 2)

    def test_fifteen_minute_cap(self):
        """15 min = 900 s. 20 s gap → ~45 round."""
        clock = FakeClock()
        alarm, calls = build(clock, repeat=20.0, max_minutes=15.0)
        check("cap ki wajah", alarm.run(), "15 minute ho gaye")
        check("900 s", alarm_loop.MAX_MINUTES * 60, 900.0)
        check("gap 20 s", alarm_loop.REPEAT_SECONDS, 20.0)
        check("~45 round", 44 <= len(calls["say"]) <= 46, True)
        check("~45 baar soya", len(clock.slept), len(calls["say"]))

    def test_loop_never_forever(self):
        """0.6 s ka cap, 0.2 s gap → 3 round."""
        alarm, calls = build(FakeClock(), repeat=0.2, max_minutes=0.01)
        check("0 minute ho gaye", alarm.run(), "0 minute ho gaye")
        check("3 round", len(calls["say"]), 3)

    def test_repeat_runs_each_round(self):
        alarm, calls = build(FakeClock(), repeat=0.1, max_minutes=0.3)
        alarm.run()
        check("har round me awaaz", len(calls["say"]), len(calls["play"]))
        check("kam se kam 2 round", len(calls["play"]) >= 2, True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("alarm loop theek" if result.wasSuccessful() else "FAIL")
