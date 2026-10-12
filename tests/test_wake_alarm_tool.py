"""Alarm ke do supporting hisse — **default OFF** aur **locale-safe task**.

1. `tools/alarm.py` — Jarvis ka tool. `PRABH_ALARM_TOOL=0` (default) par
   LLM ko dikhta hi nahi aur `execute()` maneta hai. Time parse **pure** hai.
2. `tools/alarm_task.py` — Task Scheduler. `ps_when()` **pure** hai aur
   minute **nahi** chhedta (07:10 ka task 07:00 par ban chuka tha).

**Asla PowerShell kabhi nahi chalta** — `run_powershell` fake se badla gaya.
`schtasks /delete` bhi nahi (task delete ka koi test nahi; woh `--uninstall`
ka kaam hai).
"""

import datetime
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
import tools
from tests.wakehelp import check, finish
from tests.wakecmdhelp import patch
from tools import alarm as alarm_tool
from tools import alarm_task

NOW = datetime.datetime(2026, 10, 13, 2, 0)      # raat 2 baje


class TestParseWhen(unittest.TestCase):
    """`parse_when` pure hai — 2026-10-13 02:00 par sab nateeja."""

    def test_plain_hour(self):
        for text in ("7", "7 baje", "07:00", "kal subah 7 baje", "saat 7"):
            check(f"{text!r} -> 07:00", alarm_tool.parse_when(text, NOW),
                  datetime.datetime(2026, 10, 13, 7, 0))

    def test_minutes_kept(self):
        """"7:30 am" me minute 30 rehna chahiye — pehle regex "30 am" uthata
        tha (yaani 30 ghante) aur ValueError deta tha."""
        check("7:30 am", alarm_tool.parse_when("7:30 am", NOW),
              datetime.datetime(2026, 10, 13, 7, 30))
        check("7.30 pm", alarm_tool.parse_when("7.30 pm", NOW),
              datetime.datetime(2026, 10, 13, 19, 30))
        check("19:00", alarm_tool.parse_when("19:00", NOW),
              datetime.datetime(2026, 10, 13, 19, 0))

    def test_meridiem(self):
        check("9 pm -> 21", alarm_tool.parse_when("9 pm", NOW).hour, 21)
        check("12 am -> 0", alarm_tool.parse_when("12 am", NOW).hour, 0)
        check("12 pm -> 12", alarm_tool.parse_when("12 pm", NOW).hour, 12)

    def test_rolls_to_tomorrow(self):
        """Aaj ka 7:00 nikal chuka ho to **kal** — aaj raat nahi."""
        check("1 baje raat 2 ke baad -> kal",
              alarm_tool.parse_when("1", NOW),
              datetime.datetime(2026, 10, 14, 1, 0))
        # 02:00 par 02:30 aaj hi aane wala hai (aaj raat hi, kal nahi).
        check("2:30 raat 2 par aaj hi", alarm_tool.parse_when("2:30", NOW).day, 13)
        check("1:30 raat 2 par kal", alarm_tool.parse_when("1:30", NOW).day, 14)

    def test_rejects_garbage(self):
        for text in ("", "abc", "7:60", "25:00", "kal"):
            try:
                alarm_tool.parse_when(text, NOW)
                check(f"{text!r} reject hua", "haan", "ValueError")
            except ValueError:
                check(f"{text!r} reject hua", True, True)

    def test_clamp_minutes(self):
        check("3 theek", alarm_tool.clamp_minutes("3"), 3)
        check("99 -> 15", alarm_tool.clamp_minutes("99"), 15)
        check("0 -> 1", alarm_tool.clamp_minutes("0"), 1)
        check("abc -> 15", alarm_tool.clamp_minutes("abc"), 15)


