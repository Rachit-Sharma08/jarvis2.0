"""Desktop shell ka test — koi asli mic nahi, koi browser nahi, koi registry nahi.

Jo cheezein side effect karti hain (Edge spawn, Run key, tray message loop)
unka **command / path** check hota hai, chalta hua code nahi. Is liye ye
suite har baar tez aur khatarna-free hai.

Tray/state/permission ka hissa `test_desktop_tray.py` me hai.
Ye Step 3a (shell) ka test hai — wake ka `test_wake.py` me.
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import core.modes as modes
from desktophelp import FAILED, check, finish, show
from desktop import hud_window, launcher, single as single_mod
from gatekeeper.limiter import Limiter
from wake import worker as wake_worker

ROOT = Path(__file__).resolve().parent.parent


def test_config():
    print("CONFIG")
    check("backoff pehla", config.backoff_for(1), 2)
    check("backoff aakhir", config.backoff_for(99), 30)
    check("restart limit", config.RESTART_MAX, 5)
    check("tools auto-off 30 min", config.TOOLS_AUTO_OFF_MINUTES, 30)
    check("exit codes alag", len({config.EXIT_QUIT, config.EXIT_RESTART,
                                  config.EXIT_ALREADY_RUNNING}), 3)
    check("HUD viewport me fit", config.HUD_WIDTH + config.HUD_HEIGHT <= 1366 + 768, True)
    check("SUNDAY_ONLY on", config.SUNDAY_ONLY, True)
    check("sirf sunday", modes.detect_mode("Prabh, kya haal", "sunday"), ("sunday", "kya haal"))
    check("sunday chalta hai", modes.detect_mode("Sunday, kya haal", "sunday")[0], "sunday")


def test_hud_window():
    print("HUD WINDOW (Edge --app, sirf command check)")
    cmd = hud_window.command(r"C:\fake\msedge.exe")
    check("exe pehle", cmd[0], r"C:\fake\msedge.exe")
    check("--app URL", cmd[1].startswith("--app=http://127.0.0.1:8000"), True)
    check("apna profile", any(a.startswith("--user-data-dir=") for a in cmd), True)
    check("size di hui", "--window-size=1200,720" in cmd, True)
    check("first-run band", "--no-first-run" in cmd, True)
    check("url sahi", hud_window.url(), f"{config.SERVER_ORIGIN}/")
    exe, name = config.browser_path()
    check("browser dhoondha ya khali", isinstance(exe, str) and isinstance(name, str), True)
    show(f"browser = {name or 'NAHI MILA'} ({exe or '-'})")
    check("fake exe par khula nahi", hud_window.HudWindow(exe=r"D:\nahi\hai.exe").open(), False)


def test_single_instance():
    print("SINGLE INSTANCE")
    path = config.DATA_DIR / "test.lock"
    if path.exists():
        path.unlink()
    first = single_mod.Single(path).acquire()
    try:
        try:
            single_mod.Single(path).acquire()
            FAILED.append("dusra instance rok nahi paya")
            print("  FAIL dusra instance rok nahi paya")
        except single_mod.AlreadyRunning:
            print("  OK   dusra instance mana kiya")
    finally:
        first.release()
    again = single_mod.Single(path).acquire()
    check("chhodne ke baad dobara mila", again is not None, True)
    again.release()
    path.unlink(missing_ok=True)


def test_launcher():
    print("LAUNCHER (crash restart)")
    check("child wahi python", launcher.child_command()[0], sys.executable)
    check("child desktop.app", launcher.child_command()[2], "desktop.app")
    # next_step pure function hai — asli child kabhi spawn nahi hota
    q, r = config.EXIT_QUIT, config.EXIT_RESTART
    check("quit = supervisor band", launcher.next_step(q, [], 0.0, 600)[0], "exit")
    check("already running = supervisor band",
          launcher.next_step(config.EXIT_ALREADY_RUNNING, [], 0.0, 600)[0], "exit")
    check("tray restart = turant", launcher.next_step(r, [], 0.0, 600)[1], 0)
    act, wait, cr = launcher.next_step(1, [], 0.0, 600)
    check("crash = restart", (act, wait, len(cr)), ("restart", 2, 1))
    act, wait, cr = launcher.next_step(1, cr, 10.0, 600)
    check("dusra crash backoff badha", (act, wait, len(cr)), ("restart", 5, 2))
    act, wait, cr = launcher.next_step(1, cr, 20.0, 600)
    check("teesra crash backoff", (act, wait, len(cr)), ("restart", 10, 3))
    act, _, _ = launcher.next_step(1, cr, 30.0, 600, limit=3)
    check("limit cross = supervisor band", act, "give_up")
    old = [0.0, 1.0]
    act, _, cr = launcher.next_step(1, old, 300.0, 60)
    check("purane crash bhool jate hain", (act, len(cr)), ("restart", 1))
    check("crash list mutate nahi hui", len(old), 2)


def test_tools_auto_off():
    print("TOOLS AUTO-OFF (30 min)")
    limiter = Limiter(enabled=True, auto_off_minutes=0.0004)   # ~24 ms
    check("shuru me ON", limiter.enabled, True)
    check("bache minute", limiter.minutes_left() <= 0.01, True)
    time.sleep(0.05)
    check("30 min baad OFF", limiter.enabled, False)
    check("OFF par 0 minute", limiter.minutes_left(), 0.0)
    limiter.set_enabled(True)
    check("dobara ON", limiter.enabled, True)
    check("timer dobara chala", Limiter(enabled=True, auto_off_minutes=5).minutes_left() > 0, True)
    check("check() OFF par rokta hai", Limiter(enabled=False).check() != "", True)
    forever = Limiter(enabled=True, auto_off_minutes=0)     # 0 = auto-off band
    time.sleep(0.02)
    check("0 minute = kabhi OFF nahi", forever.enabled, True)


def test_wake_stub():
    print("WAKE STUB (Step 3a)")
    check("start abhi nahi chalta", wake_worker.start(), False)
    check("state off", wake_worker.state(), "off")
    check("wake chalu nahi", wake_worker.READY, False)


def test_hygiene():
    print("HYGIENE")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for name in ("data/", "models/", ".cache/", ".tmp/"):
        check(f".gitignore me {name}", name in gitignore, True)
    check("sirf sunday .env.example me",
          "PRABH_SUNDAY_ONLY" in (ROOT / ".env.example").read_text(encoding="utf-8"), True)
    for path in ("desktop/app.py", "desktop/launcher.py", "desktop/tray.py",
                 "desktop/hud_window.py", "desktop/state.py", "config_desktop.py"):
        lines = len((ROOT / path).read_text(encoding="utf-8").splitlines())
        check(f"{path} <200 lines ({lines})", lines < 200, True)


for fn in (test_config, test_hud_window, test_single_instance, test_launcher,
           test_tools_auto_off, test_wake_stub, test_hygiene):
    fn()

finish("Saare desktop shell test pass.")