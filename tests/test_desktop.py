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


def test_wake_worker():
    """Wake worker (Step 1) ka wiring — **asli mic kabhi nahi** khulta.

    `start()` asli chalta to model load + mic khul jaata, is liye yahan
    `wake/session.py` ke do cheez (model build + `MicSource`) fake se badal
    kar sirf wiring check hota hai. Loop ka poora test `test_wake_loop.py`.
    """
    print("WAKE WORKER (Step 1)")
    from wake import session as session_mod
    from wakehelp import FakeListener, FakeMic

    check("READY ab True hai", wake_worker.READY, True)
    check("state shuru me off", wake_worker.state(), "off")
    for name in ("start", "stop", "state", "listening", "set_paused", "wakes"):
        check(f"worker.{name} hai", callable(getattr(wake_worker, name, None)), True)

    saved = (session_mod.detect.build, session_mod.audio_mod.MicSource)
    mic = FakeMic()
    session_mod.detect.build = lambda: FakeListener()
    session_mod.audio_mod.MicSource = lambda: mic
    try:
        check("start True", wake_worker.start(), True)
        check("state listening", wake_worker.state(), "listening")
        check("wake shabd config me", config.WAKE_WORDS, ("sunday",))
        wake_worker.set_paused(True)
        wake_worker.set_paused(False)
    finally:
        wake_worker.stop()
        session_mod.detect.build, session_mod.audio_mod.MicSource = saved
    check("stop ke baad off", wake_worker.state(), "off")


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
          "print(line, flush=True)" in (ROOT / "desktop/startup.py").read_text(encoding="utf-8"),
          True)
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


def test_stale_lock_diagnose():
    """"pehle se chal raha hai" sirf tab bolna hai jab PID zinda ho aur GET /
    200 de. Warna message stale/atka hona chahiye — dono probe daal kar test
    hota hai, asli process ya socket nahi chhua jaata."""
    print("STALE LOCK DIAGNOSE")
    import tempfile
    from desktop.single import Single, http_alive, pid_alive

    # Ek hi temp dir poore test tak — `fake_single()` me `with` block khatam hote
    # hi file mita di jaati, to `owner_pid()` 0 milta aur test galat fail hota.
    holder = tempfile.TemporaryDirectory()

    def fake_single(pid_text, name="a"):
        lock = Path(holder.name) / ("prabh-%s.lock" % name)
        lock.write_bytes(b"0")
        s = Single(lock)
        s.pid_path.write_text(pid_text, encoding="utf-8")
        return s

    # --- pid_alive / http_alive ke chhote helper ---
    check("pid 0 marda hai", pid_alive(0), False)
    check("pid -1 marda hai", pid_alive(-1), False)
    check("probe se zinda", pid_alive(5, probe=lambda p: p == 5), True)
    check("probe se murda", pid_alive(5, probe=lambda p: False), False)

    class Ok:
        status = 200

        def __enter__(self): return self

        def __exit__(self, *a): return False
    check("http 200 = zinda", http_alive("http://x", opener=lambda u, timeout=0: Ok()), True)

    def boom(u, timeout=0): raise OSError("refused")
    check("http fail = murda", http_alive("http://x", opener=boom), False)

    class Bad:
        status = 503

        def __enter__(self): return self

        def __exit__(self, *a): return False
    check("http 503 = murda",
          http_alive("http://x", opener=lambda u, timeout=0: Bad()), False)

    # --- 4 asli combinations ---
    alive = lambda p: True
    dead = lambda p: False
    good = lambda *a, **k: Ok()          # HTTP 200 de raha hai
    bad = lambda *a, **k: boom("")       # HTTP jawab nahi de raha

    msg = fake_single("123\n").diagnose(alive, good)
    check("zinda + 200 -> CHAL raha hai", "CHAL raha hai" in msg, True)
    check("  PID bataya", "pid=123" in msg, True)

    msg = fake_single("123\n").diagnose(alive, bad)
    check("zinda par HUD nahi -> atka", "atki hai" in msg, True)
    check("  'stale' nahi bola", "stale" in msg, False)

    msg = fake_single("123\n").diagnose(dead, good)
    check("PID murda + port kisi ka", "port 8000" in msg, True)

    msg = fake_single("123\n").diagnose(dead, bad)
    check("dono dead -> stale", "stale" in msg, True)

    msg = fake_single("").diagnose(dead, bad)
    check("PID file hi nahi -> stale", "stale" in msg, True)
    check("  koi 'pehle se' nahi", "pehle se CHAL" in msg, False)


def test_stale_pid_self_heal():
    """Asli stale PID file: mar ke baad bacha hua `.pid`. Lock milne ke baad
    apne aap hat jaana chahiye warna user ko hamesha 'pehle se chal raha hai'
    dikhta rahega. Test apne temp dir me hai - asli `data/` chhua nahi jaata."""
    print("STALE PID SELF-HEAL")
    import os
    import tempfile

    from desktop.single import Single

    # 99999999 ka koi process nahi hota - safe "marda" PID.
    dead_pid = 99999999
    tmp = tempfile.TemporaryDirectory()
    lock = Path(tmp.name) / "prabh.lock"
    lock.write_bytes(b"0")
    s = Single(lock)
    s.pid_path.write_text("%d\n" % dead_pid, encoding="utf-8")
    check("shuru me purana PID pada hai", s.owner_pid(), dead_pid)

    s.acquire()                      # koi live process nahi -> lock mil jayegi
    check("lock mili", s.owner_pid(), os.getpid())
    check("purana PID hat gaya", str(dead_pid) in s.pid_path.read_text("utf-8"), False)

    # ab jab lock HELD hai, doosra instance ko saaf message milna chahiye
    other = Single(lock)
    try:
        other.acquire()
        check("doosra instance lock nahi pakad paaya", False, True)
    except Exception as exc:
        msg = str(exc)
        check("doosre ko 'stale' nahi bola", "stale" in msg, False)
        check("doosre ko 'CHAL raha hai' bola", "CHAL raha hai" in msg, True)
        check("  apna PID bataya", "pid=%d" % os.getpid() in msg, True)
    finally:
        s.release()
    check("release ke baad doosra lock pakad paata hai",
          other.acquire() is other, True)
    other.release()
    tmp.cleanup()


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


def test_hygiene():
    print("HYGIENE")
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for name in ("data/", "models/", ".cache/", ".tmp/"):
        check(f".gitignore me {name}", name in gitignore, True)
    check("sirf sunday .env.example me",
          "PRABH_SUNDAY_ONLY" in (ROOT / ".env.example").read_text(encoding="utf-8"), True)
    for path in ("desktop/app.py", "desktop/launcher.py", "desktop/tray.py",
                 "desktop/hud_window.py", "desktop/state.py",
                 "desktop/startup.py", "desktop/actions.py",
                 "desktop/single.py", "config_desktop.py", "log_setup.py"):
        lines = len((ROOT / path).read_text(encoding="utf-8").splitlines())
        check(f"{path} <200 lines ({lines})", lines < 200, True)


for fn in (test_config, test_hud_window, test_single_instance, test_launcher,
           test_tools_auto_off, test_wake_worker, test_startup_lines,
           test_log_ascii, test_stale_lock_diagnose, test_stale_pid_self_heal,
           test_tray_guard, test_hygiene):
    fn()

finish("Saare desktop shell test pass.")