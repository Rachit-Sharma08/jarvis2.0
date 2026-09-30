"""Allow/Deny ki approval. Har approval exact tool+args ke hash se bandha.

- Ek waqt me sirf EK pending card.
- Hash alag karne par approve nahi hota.
- Ek baar use hone ke baad dobara approve nahi ho sakta (replay block).
- 60 second me jawab na aaye to apne aap Deny.
"""

import hashlib
import json
import threading
import time

import config


def fingerprint(tool: str, args: dict) -> str:
    payload = json.dumps({"tool": tool, "args": args}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class Pending:
    def __init__(self, tool: str, args: dict, timeout: int = None):
        self.tool = tool
        self.args = args
        self.hash = fingerprint(tool, args)
        self.id = hashlib.sha256(f"{tool}{time.time()}".encode()).hexdigest()[:12]
        self.timeout = config.TOOL_CONFIRM_TIMEOUT if timeout is None else timeout
        self.started = time.monotonic()
        self.expires = self.started + self.timeout
        self.used = False
        self.allow = False
        self.event = threading.Event()

    def remaining(self) -> int:
        return max(0, round(self.expires - time.monotonic()))

    def expired(self) -> bool:
        return time.monotonic() >= self.expires


class Registry:
    def __init__(self):
        self._lock = threading.Lock()
        self._current = None

    def open(self, tool: str, args: dict, timeout: int = None) -> Pending:
        """Naya pending card. Purana hai to naya ban jaata hai (ek waqt me ek)."""
        with self._lock:
            self._current = Pending(tool, args, timeout=timeout)
            return self._current

    def busy(self) -> bool:
        with self._lock:
            current = self._current
        return bool(current and not current.used and not current.expired())

    def current(self):
        with self._lock:
            return self._current

    def decide(self, req_id: str, req_hash: str, allow: bool) -> tuple:
        """UI ke button se aata hai. -> (ok, reason)"""
        with self._lock:
            current = self._current
            if current is None or current.id != req_id:
                return False, "ye card abhi pending nahi hai"
            if current.used:
                return False, "ye card pehle hi use ho chuka hai"
            if current.expired():
                current.event.set()
                return False, "60 second nikal gaye — Deny"
            if req_hash != current.hash:
                return False, "hash match nahi hua — command badal diya gaya"
            current.used = True
            current.allow = bool(allow)
            current.event.set()
            return True, "allow" if allow else "deny"

    def wait(self, pending: Pending) -> tuple:
        """UI ka jawab ya timeout. -> (allowed, reason)"""
        if pending.event.wait(timeout=max(0.1, pending.remaining() + 0.05)):
            return (pending.allow, "user ne allow kiya" if pending.allow else "user ne deny kiya")
        with self._lock:
            if self._current is pending:
                self._current = None
        return False, "60 second me jawab nahi aaya — Deny"

    def cancel(self) -> tuple:
        """STOP dabane par pending card ko band karo."""
        with self._lock:
            current = self._current
            if current is None or current.used:
                return False, "koi pending card nahi"
            current.used = True
            current.allow = False
            current.event.set()
            return True, "STOP — card cancel"
