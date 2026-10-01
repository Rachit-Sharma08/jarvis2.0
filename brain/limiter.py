"""Provider ka rate limiter — sliding window, per provider.

NVIDIA ki 40 RPM limit poori key par hai (saare models milake), isliye ek
pool-wide limiter chahiye — per-model count nahi chalega. Groq/Gemini par
limit 0 hai, matlab koi limit nahi.
"""

import threading
import time

from log_setup import get_logger

log = get_logger("limiter")


class RateLimiter:
    """max_calls rolling window me. Thread-safe (FastAPI async + WS dono)."""

    def __init__(self, name: str, max_calls: int, window: float = 60.0):
        self.name = name
        self.max_calls = max_calls
        self.window = window
        self._calls = []
        self._lock = threading.Lock()
        self.waits = 0

    def _prune(self, now: float) -> None:
        cut = now - self.window
        self._calls = [t for t in self._calls if t > cut]

    def wait_seconds(self) -> float:
        """Kitni der rukna hai (0 = abhi jaa sakta hai)."""
        if not self.max_calls:
            return 0.0
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            if len(self._calls) < self.max_calls:
                return 0.0
            return max(0.0, self._calls[0] + self.window - now)

    def take(self) -> None:
        """Slot book karo. `wait_seconds` 0 hone par hi call karo."""
        with self._lock:
            self._calls.append(time.monotonic())
            self._prune(time.monotonic())

    def acquire(self) -> float:
        """Ruko agar zaroorat hai, phir slot lo. Ruka hua time return karta hai."""
        slept = 0.0
        while True:
            wait = self.wait_seconds()
            if wait <= 0:
                break
            log.info("%s rate limit: %.1fs rukhna padega", self.name, wait)
            time.sleep(wait)
            slept += wait
            self.waits += 1
        self.take()
        return slept

    def used(self) -> int:
        now = time.monotonic()
        with self._lock:
            self._prune(now)
            return len(self._calls)

    def reset(self) -> None:
        with self._lock:
            self._calls = []


_LIMITERS = {}


def get(provider: dict) -> RateLimiter:
    """Provider config se limiter. max_calls=0 ho to unlimited limiter."""
    name = provider["name"]
    if name not in _LIMITERS:
        _LIMITERS[name] = RateLimiter(name, provider.get("rate_limit", 0))
    return _LIMITERS[name]


def reset_all() -> None:
    for lim in _LIMITERS.values():
        lim.reset()