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
from server import hud_reminders  # noqa: E402
from tests.datasafe import isolated_data  # noqa: E402
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
    loop = app_loop.AppLoop()
    loop._fire_reminders()
    check("bola", spoken, ["Sir, reminder: paani piyo"])
    check("HUD update", len(sent), 1)
    loop._fire_reminders()
    check("dobara nahi bola", spoken, ["Sir, reminder: paani piyo"])


def test_ids_not_reused():
    print("ID: clear ke baad wahi id dobara nahi")
    check("pehla #1", reminders.add_reminder("a", in_minutes=5).startswith("Reminder set #1"), True)
    check("doosra #2", reminders.add_reminder("b", in_minutes=5).startswith("Reminder set #2"), True)
    reminders.clear_reminder(1)
    check("teesra #3 (id reuse nahi)", reminders.add_reminder("c", in_minutes=5).startswith("Reminder set #3"), True)


for fn in (test_add_and_due, test_due_and_mark, test_fire_once, test_ids_not_reused):
    with isolated_data():
        fn()

if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
