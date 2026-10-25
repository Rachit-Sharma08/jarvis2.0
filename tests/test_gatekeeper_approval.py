"""Approval card, timeout, kill switch, rate limit aur log masking.

Koi tool chalta nahi — sirf Registry/Limiter/audit ka faisla. Engine mock nahi
chahiye; ye seedha decision layer test karta hai.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from gatekeeper import audit, keeper
from gatekeeper.approvals import Registry
from gatekeeper.limiter import Limiter


class ApprovalTest(unittest.TestCase):
    def test_hash_and_single_use(self):
        registry = Registry()
        pending = registry.open("run_command", {"command": "echo hi"})
        self.assertTrue(registry.busy())

        bad_hash, _ = registry.decide(pending.id, "not-the-hash", True)
        self.assertFalse(bad_hash, "hash galat hone par allow nahi hona chahiye")

        bad_id, _ = registry.decide("fake-id", pending.hash, True)
        self.assertFalse(bad_id, "galat id par allow nahi hona chahiye")

        ok, _ = registry.decide(pending.id, pending.hash, True)
        self.assertTrue(ok)
        again, reason = registry.decide(pending.id, pending.hash, True)
        self.assertFalse(again, "dobara use nahi hona chahiye")
        self.assertIn("pehle hi use", reason)

    def test_timeout_means_deny(self):
        registry = Registry()
        pending = registry.open("write_file", {"path": "x", "content": "y"}, timeout=1)
        started = time.monotonic()
        allowed, reason = registry.wait(pending)
        elapsed = time.monotonic() - started
        self.assertFalse(allowed, "timeout par DENY hona chahiye")
        self.assertIn("60 second", reason)
        self.assertGreaterEqual(elapsed, 0.9)

    def test_deny_works(self):
        registry = Registry()
        pending = registry.open("close_app", {"name": "notepad"})
        allowed, _ = registry.decide(pending.id, pending.hash, False)
        self.assertTrue(allowed)
        self.assertFalse(pending.allow)

    def test_only_one_pending_card(self):
        registry = Registry()
        first = registry.open("run_command", {"command": "echo 1"})
        self.assertTrue(registry.busy())
        registry.decide(first.id, first.hash, True)
        self.assertFalse(registry.busy(), "use hone ke baad nahi rehna chahiye")

    def test_naya_card_purana_cancel(self):
        """Naya card purane ko cancel kare - warna purana waiter 60s tak atka rehta."""
        registry = Registry()
        first = registry.open("run_command", {"command": "echo 1"})
        second = registry.open("run_command", {"command": "echo 2"})
        self.assertTrue(first.event.is_set(), "purana card cancel hona chahiye")
        allowed, reason = registry.wait(first)
        self.assertFalse(allowed)
        self.assertIn("naya card", reason)
        self.assertEqual(second, registry.current())


class LimiterTest(unittest.TestCase):
    def test_kill_switch(self):
        limiter = Limiter(enabled=True, per_minute=20)
        self.assertEqual("", limiter.check())
        limiter.set_enabled(False)
        self.assertIn("TOOLS OFF", limiter.check())
        limiter.set_enabled(True)
        self.assertEqual("", limiter.check())

    def test_rate_limit(self):
        limiter = Limiter(enabled=True, per_minute=20)
        for _ in range(20):
            self.assertEqual("", limiter.check())
            limiter.record()
        self.assertIn("limit", limiter.check())
        self.assertEqual(20, limiter.used())

    def test_auto_off_hook_lock_ke_bahar(self):
        """Hook lock ke andar chale to limiter ko padhne wala hook deadlock kar dega."""
        limiter = Limiter(enabled=True, auto_off_minutes=0.0004)   # ~24 ms
        free = []

        def hook(_on):
            got = limiter._lock.acquire(blocking=False)
            free.append(got)
            if got:
                limiter._lock.release()

        limiter.set_on_change(hook)
        time.sleep(0.06)
        self.assertFalse(limiter.enabled)
        self.assertEqual([True], free, "hook lock ke bahar chalna chahiye")

    def test_blocked_tool_budget_nahi_khata(self):
        """DENY par rate-limit slot na jaye - warna injection loop apni limit kha jaata."""
        saved = keeper.LIMITER
        keeper.LIMITER = Limiter(enabled=True, per_minute=3)
        try:
            for _ in range(5):
                decision, _ = keeper.review(
                    "run_command", {"command": "Remove-Item gatekeeper/keeper.py"}, "sunday")
                self.assertEqual(keeper.DENY, decision)
            self.assertEqual(0, keeper.LIMITER.used())
        finally:
            keeper.LIMITER = saved


class MaskTest(unittest.TestCase):
    def test_mask_hides_keys(self):
        fake = "gsk_test1234567890abcdef"
        self.assertNotIn(fake, audit.mask(f"key hai {fake} yahan"))
        self.assertIn("***", audit.mask(f"key hai {fake} yahan"))
        self.assertNotIn("AIzaSyABCDEFGHIJ", audit.mask("AIzaSyABCDEFGHIJ"))
        self.assertNotIn("sk_live_abcdefghijkl", audit.mask("sk_live_abcdefghijkl"))
        self.assertNotIn("AQ.AbCdEf", audit.mask("token=AQ.AbCdEfGhIjKlMnOpQrStUvWxYz012345"))
        if config.GROQ_API_KEY:
            self.assertNotIn(config.GROQ_API_KEY, audit.mask(f"leak {config.GROQ_API_KEY}"))

    def test_action_log_masked(self):
        line = keeper.audit.log_action(
            "prabh", "run_command", {"command": "echo gsk_abcdefghijklmnop"}, "ask", "card bheja"
        )
        self.assertIn("decision=ask", line)
        self.assertNotIn("gsk_abcdefghijklmnop", line)
        self.assertTrue(config.ACTION_LOG.exists())


if __name__ == "__main__":
    unittest.main(verbosity=1)
