"""REGRESSION (R-2, 13-Oct): har "Jarvis" par nayi HUD window khulti thi.

Asli wajah: `desktop/hud_window.py` me `_focus_existing()` `EnumWindows` se
window dhoondta tha, par uske aakhir me `return False` likha tha - matlab
"window mili" ka faisla **lapiset** ho jaata tha. `open()` is liye har baar
naya browser chala deta tha. 4 wake = 4 window (taskbar me bhi 4).

Ye test **asli Edge, mic, STT ya brain kabhi nahi** chalaata - fakes
`tests/hudhelp.py` me hain. Wake **asli** raaste se aata hai:
`desktop/callbacks.on_wake()`, jaise app me `SundayApp._on_wake()` bhejta
hai. Sirf `wake/command.run` nakli hai (wo HUD wale hisse ko chhoo nahi
chuta), is liye test sach me batata hai ki **wake kitni baar aayi**.

Baaki hissa (`tests/test_desktop_hud_win.py`): title ka pakadna aur
Edge ke edge cases.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from desktophelp import check, finish
from tests.hudhelp import (FRONTED, FakeApp, FakeCommand, FakeDesktop,
                           make_hud, patched, wake)

WAKE_TIMES = 10          # task: 10 wake par sirf 1 window


def test_ten_wakes_one_window():
    print(f"ASLI WAKE x{WAKE_TIMES} -> sirf 1 window")
    desk = FakeDesktop()
    app = FakeApp(make_hud(desk))
    ran = FakeCommand()
    with patched():
        for _ in range(WAKE_TIMES):
            wake(app, ran)
        check(f"{WAKE_TIMES} wake ka command sach me chala", ran.calls, WAKE_TIMES)
        check("sirf EK window bani", len(desk.windows), 1)
        check("browser sirf 1 hi baar chala", desk.spawns, 1)
        check("baaki 9 wake usi window par le gaye",
              FRONTED.count(desk.windows[0]), WAKE_TIMES - 1)


def test_old_bug_cannot_come_back():
    """Jis line se bug tha wahi jaan-boojh check: window mili to **True**."""
    print("PURANA BUG (focus_existing hamesha False deta tha)")
    desk = FakeDesktop()
    hud = make_hud(desk)
    with patched():
        hud.open()
        check("pehli baar khuli", len(desk.windows), 1)
        check("window khuli hai par focus_existing = True", hud.focus_existing(), True)
        check("focus ke baad bhi 1 hi window", len(desk.windows), 1)
        check("browser dobara nahi chala", desk.spawns, 1)
        check("is_open() bhi sach bolta hai", hud.is_open(), True)


def test_other_process():
    """Desktop shortcut / tray `desktop/open_hud.py` **alag process** se
    chalta hai aur naya `HudWindow` banata hai (koi purana yaad nahi, `_hwnd`
    0). Tab bhi nayi window nahi bani - yahi sabse pakka test hai, kyunki
    isme koi grace/intezaar bhi madad nahi karta."""
    print("ALAG PROCESS (shortcut / open_hud.py)")
    desk = FakeDesktop()
    with patched():
        make_hud(desk).open()
        other = make_hud(desk)
        check("doosre process ne khola ya focus kiya", other.open(), True)
        check("windows ab bhi 1", len(desk.windows), 1)
        check("browser 1 hi baar chala", desk.spawns, 1)


def test_hotkey_same_window():
    """Ctrl+Alt+S bhi wahi raasta hai (`callbacks.on_hotkey`) - alag window
    nahi, warna shortcut + wake mil kar 2 window bana dete."""
    print("HOTKEY (Ctrl+Alt+S)")
    from desktop import callbacks as cb
    desk = FakeDesktop()
    app = FakeApp(make_hud(desk))
    with patched():
        app.hud.open()
        cb.on_hotkey(app)
        check("windows ab bhi 1", len(desk.windows), 1)
        check("browser 1 hi baar chala", desk.spawns, 1)


with patched():
    for fn in (test_ten_wakes_one_window, test_old_bug_cannot_come_back,
               test_other_process, test_hotkey_same_window):
        fn()

finish("HUD ek hi window - 10 wake par bhi sirf 1.")
