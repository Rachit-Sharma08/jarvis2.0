"""Single instance — ek hi app.

Do baar `start_jarvis.bat` chala do to dono baar mic aur port 8000 ek saath
kholne ki koshish karenge. Is liye ek lock file pakdi jati hai.

Kaam Windows ka apna `msvcrt.locking` karta hai — iska fayda: lock file
process ke saath hi khatam hoti hai. Agar app crash ho gayi ya `taskkill`
kiya gaya to lock apne aap chhoot jaati hai, is liye mar ke baad dobara
chalao to bhi chalega.

"Pehle se chal raha hai" **sirf sach me** bolna hai — is liye lock fail hone
par `diagnose()` check karta hai ki (1) `.pid` wala process abhi zinda hai aur
(2) `GET /` 200 deta hai. Dono na mile to message "stale lock" bolta hai, taaki
user ghalat na samjhe. File ka content (PID) sirf report ke liye hai — chalu
hone ka faisla lock se hota hai, PID se nahi.
"""

import msvcrt
import os
from pathlib import Path

import config
from log_setup import get_logger

log = get_logger("single")

# PROCESS_QUERY_LIMITED_INFORMATION — sirf pata karna, process par koi asar nahi.
_PROC_QUERY = 0x1000


def pid_alive(pid: int, probe=None) -> bool:
    """Kya ye PID abhi zinda hai?

    Windows par `os.kill(pid, 0)` **KHATRA** hai — CPython usay
    `TerminateProcess` me badal deta hai, matlab process maar dega. Is liye
    `OpenProcess` se sirf haath pakda aur chhod diya.
    """
    if pid <= 0:
        return False
    if probe is not None:
        return bool(probe(pid))
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except OSError:
            return False
        return True
    import ctypes
    handle = ctypes.windll.kernel32.OpenProcess(_PROC_QUERY, False, int(pid))
    if not handle:
        return False
    ctypes.windll.kernel32.CloseHandle(handle)
    return True


def http_alive(origin: str, timeout: float = 2.0, opener=None) -> bool:
    """`GET /` 200 deta hai? Test me `opener` daal do — asli socket nahi khulega."""
    import urllib.request
    op = opener or urllib.request.urlopen
    try:
        with op(origin + "/", timeout=timeout) as res:
            return getattr(res, "status", 200) == 200
    except Exception:
        return False


class AlreadyRunning(Exception):
    """Lock dusre process ne pakdi hui hai — ye instance nahi chalega."""


class Single:
    """Lock file khol kar pakad lo. `with` ya `release()` se chhod do."""

    def __init__(self, path: Path = None):
        self.path = Path(path or config.LOCK_FILE)
        self.pid_path = self.path.with_suffix(".pid")
        self._handle = None

    def acquire(self) -> "Single":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(self.path, "a+b")
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:          # khali file par lock nahi lagta
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            handle.close()
            raise AlreadyRunning(self.diagnose())
        self._handle = handle
        self._clean_stale_pid()
        self._write_pid(os.getpid())
        log.info("single instance lock pakdi: %s", self.path)
        return self

    def release(self) -> None:
        if self._handle is None:
            return
        try:
            self._handle.seek(0)
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError as exc:
            log.warning("lock chhodne me dikkat: %s", exc)
        finally:
            self._handle.close()
            self._handle = None
            self.pid_path.unlink(missing_ok=True)
            log.info("single instance lock chhodi")

    def owner_pid(self) -> int:
        """PID alag `.pid` file me hai. Lock wali file ka pehla byte jab locked
        ho to dusra process use **padh hi nahi sakta** (ERROR_SHARING_VIOLATION),
        isliye PID wahan likhna error message ko 0 dikha deta tha."""
        try:
            first = self.pid_path.read_text(encoding="utf-8").splitlines()[0]
            return int(first.strip())
        except (OSError, ValueError, IndexError):
            return 0

    def diagnose(self, pid_probe=None, http_check=None) -> str:
        """"Pehle se chal raha hai" ki **saaf** baat. Test me dono probe daal
        do — asli process/socket nahi chhune padte.

        Sirf tab "chal raha hai" jab PID zinda HO **aur** `GET /` 200 de.
        """
        pid = self.owner_pid()
        pid_ok = pid_alive(pid, pid_probe)
        http_ok = http_alive(config.SERVER_ORIGIN, opener=http_check)
        who = config.ASSISTANT_NAME
        if pid_ok and http_ok:
            return ("%s pehle se CHAL raha hai (pid=%d). Usi tray icon se "
                    "Open HUD karo, ya Quit dabao." % (who, pid))
        if pid_ok:
            return ("%s ka process (pid=%d) zinda hai lekin HUD nahi de "
                    "raha - app atki hai. Task Manager se us pid ko band karo, "
                    "phir dobara chalao." % (who, pid))
        if http_ok:
            return ("%s ka koi process nahi (pid=%d murda) lekin port 8000 "
                    "kisi aur ka hai - ye lock stale nahi, dusra app us port "
                    "par hai." % (who, pid))
        return ("%s ka koi live process nahi (pid=%d) - lock stale hai. "
                "Ye naya instance apne aap lock pakad lega." % (who, pid))

    def _clean_stale_pid(self) -> None:
        """Lock mil gayi, matlab koi live process nahi. Purana `.pid` (mar ke
        baad bacha hua) ghabra karne na de — hata do."""
        old = self.owner_pid()
        if old and old != os.getpid() and not pid_alive(old):
            try:
                self.pid_path.unlink(missing_ok=True)
                log.warning("stale pid file hata di: %s (pid=%d)", self.pid_path, old)
            except OSError as exc:
                log.warning("stale pid file nahi hata: %s", exc)

    def _write_pid(self, pid: int) -> None:
        try:
            self.pid_path.write_text(f"{pid}\n", encoding="utf-8")
        except OSError as exc:
            log.warning("pid likha nahi gaya: %s", exc)

    def __enter__(self) -> "Single":
        return self.acquire()

    def __exit__(self, *_exc) -> None:
        self.release()
