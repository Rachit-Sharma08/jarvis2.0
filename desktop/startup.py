"""Startup ki 4 standard line - `server up` / `tray started` / `HUD ready` /
`wake: stub`.

Ye alag file is liye hai ki `desktop/app.py` 200 line se chhota rahe. Shabd
`config_desktop.py` me hain; **bolne wala sirf `desktop/app.py` hai**, is liye
har line ek hi jagah se aati hai.

Line do jagah jaati hain:
  - `logs/prabh.log` me (ASCII, `log_setup.AsciiFormatter`)
  - seedha console par - app `start_prabh.bat` se chalta hai, to crash me
    user ko turant dikhe. Sirf log me rakhne se wo kuch nahi jaanta.
"""

import time
import urllib.error
import urllib.request

from log_setup import get_logger

log = get_logger("startup")


def say(step: str, detail: str = "") -> None:
    """`step` wahi shabd ho jo `config_desktop.STARTUP_*` me hai."""
    line = "%s: %s" % (step, detail) if detail else step
    log.info("%s", line)
    print(line, flush=True)


def await_http(origin: str, timeout: float) -> tuple:
    """Server sach me 200 de raha hai? -> (ok, reason)

    Port busy / crash / route error par `ok=False` aur wajah. Chup-chaap
    na ruke - caller "HUD ready: FAILED - <wajah>" bol kar aage badhta hai,
    taaki asli crash console par dikhe.
    """
    deadline = time.monotonic() + timeout
    reason = "timeout"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(origin + "/", timeout=2) as res:
                if res.status == 200:
                    return True, "ok"
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", exc)
        except OSError as exc:            # ConnectionRefusedError, timeout
            reason = exc
        time.sleep(0.4)
    return False, reason