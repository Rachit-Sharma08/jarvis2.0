"""Single instance + stale PID/lock — koi asli process ya socket nahi chhua jaata.

`"pehle se chal raha hai"` ka message **sirf** tab sahi hai jab PID zinda ho
aur `GET /` 200 de. Wohi rule yahan fake probe se check hota hai.

Ye Step 3a ka test hai — shell ka baaki hissa `test_desktop.py` me, tray ka
`test_desktop_tray.py` me.
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from desktophelp import FAILED, check, finish
from desktop import single as single_mod
from desktop.single import Single, http_alive, pid_alive


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


def boom(u, timeout=0):
    """HTTP jawab nahi de raha — `OSError`, jaise connection refused."""
    raise OSError("refused")


class Ok:
    """HTTP 200 de raha hai (context manager bhi)."""
    status = 200

    def __enter__(self): return self

    def __exit__(self, *a): return False


class Bad:
    """Server zinda hai par 503 de raha hai."""
    status = 503

    def __enter__(self): return self

    def __exit__(self, *a): return False


def test_probe_helpers():
    """`pid_alive` / `http_alive` — dono probe injectable, koi asli I/O nahi."""
    print("PID + HTTP PROBE")
    check("pid 0 marda hai", pid_alive(0), False)
    check("pid -1 marda hai", pid_alive(-1), False)
    check("probe se zinda", pid_alive(5, probe=lambda p: p == 5), True)
    check("probe se murda", pid_alive(5, probe=lambda p: False), False)

    check("http 200 = zinda", http_alive("http://x", opener=lambda u, timeout=0: Ok()), True)
    check("http fail = murda", http_alive("http://x", opener=boom), False)
    check("http 503 = murda",
          http_alive("http://x", opener=lambda u, timeout=0: Bad()), False)


def test_stale_lock_diagnose():
    """Char asli combinations — dono probe daal kar test hota hai."""
    print("STALE LOCK DIAGNOSE")
    # Ek hi temp dir poore test tak — `fake_single()` me `with` block khatam hote
    # hi file mita di jaati, to `owner_pid()` 0 milta aur test galat fail hota.
    holder = tempfile.TemporaryDirectory()

    def fake_single(pid_text, name="a"):
        lock = Path(holder.name) / ("prabh-%s.lock" % name)
        lock.write_bytes(b"0")
        s = Single(lock)
        s.pid_path.write_text(pid_text, encoding="utf-8")
        return s

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
    holder.cleanup()


def test_stale_pid_self_heal():
    """Stale PID file: mar ke baad bacha `.pid` lock milte hi hat jaana chahiye.

    Warna user ko hamesha `"pehle se chal raha hai"` dikhta rahega. Test apne
    temp dir me hai — asli `data/` chhua nahi jaata.
    """
    print("STALE PID SELF-HEAL")
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

    # ab jab lock HELD hai, doosra instance ko saaf message milna chahiye.
    # `acquire()` andar se `diagnose()` call karta hai - asli `http_alive`
    # chalega, is liye message ka **shabd nahi**, guarantee hui baat check karo:
    # live process lock pakde hai to "stale" **kabhi** nahi bola jaata. (Pehle
    # yahan "CHAL raha hai" check tha, jo sirf tab pass hota jab app ka asli
    # server 8000 par chala ho - yani test **environment** par depend karta tha,
    # jabki is file ka apna vaada hai "koi asli process ya socket nahi".)
    other = Single(lock)
    try:
        other.acquire()
        check("doosra instance lock nahi pakad paaya", False, True)
    except Exception as exc:
        msg = str(exc)
        check("doosre ko 'stale' nahi bola", "stale" in msg, False)
        check("  apna PID bataya", "pid=%d" % os.getpid() in msg, True)
    finally:
        s.release()
    check("release ke baad doosra lock pakad paata hai",
          other.acquire() is other, True)
    other.release()
    tmp.cleanup()


for fn in (test_single_instance, test_probe_helpers, test_stale_lock_diagnose,
           test_stale_pid_self_heal):
    fn()

finish("Saare single instance test pass.")