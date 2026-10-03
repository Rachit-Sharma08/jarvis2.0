"""Desktop shell ka test — koi asli mic nahi, koi browser nahi, koi registry nahi.

Jo cheezein side effect karti hain (Edge spawn, Run key, tray message loop)
unka **command / path** check hota hai, chalta hua code nahi. Is liye ye
suite har baar tez aur khatarna-free hai.

Baaki hisse alag file me (sab apne aap se chalti hain):
  - `test_desktop_single.py` — single instance + stale PID/lock
  - `test_desktop_guard.py`  — TOOLS auto-off + tray ke bina mat chalo
  - `test_desktop_tray.py`   — tray rang/menu/state/permission
  - `test_wake_worker.py`    — wake worker ka wiring
Ye Step 3a (shell) ka test hai — mic/VAD ka `test_wake.py` me.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import core.modes as modes
from desktophelp import check, finish, show
from desktop import hud_window, launcher

ROOT = Path(__file__).resolve().parent.parent

# Niyam: "koi file 200 lines se badi na ho" — yaani **200 chalega**, 201 nahi.
SOURCE_FILES = ("desktop/app.py", "desktop/launcher.py", "desktop/tray.py",
                "desktop/hud_window.py", "desktop/state.py", "desktop/startup.py",
                "desktop/actions.py", "desktop/single.py", "desktop/playback.py",
                "desktop/open_hud.py", "desktop/hotkey.py", "desktop/shortcut.py",
                "wake/session.py", "wake/utterance.py", "wake/worker.py",
                "wake/command.py", "wake/listen.py",
                "config.py", "config_name.py", "config_tools.py",
                "config_desktop.py", "config_wake.py", "log_setup.py")


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


def test_startup_lines():
    """Startup ke 4 line ek jagah, exact shabd — console + log dono."""
    print("STARTUP LINES")
    for key in ("STARTUP_SERVER", "STARTUP_TRAY", "STARTUP_HUD", "STARTUP_WAKE"):
        check(f"config.{key} hai", hasattr(config, key), True)
    check("server up", config.STARTUP_SERVER, "server up")
    check("tray started", config.STARTUP_TRAY, "tray started")
    check("HUD ready", config.STARTUP_HUD, "HUD ready")
    check("wake", config.STARTUP_WAKE, "wake")

    src = (ROOT / "desktop/app.py").read_text(encoding="utf-8")
    up = (ROOT / "desktop/startup.py").read_text(encoding="utf-8")
    # Sirf app.py bolti hai (ya use helper bulata hai) — line ka shabd ek jagah.
    check("app.py me server up bolta hai", "config.STARTUP_SERVER" in src, True)
    check("app.py me tray bolta hai", "config.STARTUP_TRAY" in src, True)
    check("app.py HUD helper use karta hai", "startup.say_hud(" in src, True)
    check("app.py wake helper use karta hai", "startup.say_wake(" in src, True)
    check("startup.py me HUD shabd", "config.STARTUP_HUD" in up, True)
    check("startup.py me wake shabd", "config.STARTUP_WAKE" in up, True)
    # 'HUD ready' sirf ek jagah — server/app.py duplicate na bole.
    check("server/app.py duplicate log nahi",
          'log.info("HUD ready' in (ROOT / "server/app.py").read_text(encoding="utf-8"),
          False)

    # Console par bhi jaani chahiye, warna user ko crash dikhta hi nahi.
    check("startup.py console par print karta hai",
          "print(line, flush=True)" in up, True)
    lsrc = (ROOT / "desktop/launcher.py").read_text(encoding="utf-8")
    check("launcher crash console par bolta hai", "_console(" in lsrc, True)
    check("launcher child output tee karta hai", "stdout=subprocess.PIPE" in lsrc, True)


def test_log_ascii():
    """Log ASCII — em-dash/Devanagari mojibake (`??`) na bane."""
    print("LOG ASCII")
    from log_setup import ascii_text, get_logger
    check("em-dash -> -", ascii_text("a \u2014 b"), "a - b")
    check("arrow -> ->", ascii_text("x \u2192 y"), "x -> y")
    check("Devanagari hat jaata hai", ascii_text("\u0939\u093f\u0928\u094d\u0926\u0940"), "")
    check("ASCII waisa hi rehta hai", ascii_text("server up: 200"), "server up: 200")

    # Asli logger se ek non-ASCII line likhwa kar file me jaanche.
    probe = "PROBE-\u2014\u2192\u0939\u093f"
    before = config.LOG_FILE.stat().st_size
    get_logger("ascii_probe").error("%s", probe)
    new = config.LOG_FILE.read_bytes()[before:]
    check("logger ne non-ASCII likha hi nahi", [b for b in new if b > 127], [])
    check("par woh message me hai", probe[:6] in new.decode("ascii", "replace"), True)


def test_hygiene():
    print("HYGIENE")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for name in ("data/", "models/", ".cache/", ".tmp/"):
        check(f".gitignore me {name}", name in gitignore, True)
    check("sirf sunday .env.example me",
          "PRABH_SUNDAY_ONLY" in (ROOT / ".env.example").read_text(encoding="utf-8"), True)
    for path in SOURCE_FILES:
        lines = len((ROOT / path).read_text(encoding="utf-8").splitlines())
        check(f"{path} <=200 lines ({lines})", lines <= 200, True)
    # Test file khud bhi badi na ho — is suite ka apna rule (AGENTS.md).
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        lines = len(path.read_text(encoding="utf-8").splitlines())
        check(f"tests/{path.name} <=200 lines ({lines})", lines <= 200, True)


for fn in (test_config, test_hud_window, test_launcher,
           test_startup_lines, test_log_ascii, test_hygiene):
    fn()

finish("Saare desktop shell test pass.")