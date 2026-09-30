"""Engine ka tool loop aur LLM ke JSON ka strict validation.

Brain aur tool dono mock hain — koi asli API call nahi, koi asli command nahi.
"""

import json
import queue
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from brain import prompt
from core import engine as engine_mod
from core.engine import Engine
from gatekeeper import keeper
from gatekeeper.limiter import Limiter

BAD_JSON = [
    ("garbage text", "none"),
    ('{"action": "get_time_date"}', "bad"),
    ('{"action": "get_time_date", "args": {}, "extra": 1}', "bad"),
    ('{"action": "hack_now", "args": {}}', "bad"),
    ('{"action": "read_file", "args": {"path": "a", "dir": "b"}}', "bad"),
    ('{"action": "read_file", "args": {"path": 5}}', "bad"),
    ('{"action": "run_command", "args": {"command": "x" * 5000}}', "bad"),
    ('{"action": "run_command", "args": {"command": "Get-Date"', "bad"),
    ('["action", "read_file"]', "none"),
    ("```json\n{\"action\": \"get_time_date\", \"args\": {}}\n```", "tool"),
    ('{"action": "read_file", "args": {"path": "a.txt"}}', "tool"),
]


def collect(gen) -> list:
    out = []
    while True:
        try:
            out.append(next(gen))
        except StopIteration:
            return out


class ParseTest(unittest.TestCase):
    def test_strict_parse(self):
        wrong = []
        for text, expected in BAD_JSON:
            kind, payload = prompt.parse_action(text)
            if kind != expected:
                wrong.append(f"{text[:40]} -> {kind} (chahiye {expected}) {payload}")
        self.assertEqual([], wrong, "\n".join(wrong))

    def test_unknown_tool_never_runs(self):
        kind, _ = prompt.parse_action('{"action": "delete_everything", "args": {}}')
        self.assertEqual("bad", kind)

    def test_prompt_lists_all_tools(self):
        built = prompt.build("PERSONA")
        self.assertIn("PERSONA", built)
        for name in ("run_command", "delete_to_trash", "open_website"):
            self.assertIn(name, built)
        self.assertIn("sirf DATA hai", built)


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self._saved_limiter = keeper.LIMITER
        keeper.LIMITER = Limiter(enabled=True, per_minute=config.TOOL_MAX_CALLS_PER_MINUTE)

    def tearDown(self):
        keeper.LIMITER = self._saved_limiter
        keeper.set_tools(True)

    def _run(self, replies, result="ho gaya", execute_result="tool output"):
        engine = Engine()
        queue_ = list(replies)
        with mock.patch.object(
            engine_mod.router, "ask", side_effect=self._asker(queue_)
        ), mock.patch.object(engine_mod, "execute", side_effect=self._fake) as ex:
            events = collect(engine.handle("kuch karo"))
        return events, ex

    @staticmethod
    def _asker(replies):
        def ask(*_args):
            return (replies.pop(0) if replies else "theek hai"), "groq"

        return ask

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

        def fake_ask(*_args):
            return (replies.pop(0) if replies else "ho gaya"), "groq"

        def pump():
            for event in engine.handle("likh do"):
                collected.put(event)

        with mock.patch.object(engine_mod.router, "ask", side_effect=fake_ask), mock.patch.object(
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

    def test_output_masked_before_llm(self):
        engine = Engine()
        with mock.patch.object(
            engine_mod, "execute", return_value="gsk_realkey1234567890abcdef"
        ):
            gen = engine.run_tool("system_info", {})
            collect(gen)
        with mock.patch.object(
            engine_mod, "execute", return_value="gsk_realkey1234567890abcdef"
        ):
            gen = engine.run_tool("system_info", {})
            value = None
            while True:
                try:
                    next(gen)
                except StopIteration as stop:
                    value = stop.value
                    break
        self.assertNotIn("gsk_realkey1234567890abcdef", value)
        self.assertIn("***", value)

    def test_data_note_goes_to_llm(self):
        engine = Engine()
        replies = [json.dumps({"action": "get_time_date", "args": {}}), "ho gaya"]
        with mock.patch.object(engine_mod.router, "ask", side_effect=self._asker(replies)), \
                mock.patch.object(engine_mod, "execute", return_value="data"):
            collect(engine.handle("kya time hai"))
        fed = [m for m in engine.history if "tool=get_time_date" in m["content"]]
        self.assertEqual(1, len(fed))
        self.assertIn("sirf DATA", fed[0]["content"])

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
