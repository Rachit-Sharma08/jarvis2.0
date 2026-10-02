"""Kill switch + rate limit. Ek minute me 20 tool calls.

Kill switch OFF hote hi koi bhi tool nahi chalta — gate yahin par rok deta hai.

Saath me **auto-off**: TOOLS ON karne ke `config.TOOLS_AUTO_OFF_MINUTES`
(30) minute baad kill switch apne aap OFF ho jaata hai. Iska matlab — bhool
kar chhod diya to raat bhar PC tools se khula na rahe. Timer `set_enabled`
se chalta hai, app ke band hone par nahi.
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

    @property
    def enabled(self) -> bool:
        with self._lock:
            self._expire()
            return self._enabled

    def set_enabled(self, on: bool) -> bool:
        with self._lock:
            self._enabled = bool(on)
            if self._enabled:
                self._since = time.monotonic()
            else:
                self._calls.clear()
            return self._enabled

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
                return "ek minute me 20 tool ki limit poori ho gayi. Thodi der baad."
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

    def _prune(self) -> None:
        cutoff = time.monotonic() - 60
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()
