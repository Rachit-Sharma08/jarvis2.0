"""Windows lock (Win+L) ka pata — taaki lock par TOOLS apne aap OFF ho jaye.

User ka niyam: lock hone par sirf baat-cheet chalti hai, koi tool nahi.

**Ye 100% ka pakka nahi hai** — `OpenInputDesktop()` Windows ka documented
API hai, par lock/switch par uska behaviour ek **heuristic** hai. Is liye:

- detect ho gaya  → tools OFF + log
- detect nahi hua → sirf log me report (`lock_watch: ...`), **kuch block
  nahi karte**. Galat pakad kar baat-cheet band karna bura hoga.

`python -m desktop.lockwatch` chala kar PC lock karke dekh sakte ho ki
is laptop par kaam karta hai ya nahi — `logs/jarvis.log` me `locked=True/False`
likha hoga. Jo bhi sach nikle, wahi AGENTS.md me likha jayega.
"""

import ctypes
import threading
import time

import config
from log_setup import get_logger

log = get_logger("lockwatch")

DESKTOP_SWITCHDESKTOP = 0x0100
_user32 = ctypes.windll.user32


def is_locked() -> bool:
    """>=0 ka matlab desktop khula hai. Exception aaye to 'band nahi' maan lo."""
    try:
        handle = _user32.OpenInputDesktop(0, False, DESKTOP_SWITCHDESKTOP)
    except OSError as exc:
        log.warning("OpenInputDesktop fail: %s", exc)
        return False
    if not handle:
        return True
    try:
        _user32.CloseDesktop(handle)
    except OSError:
        pass
    return False


def watch(on_lock, on_unlock=None, stop: threading.Event = None) -> threading.Thread:
    """Background me `on_lock()` / `on_unlock()` ko bulao. Daemon thread."""
    stop = stop or threading.Event()

    def run():
        last = is_locked()
        log.info("lock_watch: shuru, locked=%s", last)
        while not stop.is_set():
            time.sleep(config.LOCK_POLL_SECONDS)
            now = is_locked()
            if now == last:
                continue
            last = now
            log.info("lock_watch: locked=%s", now)
            try:
                (on_lock if now else (on_unlock or (lambda: None)))()
            except Exception as exc:
                log.error("lock_watch callback: %s: %s", type(exc).__name__, exc)

    thread = threading.Thread(target=run, name="lockwatch", daemon=True)
    thread.start()
    return thread


def main() -> int:
    """`python -m desktop.lockwatch` — 2 second par ek line, khuli ya band."""
    print("Har 2 second me lock ka haalat. Band karke dekho — Ctrl+C se ruko.")
    last = None
    try:
        while True:
            now = is_locked()
            if now != last:
                last = now
                print(f"locked={now}")
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nband")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
