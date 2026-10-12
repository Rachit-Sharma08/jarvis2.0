"""HUD window ke edge cases — title dhoondhna aur Edge ki der/sudhaar.

`tests/test_desktop_hud_single.py` ka saathi (wo "ek hi window" wala bug
pakda hai). Yahan teen baatein:

1. `desktop/win_find.py` ka `is_hud_title()` — **pure**, browser ke bina.
   User ka apna tab ("Jarvis - Wikipedia") galat se pakad na le, is liye
   sirf 'Jarvis' se kaam chalana sahi nahi.
2. Edge **dheere** khulta hai (1-2 s) — usi der me dobara spawn karne se do
   window banti hain. `SPAWN_GRACE_SECONDS` isi ke liye hai.
3. Edge **mar gaya** to app chup nahi baith jaani chahiye - grace ki hadd ke
   baad dobara koshish hogi.

Fakes `tests/hudhelp.py` me hain. Asli Edge/taskkill kabhi nahi.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from desktophelp import check, finish
from desktop import hud_window, win_find
from tests.hudhelp import FakeDesktop, FakeRun, make_hud, patched
from tests.wakecmdhelp import patch


def test_title_match():
    print("TITLE MATCH (pure - browser ke bina)")
    check("page ka title", win_find.hud_title(), f"{config.ASSISTANT_NAME} HUD")
    check("HUD ki window", win_find.is_hud_title(win_find.hud_title()), True)
    check("URL wala title (page load ho raha)",
          win_find.is_hud_title(f"{win_find.hud_url()} - Jarvis"), True)
    check("display naam", win_find.is_hud_title(config.DISPLAY_NAME), True)
    check("khaali title", win_find.is_hud_title(""), False)
    check("None", win_find.is_hud_title(None), False)
    check("Chrome ki doosri window",
          win_find.is_hud_title("Study material - Google Chrome"), False)
    check("Brave tab", win_find.is_hud_title("Samjhawan - YouTube - Brave"), False)
    check("sirf naam wala user tab nahi pakda",
          win_find.is_hud_title("Jarvis - Wikipedia"), False)
    check("url aur title ek hi jagah se", win_find.hud_url(), hud_window.url())


def test_empty_window_title():
    print("KHALI TITLE (Edge ke chhupne wale windows)")
    check("0 ka hwnd", win_find.window_text(0), "")
    check("koi hwnd nahi diya", win_find.still_open(0), 0)


def test_slow_browser():
    print("EDGE DHEERE (window abhi bani hi nahi)")
    desk = FakeDesktop(invisible_for=2)
    hud = make_hud(desk)
    with patched():
        for _ in range(3):
            hud.open()
        check("teeno wake par ek hi spawn", desk.spawns, 1)
        check("window ban gayi to pakad bhi gayi", hud.focus_existing(), True)


def test_grace_expires():
    """Intezaar ki hadd - Edge mar gaya to app chup nahi baith jaani chahiye."""
    print("EDGE MAR GAYA (intezaar ki hadd)")
    desk = FakeDesktop(invisible_for=10 ** 6)      # kabhi nahi dikhegi
    hud = make_hud(desk)
    with patched():
        hud.open()
        hud.open()
        check("abhi-hi bane window ka intezaar", desk.spawns, 1)
        hud._spawned_at -= hud_window.SPAWN_GRACE_SECONDS + 1
        hud.open()
        check("hadd ke baad dobara koshish", desk.spawns, 2)


def test_grace_not_left_stale():
    """`focus_existing()` ne window pakad li to intezaar saaf hona chahiye -
    warna band karke dobara kholne par intezaar ki wajah se nahi khulega."""
    print("GRACE SAaf HONA")
    desk = FakeDesktop()
    hud = make_hud(desk)
    with patched():
        hud.open()
        truthy_before = hud._opening()
        hud.focus_existing()
        check("window milne par ab intezaar nahi", hud._opening(), False)
        check("pehle haal bhi sach hota tha", truthy_before, True)


def test_close_then_open():
    print("BAND KARNE KE BAAD DOBARA")
    desk = FakeDesktop()
    hud = make_hud(desk)
    fake_sub = FakeRun(desk)
    with patched():
        hud.open()
        with patch(hud_window, "subprocess", fake_sub):
            check("band hua", hud.close(), True)
        check("taskkill sirf record hua (asli process nahi mara)",
              len(fake_sub.killed), 1)
        check("window list khali", desk.windows, [])
        check("dobara close = kuch nahi", hud.close(), False)
        hud.open()
        check("band karne ke baad naya khol sakta hai", desk.spawns, 2)


def test_no_browser():
    print("BROWSER HI NAHI")
    hud = hud_window.HudWindow(exe=r"D:\nahi\hai.exe")
    check("available() False", hud.available(), False)
    check("open() khud band khade", hud.open(), False)


def test_grace_seconds_sane():
    """Hadd Edge se badi honi chahiye (window 1-2 s me banti hai) aur chhoti
    bhi - warna ya to dubara window banegi ya app chup ho jayegi."""
    print("GRACE KI HADD")
    check("1 s se badi", hud_window.SPAWN_GRACE_SECONDS > 1.0, True)
    check("30 s se chhoti", hud_window.SPAWN_GRACE_SECONDS < 30.0, True)


for fn in (test_title_match, test_empty_window_title, test_slow_browser,
           test_grace_expires, test_grace_not_left_stale, test_close_then_open,
           test_no_browser, test_grace_seconds_sane):
    fn()

finish("HUD window ke edge cases pass.")
