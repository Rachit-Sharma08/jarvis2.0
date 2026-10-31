"""Reminders: dena, bajna (due), ek hi baar bolna, id reuse nahi.

`when` nikalne wala reminder `due()` me aata hai, `mark_done()` ke baad nahi,
aur `_fire_reminders()` use ek hi baar bolta hai (speaker + thread fake).
Asli `data/` kabhi nahi chhoota — `isolated_data()` sab path tmp par daalta hai.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from desktop import app_loop  # noqa: E402
import config_lines  # noqa: E402
from server import hud_reminders  # noqa: E402
from tests.datasafe import isolated_data  # noqa: E402
from brain import prompt  # noqa: E402
import tools  # noqa: E402
from tools import reminders  # noqa: E402

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def past(text="doodh lana", minutes=5):
    """Ek reminder jo `minutes` pehle ka tha (file me seedha likh ke)."""
    when = (datetime.now() - timedelta(minutes=minutes)).isoformat()
    reminders.RFILE.write_text(
        json.dumps([{"id": 9, "text": text, "when": when, "done": False}]),
        encoding="utf-8")


class FakeThread:
    """Thread ki jagah seedha chala do — warna test race karega."""

    def __init__(self, target=None, args=(), daemon=None):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


def test_add_and_due():
    print("ADD: 1 minute baad wala abhi due nahi")
    check("set hua", reminders.add_reminder("call home", in_minutes=1).startswith("Reminder set #1"), True)
    check("abhi due nahi", reminders.due(), [])


def test_due_and_mark():
    print("DUE: nikal chuka reminder bajta hai, phir dobara nahi")
    past()
    got = reminders.due()
    check("due me aaya", [x["id"] for x in got], [9])
    check("HUD par overdue m=0", [x["m"] for x in hud_reminders.due_soon()], [0])
    check("done hua", reminders.mark_done([9]), 1)
    check("due khaali", reminders.due(), [])
    check("done dobara count nahi", reminders.mark_done([9]), 0)
    check("pending list me nahi", reminders.list_reminders(), "Koi pending reminder nahi hai")


def test_fire_once():
    print("FIRE: _fire_reminders ek hi baar bolta hai")
    past("paani piyo")
    spoken, sent = [], []
    app_loop.threading.Thread = FakeThread
    app_loop.playback.say = lambda line, mode=None, rate=None: spoken.append(line)
    app_loop.hud_reminders.broadcast = lambda: sent.append(1)
    app_loop.config.quiet_now = lambda: False   # test apni ghadi par nahi
    loop = app_loop.AppLoop()
    loop._fire_reminders()
    check("bola", spoken, ["Sir, reminder: paani piyo"])
    check("HUD update", len(sent), 1)
    loop._fire_reminders()
    check("dobara nahi bola", spoken, ["Sir, reminder: paani piyo"])


def test_quiet_hours():
    print("QUIET: raat me reminder chup, subah bolega")
    past("raat ka kaam")
    spoken, sent = [], []
    app_loop.playback.say = lambda line, mode=None, rate=None: spoken.append(line)
    app_loop.hud_reminders.broadcast = lambda: sent.append(1)
    app_loop.config.quiet_now = lambda: True
    loop = app_loop.AppLoop()
    loop._fire_reminders()
    check("raat me chup", spoken, [])
    check("pending rehta hai (HUD m=0)", [x["m"] for x in hud_reminders.due_soon()], [0])
    app_loop.config.quiet_now = lambda: False
    loop._fire_reminders()
    check("subah bola", spoken, ["Sir, reminder: raat ka kaam"])
    check("ab done", reminders.due(), [])


def test_quiet_math():
    print("QUIET MATH: 23-7 window")
    config_lines.QUIET_HOURS = (23, 7)
    check("22:59 khula", config_lines.quiet_now(datetime(2026, 1, 1, 22, 59)), False)
    check("23:00 quiet", config_lines.quiet_now(datetime(2026, 1, 1, 23, 0)), True)
    check("03:00 quiet", config_lines.quiet_now(datetime(2026, 1, 1, 3, 0)), True)
    check("06:59 quiet", config_lines.quiet_now(datetime(2026, 1, 1, 6, 59)), True)
    check("07:00 khula", config_lines.quiet_now(datetime(2026, 1, 1, 7, 0)), False)
    config_lines.QUIET_HOURS = (9, 17)
    check("din wali window bhi", config_lines.quiet_now(datetime(2026, 1, 1, 12, 0)), True)
    config_lines.QUIET_HOURS = (0, 0)
    check("0-0 = kabhi quiet nahi", config_lines.quiet_now(datetime(2026, 1, 1, 3, 0)), False)
    config_lines.QUIET_HOURS = (23, 7)


def test_ids_not_reused():
    print("ID: clear ke baad wahi id dobara nahi")
    check("pehla #1", reminders.add_reminder("a", in_minutes=5).startswith("Reminder set #1"), True)
    check("doosra #2", reminders.add_reminder("b", in_minutes=5).startswith("Reminder set #2"), True)
    reminders.clear_reminder(1)
    check("teesra #3 (id reuse nahi)", reminders.add_reminder("c", in_minutes=5).startswith("Reminder set #3"), True)


def test_llm_optional_args():
    print("ARGS: model sirf text+at bheje to bhi chalna chahiye (31-Oct live bug)")
    kind, payload = prompt.parse_action(
        '{"action": "add_reminder", "args": {"text": "call home", "at": "9:00"}}')
    check("parse hua", kind, "tool")
    check("tool chala", tools.execute(*payload).startswith("Reminder set #1"), True)


for fn in (test_add_and_due, test_due_and_mark, test_fire_once, test_quiet_hours,
           test_quiet_math, test_ids_not_reused, test_llm_optional_args):
    with isolated_data():
        fn()

if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
