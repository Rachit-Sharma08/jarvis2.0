"""Single instance — ek hi app.

Do baar `start_prabh.bat` chala do to dono baar mic aur port 8000 ek saath
kholne ki koshish karenge. Is liye ek lock file pakdi jati hai.

Kaam Windows ka apna `msvcrt.locking` karta hai — iska fayda: lock file
process ke saath hi khatam hoti hai. Agar app crash ho gayi ya `taskkill`
kiya gaya to lock apne aap chhoot jaati hai, is liye mar ke baad dobara
chalao to bhi chalega. File ka content (PID) sirf report ke liye hai —
chalu hone ka faisla lock se hota hai, PID se nahi.
"""

import msvcrt
import os
from pathlib import Path

import config
from log_setup import get_logger

log = get_logger("single")


class AlreadyRunning(Exception):
    """Lock dusre process ne pakdi hui hai — ye instance nahi chalega."""


class Single:
    """Lock file khol kar pakad lo. `with` ya `release()` se chhod do."""

    def __init__(self, path: Path = None):
        self.path = Path(path or config.LOCK_FILE)
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
            raise AlreadyRunning(f"pehle se chal raha hai (pid={self.owner_pid()})")
        self._handle = handle
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
            log.info("single instance lock chhodi")

    def owner_pid(self) -> int:
        """Lock file me likha PID. Sirf log/error message ke liye."""
        try:
            return int(self.path.read_bytes().split(b",")[0] or 0)
        except (OSError, ValueError):
            return 0

    def _write_pid(self, pid: int) -> None:
        try:
            self._handle.seek(0)
            self._handle.truncate()
            self._handle.write(f"{pid},{int(self.path.stat().st_mtime)}".encode())
            self._handle.flush()
        except OSError as exc:
            log.warning("pid likha nahi gaya: %s", exc)

    def __enter__(self) -> "Single":
        return self.acquire()

    def __exit__(self, *_exc) -> None:
        self.release()