class TestDefaultOff(unittest.TestCase):
    """`PRABH_ALARM_TOOL=0` — LLM ko tool dikhe hi nahi."""

    def test_flag_default_off(self):
        check("default OFF", config.ALARM_TOOL_ENABLED, False)
        check("spec me nahi", "set_wake_alarm" in tools.spec(), False)
        check("disabled list me hai", "set_wake_alarm" in tools.disabled(), True)
        check("alarm_status bhi band", "alarm_status" in tools.disabled(), True)

    def test_execute_refuses(self):
        out = tools.execute("set_wake_alarm", {"at": "7:00", "repeat_minutes": "15"})
        check("mana kar diya", "band hai" in out, True)
        check("file nahi bani", alarm_tool.read_request(), {})

    def test_tool_does_not_touch_scheduler(self):
        """LLM ke text se system nahi badalna — registry nahi, task nahi."""
        src = (ROOT / "tools" / "alarm.py").read_text(encoding="utf-8")
        for bad in ("Register-ScheduledTask", "schtasks", "subprocess"):
            check(f"{bad} alarm.py me nahi", bad in src, False)

    def test_when_enabled_it_writes(self):
        tmp = Path("D:/prabh-test-alarm-req.json")
        try:
            with patch(config, "ALARM_TOOL_ENABLED", True), \
                    patch(alarm_tool, "request_path", lambda: tmp):
                out = alarm_tool.set_wake_alarm("7:00", "15")
                check("set hua", "Alarm set" in out, True)
                data = alarm_tool.read_request()
                check("file me time", data.get("when", "").startswith("2026-"), True)
                check("repeat 15", data.get("repeat_minutes"), 15)
                check("task ka naam", data.get("task"), "JarvisWakeAlarm")
                check("spec me dikhe", "set_wake_alarm" in tools.spec(), True)
                check("status bolta hai", "Alarm:" in alarm_tool.alarm_status(), True)
        finally:
            tmp.unlink(missing_ok=True)

    def test_ask_risk(self):
        """Gatekeeper: alarm tool **ASK** hai (PC ki timing badalta hai)."""
        from gatekeeper import rules
        check("base risk ASK", config.TOOL_BASE_RISK.get("set_wake_alarm"),
              config.ASK)
        risk, _reason = rules.decide("set_wake_alarm", {"at": "7:00"})
        check("decide bhi ASK", risk, config.ASK)


class TestPsWhen(unittest.TestCase):
    """`ps_when` pure hai — aur MINUTE rakhni hai (07:10 ka galti yahi hua)."""

    def test_keeps_minutes(self):
        got = alarm_task.ps_when(datetime.datetime(2026, 10, 14, 7, 10))
        check("minute 10", "-Minute 10" in got, True)
        check("ghanta 7", "-Hour 7" in got, True)
        check("saal", "-Year 2026" in got, True)

    def test_no_locale_format(self):
        """`schtasks /sd` (MM/DD/YYYY) use nahi hona — locale badalta hai."""
        got = alarm_task.ps_when(datetime.datetime(2026, 10, 14, 7, 0))
        check("Get-Date se bana", got.strip().startswith("(Get-Date"), True)
        check("slash nahi", "/" not in got, True)

    def test_never_uses_broken_datetime_new(self):
        """`[datetime]::new(y,m,d,h,mi)` ka 5-arg overload exist hi nahi karta —
        isi wajah se pehli baar trigger bana hi nahi tha.

        **Asal command** me na ho — docstring me likha hua text pakadna galat
        hota hai (source grep aise hi bekaar ho jaata hai)."""
        got = alarm_task.ps_when(datetime.datetime(2026, 10, 14, 7, 10))
        check("command me nahi", "[datetime]::new" in got, False)


class TestInstallDry(unittest.TestCase):
    """`install()` ka command text — PowerShell **chalaya nahi** jaata."""

    def test_two_tasks_ten_minutes_apart(self):
        seen = []

        def fake(command, timeout=90):
            seen.append(command)
            return "OK JarvisWakeAlarm state=Ready start=2026-10-14T07:10:00+05:30"

        with patch(alarm_task, "run_powershell", fake):
            out = alarm_task.install(datetime.datetime(2026, 10, 14, 7, 0))
        check("2 command bane", len(seen), 2)
        check("primary 07:00", "-Hour 7 -Minute 0" in seen[0], True)
        check("backup 07:10", "-Hour 7 -Minute 10" in seen[1], True)
        check("backup me --if-no-ack", "--if-no-ack" in seen[1], True)
        check("primary me flag nahi", "--if-no-ack" in seen[0], False)
        check("dono naam alag", "JarvisWakeAlarm'" in seen[0], True)

    def test_verifies_before_saying_ok(self):
        """`register()` ko "OK" tabhi bolna chahiye jab output me sach me `OK` ho —
        pehli baar `| Out-Null` ne error chhupa diya tha."""
        with patch(alarm_task, "run_powershell", lambda *a, **k: "kuch galti ho gayi"):
            got = alarm_task.register("X", datetime.datetime(2026, 10, 14, 7, 0))
        check("NAHI BANA bola", got.startswith("NAHI BANA"), True)
        src = (ROOT / "tools" / "alarm_task.py").read_text(encoding="utf-8")
        check("ErrorAction Stop hai", "-ErrorAction Stop" in src, True)
        check("aakhir me verify", "Get-ScheduledTask" in src, True)

    def test_tomorrow_seven(self):
        got = alarm_task.tomorrow_seven(NOW)
        check("kal", got.day, 14)
        check("7 baje", (got.hour, got.minute), (7, 0))

    def test_venv_python_required(self):
        with patch(alarm_task, "PYTHON", Path("D:/nahi/python.exe")):
            got = alarm_task.register("X", datetime.datetime(2026, 10, 14, 7, 0))
        check("bina venv ke task nahi", got.startswith("NAHI BANA"), True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("alarm tool + task" if result.wasSuccessful() else "FAIL")
