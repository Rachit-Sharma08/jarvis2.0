"""Engine ka tool loop: SAFE/ASK/BLOCKED, 5-step limit, kill switch, parity.

Brain aur tool dono mock hain — koi asli API call nahi, koi asli command nahi.
JSON strictness `test_prompt_strict.py` me hai, masking `test_engine_detail.py` me.
"""

import json
import queue
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from core import engine as engine_mod
from core.engine import Engine
from gatekeeper import keeper
from gatekeeper.limiter import Limiter


def collect(gen) -> list:
    out = []
    while True:
        try:
            out.append(next(gen))
        except StopIteration:
            return out


def asker(replies):
    def ask(*_args):
        return (replies.pop(0) if replies else "theek hai"), "groq"

    return ask


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self._saved_limiter = keeper.LIMITER
        keeper.LIMITER = Limiter(enabled=True, per_minute=config.TOOL_MAX_CALLS_PER_MINUTE)

    def tearDown(self):
        keeper.LIMITER = self._saved_limiter
        keeper.set_tools(True)

    def _run(self, replies):
        engine = Engine()
        with mock.patch.object(
            engine_mod.router, "ask", side_effect=asker(list(replies))
        ), mock.patch.object(engine_mod, "execute", side_effect=self._fake) as ex:
            events = collect(engine.handle("kuch karo"))
        return events, ex

    def _fake(self, name, args):
        self.calls.append((name, args))
        return "tool output"

    def test_safe_tool_runs_then_answers(self):
        events, ex = self._run(
            [json.dumps({"action": "get_time_date", "args": {}}), "ab 5 baj rahi hai"]
        )
        self.assertEqual(1, ex.call_count)
        self.assertEqual(("get_time_date", {}), self.calls[0])
        activity = [e for e in events if e["type"] == "activity"]
        self.assertEqual("allow", activity[0]["decision"])
        last = [e for e in events if e["type"] == "message" and e["role"] == "assistant"][-1]
        self.assertIn("5 baj rahi hai", last["text"])

    def test_blocked_tool_never_executes(self):
        events, ex = self._run(
            [json.dumps({"action": "run_command", "args": {"command": "del C:\\"}}), "ruk gaya"]
        )
        self.assertEqual(0, ex.call_count, "BLOCKED command chal gaya!")
        activity = [e for e in events if e["type"] == "activity"][0]
        self.assertEqual("deny", activity["decision"])
        self.assertNotIn("confirm", [e["type"] for e in events], "BLOCKED par card nahi aana chahiye")

    def test_bad_json_never_executes(self):
        events, ex = self._run(['{"action": "get_time_date", "args": {"x": 1}}', "theek hai"])
        self.assertEqual(0, ex.call_count)
        self.assertTrue([e for e in events if e["type"] == "activity"] == [])

    def test_ask_timeout_is_deny(self):
        with mock.patch.object(config, "TOOL_CONFIRM_TIMEOUT", 1):
            events, ex = self._run(
                [json.dumps({"action": "write_file", "args": {"path": "a.txt", "content": "x"}}), "ho gaya"]
            )
        self.assertEqual(0, ex.call_count, "card ke bina likh dala!")
        confirm = [e for e in events if e["type"] == "confirm"]
        self.assertEqual(1, len(confirm))
        self.assertIn("a.txt", confirm[0]["detail"])
        self.assertEqual("deny", [e for e in events if e["type"] == "activity"][0]["decision"])

    def test_ask_allow_from_button(self):
        engine = Engine()
        collected = queue.Queue()
        replies = [
            json.dumps({"action": "write_file", "args": {"path": "b.txt", "content": "x"}}),
            "likh diya",
        ]
        self.calls = []

        def pump():
            for event in engine.handle("likh do"):
                collected.put(event)

        with mock.patch.object(engine_mod.router, "ask", side_effect=asker(replies)), mock.patch.object(
            engine_mod, "execute", side_effect=lambda n, a: self.calls.append((n, a)) or "likh diya"
        ):
            worker = threading.Thread(target=pump, daemon=True)
            worker.start()
            card = None
            deadline = time.time() + 10
            while card is None and time.time() < deadline:
                try:
                    event = collected.get(timeout=1)
                except queue.Empty:
                    break
                if event["type"] == "confirm":
                    card = event
            self.assertIsNotNone(card, "Allow/Deny card nahi aaya")
            self.assertEqual("write_file", card["tool"])

            ok, _ = keeper.APPROVALS.decide(card["id"], "galat-hash", True)
            self.assertFalse(ok, "galat hash se allow ho gaya")
            ok, _ = keeper.APPROVALS.decide(card["id"], card["hash"], True)
            self.assertTrue(ok)
            worker.join(timeout=10)

        self.assertEqual(1, len(self.calls), "Allow ke baad tool chalana chahiye tha")

    def test_max_five_steps(self):
        action = json.dumps({"action": "get_time_date", "args": {}})
        events, ex = self._run([action] * 9)
        self.assertEqual(config.TOOL_MAX_STEPS, ex.call_count)
        last = [e for e in events if e["type"] == "message" and e["role"] == "assistant"][-1]
        self.assertIn("5 tool step", last["text"])

    def test_kill_switch_blocks_loop(self):
        keeper.set_tools(False)
        events, ex = self._run(
            [json.dumps({"action": "get_time_date", "args": {}}), "ho gaya"]
        )
        self.assertEqual(0, ex.call_count)
        activity = [e for e in events if e["type"] == "activity"][0]
        self.assertIn("TOOLS OFF", activity["text"])

    def test_same_faisla_both_modes(self):
        seen = []
        for mode in ("sunday", "prabh"):
            engine = Engine()
            engine.mode = mode
            with mock.patch.object(engine_mod, "execute", return_value="x") as ex:
                events = collect(engine.run_tool("run_command", {"command": "reg delete HKLM"}))
            self.assertEqual(0, ex.call_count, f"{mode} me BLOCKED command chal gaya")
            activity = [e for e in events if e["type"] == "activity"][0]
            self.assertEqual("deny", activity["decision"])
            self.assertNotIn("confirm", [e["type"] for e in events])
            seen.append(activity["text"])
        self.assertEqual(seen[0], seen[1], "Sunday aur Prabh ka faisla alag tha")
        self.assertIn("registry delete", seen[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
