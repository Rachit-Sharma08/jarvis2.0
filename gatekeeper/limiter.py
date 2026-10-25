"""Kill switch + rate limit. Ek minute me 20 tool calls.

Kill switch OFF hote hi koi bhi tool nahi chalta — gate yahin par rok deta hai.

Saath me **auto-off** (optional): TOOLS ON karne ke
`config.TOOLS_AUTO_OFF_MINUTES` minute baad kill switch apne aap OFF ho jaata
tha — bhool kar chhod diya to raat bhar PC tools se khula na rahe. 4-Oct ko
user ne kaha TOOLS **hamesha** ON rahega, is liye ab wo `0` (band) hai. `0`
ka matlab: timer kabhi nahi chalta. `.env` me `JARVIS_TOOLS_AUTOOFF=30` daal
kar wapas 30-minute wala behaviour aa jaata hai.
"""

import threading
import time
from collections import deque

import config
from log_setup import get_logger

log = get_logger("limiter")


class Limiter:
    def __init__(self, enabled: bool = None, per_minute: int = None,
                 auto_off_minutes: int = None):
        self._lock = threading.Lock()
        self._calls = deque()
        self._enabled = config.TOOLS_ENABLED_DEFAULT if enabled is None else enabled
        self._per_minute = per_minute or config.TOOL_MAX_CALLS_PER_MINUTE
        self._auto_off = (config.TOOLS_AUTO_OFF_MINUTES if auto_off_minutes is None
                          else auto_off_minutes)
        self._since = time.monotonic()
        self._on_change = None

    def set_on_change(self, func) -> None:
        """TOOLS on/off ya auto-OFF hone par ek baar call hona hai.

        Desktop tray + HUD ka mic/tools haalat isi se refresh hota hai, taaki
        TOOLS toggle UI se, tray se, lock se ya timer se kahan se bhi kiya ho —
        sab ka ek hi raasta rahe (`gatekeeper` me `desktop` ka import nahi).

        **Hook dobara `Limiter` me call nahi karega** (auto-off ke andar lock
        pakda hota hai) — sirf haalat update kare.
        """
        self._on_change = func

    @property
    def enabled(self) -> bool:
        with self._lock:
            self._expire()
            return self._enabled

    def set_enabled(self, on: bool) -> bool:
        with self._lock:
            changed = self._enabled != bool(on)
            self._enabled = bool(on)
            if self._enabled:
                self._since = time.monotonic()
            else:
                self._calls.clear()
            value = self._enabled
        self._notify(changed)
        return value

    def minutes_left(self) -> float:
        """Auto-off me bache minute. OFF hai to 0."""
        with self._lock:
            if not self._enabled:
                return 0.0
            left = self._auto_off * 60 - (time.monotonic() - self._since)
            return round(max(0.0, left) / 60, 1)

    def check(self) -> str:
        """-> '' (chal sakta hai) ya wajah."""
        with self._lock:
            self._expire()
            if not self._enabled:
                return "TOOLS OFF hai. Upar ka TOOLS toggle dabao."
            self._prune()
            if len(self._calls) >= self._per_minute:
                return (f"ek minute me {self._per_minute} tool ki limit poori ho gayi. "
                        "Thodi der baad.")
            return ""

    def record(self) -> None:
        with self._lock:
            self._calls.append(time.monotonic())

    def used(self) -> int:
        with self._lock:
            self._prune()
            return len(self._calls)

    def _expire(self) -> None:
        """30 minute ho gaye to OFF. Ye har read par chalta hai — alag timer
        thread nahi, is liye band karne par bhi koi thread na atke."""
        if not self._enabled or self._auto_off <= 0:
            return
        if time.monotonic() - self._since < self._auto_off * 60:
            return
        self._enabled = False
        self._calls.clear()
        log.warning(
            "TOOLS auto-OFF: %d minute ho gaye. Dobara ON karne ke liye toggle dabao.",
            self._auto_off,
        )
        self._notify(True)

    def _notify(self, changed: bool) -> None:
        """Hook ko batao. Hook crash kare to gatekeeper kabhi na fute."""
        if not changed or self._on_change is None:
            return
        try:
            self._on_change(self._enabled)
        except Exception as exc:
            log.warning("on-change hook fail: %s: %s", type(exc).__name__, exc)

    def _prune(self) -> None:
        cutoff = time.monotonic() - 60
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()
