"""Jarvis ke andar ka alarm tool — **DEFAULT OFF**.

Boliye *"kal subah 7 baje utha dena"* → ye `set_wake_alarm` uss samay ka
request `data/alarm_request.json` me likh deta hai. **Sirf itna.**

**Task Scheduler se ye kuch nahi karta.** Registry banana alag kaam hai aur wo
hamesha haath se hota hai — `python tools/wake_alarm.py --install`. Isi liye LLM
ke text se system badalne ka koi raasta hi nahi banta (NIYAM: system files band).

Turn on karne ke liye `.env` me `PRABH_ALARM_TOOL=1`. Default **0** — tool
`tools/__init__.py` ka `spec()` me dikhai dega hi nahi, aur `execute()` bhi
manega.

`tools/wake_alarm.py` (alag script, Task Scheduler se 07:00/07:10 par chalti
hai) wahi file padhta hai — yahi dono ka ek hi raasta hai.
"""

import datetime
import json
import re

import config
from log_setup import get_logger

log = get_logger("alarm_tool")

REQUEST_FILE = "alarm_request.json"
MAX_MINUTES = 15
MIN_MINUTES = 1

# "7:30 am" / "7.30" — ghante + minute saath. Pehle ye, warna "7" me minute
# chhoot jayega (pehle ka regex "7:30 am" me "30 am" uthata tha = 30 ghante!).
_HHMM = re.compile(r"(\d{1,2})\s*[:.]\s*(\d{1,2})\s*(a\.?m\.?|p\.?m\.?)?", re.IGNORECASE)
# "7", "7 baje", "7 am", "7pm" — sirf ghante.
_HOUR = re.compile(r"(\d{1,2})\s*(a\.?m\.?|p\.?m\.?)?", re.IGNORECASE)


def _apply_meridiem(hour: int, meridiem: str) -> int:
    if not meridiem:
        return hour
    tag = meridiem[0].lower()
    if tag == "p" and hour < 12:
        return hour + 12
    if tag == "a" and hour == 12:
        return 0
    return hour


def request_path():
    return config.DATA_DIR / REQUEST_FILE


def parse_when(text: str, now: datetime.datetime = None) -> datetime.datetime:
    """"7 baje" / "7:30 am" -> agli **datetime**. ValueError par message.

    Aaj ka time nikal chuka ho to **kal** — user ko subah 7 bola hai matlab
    agle subah, aaj raat 2 baje nahi.
    """
    now = now or datetime.datetime.now()
    raw = str(text or "").strip().lower()
    if not raw:
        raise ValueError("samay nahi mila")

    hour = minute = None
    meridiem = ""
    match = _HHMM.search(raw)
    if match:
        hour, minute, meridiem = (int(match.group(1)), int(match.group(2)),
                                  match.group(3) or "")
    else:
        match = _HOUR.search(raw)
        if not match:
            raise ValueError(f"samay samajh nahi aaya: {text!r}")
        hour, minute, meridiem = int(match.group(1)), 0, match.group(2) or ""

    hour = _apply_meridiem(hour, meridiem)
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError(f"galat samay: {text!r} (0-23 ghante, 0-59 minute)")

    when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if when <= now:
        when += datetime.timedelta(days=1)
    return when


def clamp_minutes(value: str) -> int:
    """`repeat_minutes` 1..15 ke beech. Baaki number chhoot jaye to default."""
    try:
        got = int(str(value).strip())
    except (TypeError, ValueError):
        return MAX_MINUTES
    return max(MIN_MINUTES, min(MAX_MINUTES, got))


def read_request() -> dict:
    """Jo request likhi gayi hai. `{}` agar kuch nahi ya kharab."""
    try:
        return json.loads(request_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def set_wake_alarm(at: str, repeat_minutes: str = "15") -> str:
    """Alarm set karo (sirf request file). -> user ko dikhane layak line.

    `PRABH_ALARM_TOOL=0` (default) par kuch nahi likha jaata."""
    if not config.ALARM_TOOL_ENABLED:
        return ("Alarm tool abhi BAND hai. Sath me `tools/wake_alarm.py` se "
                "alarm chalaya ja sakta hai, ya .env me PRABH_ALARM_TOOL=1 karo.")
    try:
        when = parse_when(at)
    except ValueError as exc:
        return f"alarm set nahi hua: {exc}"
    data = {
        "when": when.isoformat(timespec="minutes"),
        "repeat_minutes": clamp_minutes(repeat_minutes),
        "task": "JarvisWakeAlarm",
    }
    try:
        request_path().parent.mkdir(parents=True, exist_ok=True)
        request_path().write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
    except OSError as exc:
        return f"alarm likha nahi ja paya: {exc}"
    log.info("alarm request: %s", data)
    return ("Alarm set: %s (har %d min tak dohrayega). Task banani hai to "
            "`python tools/wake_alarm.py --install`." % (when.strftime("%d %b %I:%M %p"),
                                                         data["repeat_minutes"]))


def alarm_status() -> str:
    """Abhi ka alarm request — `''` matlab koi nahi."""
    if not config.ALARM_TOOL_ENABLED:
        return "Alarm tool BAND hai (PRABH_ALARM_TOOL=1 karo)."
    data = read_request()
    if not data.get("when"):
        return "Koi alarm set nahi hai."
    return ("Alarm: %s | har %s min | task %s" % (
        data.get("when"), data.get("repeat_minutes", MAX_MINUTES),
        data.get("task", "JarvisWakeAlarm")))
