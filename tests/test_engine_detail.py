"""Tool output aur confirm card ki detail — dono jagah keys chhupani hain.

Ye test confirm karta hai ki koi secret na LLM tak pahunche, na UI event me,
na engine ke return value me. Tool executor mock hai.
"""

import json
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from core import engine as engine_mod
from core.engine import Engine, _detail
from datasafe import DataSafeCase
from gatekeeper import keeper
from gatekeeper.limiter import Limiter

FAKE_KEY = "gsk_realkey1234567890abcdef"


def collect(gen) -> list:
    out = []
    while True:
        try:
            out.append(next(gen))
        except StopIteration:
            return out


def value_of(gen):
    while True:
        try:
            next(gen)
        except StopIteration as stop:
            return stop.value


class LimiterCase(DataSafeCase):
    """Har test me tools ON chahiye; global limiter OFF default aata hai."""

    def setUp(self):
        super().setUp()
        self._saved = keeper.LIMITER
        keeper.LIMITER = Limiter(enabled=True, per_minute=config.TOOL_MAX_CALLS_PER_MINUTE)

    def tearDown(self):
        keeper.LIMITER = self._saved
        super().tearDown()


class OutputMaskTest(LimiterCase):
    def test_output_masked_before_llm(self):
        with mock.patch.object(engine_mod, "execute", return_value=f"token {FAKE_KEY}"):
            value = value_of(Engine().run_tool("system_info", {}))
        self.assertNotIn(FAKE_KEY, value)
        self.assertIn("***", value)

    def test_output_masked_in_activity_event(self):
        with mock.patch.object(engine_mod, "execute", return_value=f"token {FAKE_KEY}"):
            events = collect(Engine().run_tool("system_info", {}))
        activity = [e for e in events if e["type"] == "activity"][0]
        self.assertNotIn(FAKE_KEY, activity["text"])

    def test_data_note_goes_to_llm(self):
        engine = Engine()
        replies = [json.dumps({"action": "get_time_date", "args": {}}), "ho gaya"]
        with mock.patch.object(
            engine_mod.router, "ask", side_effect=lambda *a: (replies.pop(0), "groq")
        ), mock.patch.object(engine_mod, "execute", return_value="data"):
            collect(engine.handle("kya time hai"))
        fed = [m for m in engine.history if "tool=get_time_date" in m["content"]]
        self.assertEqual(1, len(fed))
        self.assertIn("sirf DATA", fed[0]["content"])


class CardDetailTest(LimiterCase):
    def setUp(self):
        super().setUp()
        # Card wale purane raaste ka test - ASK jaan-boojh kar chalu.
        self._nocards = mock.patch.object(config, "NO_CARDS", False)
        self._nocards.start()

    def tearDown(self):
        self._nocards.stop()
        super().tearDown()

    def test_command_detail_keeps_command_hides_key(self):
        detail = _detail("run_command", {"command": f"echo hi {FAKE_KEY}"})
        self.assertIn("echo hi", detail, "command poori dikhni chahiye")
        self.assertNotIn(FAKE_KEY, detail, "card par asli key leak ho rahi thi")

    def test_write_file_detail_masked(self):
        detail = _detail("write_file", {"path": "a.txt", "content": f"key {FAKE_KEY}"})
        self.assertIn("a.txt", detail)
        self.assertNotIn(FAKE_KEY, detail)

    def test_plain_detail_unchanged(self):
        self.assertEqual("name=notepad", _detail("close_app", {"name": "notepad"}))

    def test_ask_card_detail_masked_end_to_end(self):
        engine = Engine()
        replies = [json.dumps({"action": "write_file", "args": {"path": "c.txt", "content": FAKE_KEY}})]
        with mock.patch.object(
            engine_mod.router, "ask", side_effect=lambda *a: (replies.pop(0), "groq")
        ), mock.patch.object(config, "TOOL_CONFIRM_TIMEOUT", 1):
            events = collect(engine.handle("likh do"))
        card = [e for e in events if e["type"] == "confirm"][0]
        self.assertNotIn(FAKE_KEY, card["detail"], "confirm card me asli key gayi")


if __name__ == "__main__":
    unittest.main(verbosity=1)
