"""Phone par kaam — Artemis CLI ka **ek hi raasta**.

Google Artemis (`D:\\artemis`) ADB se asli Android phone chalata hai: khud
screen dekhta hai, khud tap/type karta hai, aur aakhir me ek line me batata
hai ki kaam hua ya nahi. Jarvis yahan se sirf `artemis run "<kaam>"`
bulata hai — phone ka faisla Artemis ka hai, is file ka nahi.

**Time:** ek kaam 2-3 minute le sakta hai (har step par screen + model call).
Is liye engine ka tool timeout `config_phone.PHONE_TIMEOUT_SECONDS` se aata
hai, aur beech me jawab nahi aata — bas ek line ka result.

**Suraksha:** `subprocess.run(..., shell=False)` + list args, is liye kaam ke
text me `&` ya `;` likha ho to wo command nahi banta. Phone par kya allowed
hai wo Artemis ka apna guard dekhta hai; Jarvis ka gatekeeper is tool ko ASK
rakhta hai aur `nocards` ise allow karta hai (owner ka faisla).
"""

import re
import subprocess

import config_phone
from log_setup import get_logger

log = get_logger("tools.phone")

# Artemis aakhir me `report_task_status({'status': ..., 'explanation': '...'})`
# chhaapta hai. Wahi asli jawab hai; poora log 2000 char se bahut bada hota hai.
_EXPLAIN = re.compile(r"['\"]explanation['\"]\s*:\s*['\"](.+?)['\"]\s*[,}]", re.S)
_NO_DEVICE = ("no device", "device offline", "unauthorized", "device not found",
              "no devices", "adb: device")


def _command(goal: str) -> list:
    return ["uv", "run", "artemis", "run", goal,
            "--profile", config_phone.ARTEMIS_PROFILE]


def _run(cmd: list, timeout: int, cwd: str):
    """Test me yahi patch hota hai — asli adb/phone kabhi nahi chalta."""
    return subprocess.run(cmd, cwd=cwd, shell=False, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=timeout)


def _clean(text: str) -> str:
    return " ".join(str(text or "").split())


def _answer(out: str) -> str:
    """Artemis ka aakhri saaf jawab, warna ''. `'` do baar aa sakta hai."""
    hit = _EXPLAIN.search(out or "")
    if hit:
        return _clean(hit.group(1))[:400]
    for line in reversed((out or "").splitlines()):
        if "report_task_status" in line:
            return _clean(line)[:400]
    return ""


def phone_task(task: str = "") -> str:
    """Phone par kaam karo. -> ek chhoti Hinglish line."""
    goal = _clean(task)[:300]
    if not goal:
        return "Phone par kya karna hai? (jaise 'Karun ko call karo')"
    log.info("phone_task: %s", goal)
    try:
        res = _run(_command(goal), config_phone.PHONE_TIMEOUT_SECONDS,
                   config_phone.ARTEMIS_DIR)
    except FileNotFoundError:
        return "Artemis nahi mila ('uv' PATH me nahi) — phone control band hai."
    except subprocess.TimeoutExpired:
        return ("Phone kaam %d second me poora nahi hua — phone dekho."
                % config_phone.PHONE_TIMEOUT_SECONDS)

    out = (res.stdout or "") + "\n" + (res.stderr or "")
    answer = _answer(out)
    if answer:
        return "Phone: " + answer
    low = out.lower()
    if any(mark in low for mark in _NO_DEVICE):
        return "Phone connect nahi hai — USB ya wireless debugging on karo."
    return "Phone kaam ka saaf jawab nahi mila (Artemis log dekho)."
