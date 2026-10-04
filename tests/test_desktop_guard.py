"""App ke do "ruk jaao" pakkaure — TOOLS auto-off aur tray ke bina mat chalo.

Dono ka faisla **pure function** hai, is liye test me na tray message loop
chalti hai na pystray. Shell ka baaki hissa `test_desktop.py` me.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from desktophelp import check, finish
from gatekeeper.limiter import Limiter

ROOT = Path(__file__).resolve().parent.parent


def test_tools_auto_off():
    print("TOOLS AUTO-OFF (30 min)")
    limiter = Limiter(enabled=True, auto_off_minutes=0.0004)   # ~24 ms
    seen = []
    limiter.set_on_change(seen.append)          # desktop tray ka hook
    check("shuru me ON", limiter.enabled, True)
    check("bache minute", limiter.minutes_left() <= 0.01, True)
    time.sleep(0.05)
    check("30 min baad OFF", limiter.enabled, False)
    check("OFF par 0 minute", limiter.minutes_left(), 0.0)
    check("auto-off ne hook ko bataya", seen, [False])
    limiter.set_enabled(True)
    check("dobara ON", limiter.enabled, True)
    check("hook ON bhi mila", seen[-1], True)
    check("same value par hook nahi", (limiter.set_enabled(True), len(seen))[1], 2)
    check("timer dobara chala", Limiter(enabled=True, auto_off_minutes=5).minutes_left() > 0, True)
    check("check() OFF par rokta hai", Limiter(enabled=False).check() != "", True)
    forever = Limiter(enabled=True, auto_off_minutes=0)     # 0 = auto-off band
    time.sleep(0.02)
    check("0 minute = kabhi OFF nahi", forever.enabled, True)
    # Hook crash kare to gatekeeper na fute
    boom = Limiter(enabled=False)
    boom.set_on_change(lambda on: (_ for _ in ()).throw(RuntimeError("hook crash")))
    boom.set_enabled(True)
    print("  OK   crash-safe hook")


def test_tray_guard():
    """Bina tray ke app na chalta rahe — 3 koshish, phir saaf exit."""
    print("TRAY GUARD")
    from desktop.tray import retry_start

    check("EXIT_NO_TRAY alag code hai", config.EXIT_NO_TRAY, 4)
    check("EXIT_NO_TRAY 0/3/20 se alag hai",
          config.EXIT_NO_TRAY in (0, 3, config.EXIT_RESTART), False)
    check("TRAY_START_ATTEMPTS = 3", config.TRAY_START_ATTEMPTS, 3)

    # retry_start alag function hai — asli pystray chalu kiye bina test hota hai.
    tries, waits = [], []

    class StubTray:
        def __init__(self, succeed_at=None):
            self.succeed_at = succeed_at

        def start(self):
            tries.append(1)
            return self.succeed_at is not None and len(tries) >= self.succeed_at

    check("3 koshish ke baad bhi fail",
          retry_start(StubTray(), 3, 1.5, sleep=waits.append), False)
    check("  3 hi koshish", len(tries), 3)
    check("  beech me 2 baar ruka", waits, [1.5, 1.5])

    tries.clear()
    check("2nd koshish me ban gaya",
          retry_start(StubTray(2), 3, 0, sleep=waits.append), True)
    check("  2 hi koshish", len(tries), 2)

    tries.clear()
    check("pehli hi me ban jaye to 1 koshish",
          retry_start(StubTray(1), 3, 0, sleep=waits.append), True)
    check("  1 koshish", len(tries), 1)

    src = (ROOT / "desktop/app.py").read_text(encoding="utf-8")
    check("app start_retry use karta hai", "start_retry(" in src, True)
    check("app EXIT_NO_TRAY se band karta hai", "EXIT_NO_TRAY" in src, True)
    check("app AlreadyRunning ka message console par bolta hai",
          "print(str(exc), flush=True)" in src, True)
    lsrc = (ROOT / "desktop/launcher.py").read_text(encoding="utf-8")
    check("launcher tray-wajah bhi bolta hai", "EXIT_NO_TRAY" in lsrc, True)


def test_tools_default_on_forever():
    """User ka faisla (4-Oct): app start hote hi TOOLS ON, aur **kabhi** apne aap
    OFF na ho. Pehle default OFF + 30 min auto-off tha."""
    print("TOOLS default ON + auto-off band")
    check("config default ON", config.TOOLS_ENABLED_DEFAULT, True)
    check("config auto-off 0", config.TOOLS_AUTO_OFF_MINUTES, 0)
    real = Limiter()                      # koi argument nahi = asli config
    check("bina kuch kiye ON", real.enabled, True)
    time.sleep(0.02)
    check("timer par OFF nahi", real.enabled, True)
    check("minutes_left 0 (koi timer nahi)", real.minutes_left(), 0.0)
    check("check() chalega", real.check(), "")


for fn in (test_tools_auto_off, test_tools_default_on_forever, test_tray_guard):
    fn()

finish("Saare desktop guard test pass.")