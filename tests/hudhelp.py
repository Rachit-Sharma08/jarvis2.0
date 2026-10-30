"""HUD window test ke fakes — dono test file inhi se import kare.

`test_desktop_hud_single.py` (ek hi window ka bug) aur
`test_desktop_hud_win.py` (title dhoondhna + edge cases).

Repo ka niyam: asli Edge, asli `taskkill`, mic/STT/brain **kabhi nahi**. Sirf
fakes:

- `FakeDesktop` — asli Edge ki jagah. `finder()` = nakli `find_hud_window()`
  (window dhoondhti hai), `spawner()` = nakli `subprocess.Popen` (window banati
  hai). `invisible_for` se Edge ki "dheere khulne wali" window bhi model hoti
  hai - `tests/test_desktop_hud_win.py` usi ko test karta hai.
- `FakeRun` — `subprocess.run` (taskkill) ka nakli, koi process marte nahi.
- `FakeCommand` — `wake/command.run` ka nakli.
- `make_hud()` / `wake()` — dono asli production call ka shape copy karte hain.
- `patched()` — `bring_front` ko record karne wala fake ke saath jaata hai
  (`tests/test_desktop_hud_single.py` usi se pata lagata hai ki wake usi
  window par le gaya ya naya khol diya).
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import contextlib  # noqa: E402

import config  # noqa: E402
from desktop import hud_window  # noqa: E402
from tests.wakecmdhelp import patch  # noqa: E402

FRONTED = []          # kis hwnd par le gaya (har wake par)


def _front(hwnd):
    FRONTED.append(int(hwnd))
    return True


class FakeProc:
    """`subprocess.Popen` ka nakli - sirf pid (taskkill kabhi nahi chalta)."""

    def __init__(self, desk, pid):
        self.desk = desk
        self.pid = pid

    def poll(self):
        return None


class FakeDesktop:
    """Asli Edge ki jagah. `windows` = abhi khuli HUD windows.

    `invisible_for`: pehle kitni `finder()` call tak window **nahi** dikhegi -
    Edge ko nayi window banane me 1-2 s lagte hain, aur usi der me dobara
    spawn karne se do window ban jaati hain.
    """

    def __init__(self, invisible_for=0):
        self.windows = []
        self.spawns = 0
        self.invisible_for = invisible_for
        self.seen = 0

    def finder(self):
        self.seen += 1
        if self.seen > self.invisible_for and self.windows:
            return self.windows[0]
        return 0

    def spawner(self, cmd):
        self.spawns += 1
        hwnd = 9000 + self.spawns
        self.windows.append(hwnd)
        return FakeProc(self, hwnd)

    def kill(self, pid):
        self.windows = [w for w in self.windows if w != pid]


class FakeRun:
    """`subprocess.run` (taskkill) ka nakli - koi asli process marte nahi."""

    def __init__(self, desk):
        self.desk = desk
        self.killed = []

    def run(self, cmd, **_kw):
        self.killed.append(list(cmd))
        self.desk.kill(int(cmd[-1]))
        return None


class FakeCommand:
    """`wake/command.run` ka nakli - mic/STT/brain kabhi nahi.

    `heard=True` par asli `on_heard` callback bhi chalata hai (jaise asli run
    valid text milne par karta hai), warna HUD kabhi na khulti."""

    def __init__(self, heard=True):
        self.calls = 0
        self.heard = heard

    def run(self, mic, stop, **kw):
        self.calls += 1
        if self.heard:
            (kw.get("on_heard") or (lambda: None))()
        return 1


class FakeApp:
    """`desktop/app.py` jaisa - `on_wake` ko sirf `.hud` chahiye."""

    def __init__(self, hud):
        self.hud = hud


def make_hud(desk):
    """`finder`/`spawner` fake wala HUD.

    `sys.executable` sirf is liye ki `available()` sach me True ho - wo sirf
    `Path(exe).is_file()` dekhti hai. Asli launch to `spawner` se badal chuka
    hai, is liye Edge kabhi nahi chalta."""
    return hud_window.HudWindow(exe=sys.executable, name="Fake Edge",
                                finder=desk.finder, spawner=desk.spawner)


def wake(app, command=None):
    """**Asli** wake raasta - `callbacks.on_wake(phrase, mic, stop, app)`,
    bilkul jaise `SundayApp._on_wake()` bhejta hai. `command` = nakli
    `wake/command.run` (`cb.command` par patch ho jaata hai)."""
    from desktop import callbacks as cb
    if command is None:
        cb.on_wake("jarvis", None, None, app)
        return
    with patch(cb.command, "run", command.run):
        cb.on_wake("jarvis", None, None, app)


@contextlib.contextmanager
def patched():
    """`bring_front` fake + `config.HUD_PROFILE_DIR` temp par.

    Asli `bring_front` sirf screen par laata hai (test me kuch nahi hota),
    aur `_spawn()` `HUD_PROFILE_DIR` banata hai - asli `data/` ko haath nahi
    lage, is liye yahin temp par bhej dete hain (E-1b niyam)."""
    real_front = hud_window.bring_front
    real_profile = config.HUD_PROFILE_DIR
    hud_window.bring_front = _front
    config.HUD_PROFILE_DIR = Path(tempfile.gettempdir()) / "prabh-hud-test-profile"
    FRONTED.clear()
    try:
        yield
    finally:
        hud_window.bring_front = real_front
        config.HUD_PROFILE_DIR = real_profile
