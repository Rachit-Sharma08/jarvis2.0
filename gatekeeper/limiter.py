"""Kill switch + rate limit. Ek minute me 20 tool calls.

Kill switch OFF hote hi koi bhi tool nahi chalta — gate yahin par rok deta hai.
"""

import threading
import time
from collections import deque

import config


class Limiter:
    def __init__(self, enabled: bool = None, per_minute: int = None):
        self._lock = threading.Lock()
        self._calls = deque()
        self._enabled = config.TOOLS_ENABLED_DEFAULT if enabled is None else enabled
        self._per_minute = per_minute or config.TOOL_MAX_CALLS_PER_MINUTE

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def set_enabled(self, on: bool) -> bool:
        with self._lock:
            self._enabled = bool(on)
            if not self._enabled:
                self._calls.clear()
            return self._enabled

    def check(self) -> str:
        """-> '' (chal sakta hai) ya wajah."""
        with self._lock:
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

    def _prune(self) -> None:
        cutoff = time.monotonic() - 60
        while self._calls and self._calls[0] < cutoff:
            self._calls.popleft()
