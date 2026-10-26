"""LLM ke tool JSON ka strict validation — brain/prompt.py ka apna test.

Garbage ya extra key wala JSON hamesha reject hona chahiye; valid action
sirf `{"action": ..., "args": {...}}` shape me hi maana jaye.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from brain import prompt

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
    ('{"action": "get_time_date", "args": {}, "action": "run_command"}', "bad"),
    ("```json\n{\"action\": \"get_time_date\", \"args\": {}}\n```", "tool"),
    ('{"action": "read_file", "args": {"path": "a.txt"}}', "tool"),
    ('{"action": "open_app", "args": {"name": "brave"}}', "tool"),
    ('{"action": "open_app", "args": {"name": "brave", "url": "https://youtu.be/x"}}', "tool"),
    ('{"action": "open_app", "args": {"url": "https://youtu.be/x"}}', "bad"),
    ('{"action": "open_app", "args": {"name": "brave", "bogus": "1"}}', "bad"),
    ('{"action": "play_media", "args": {"query": "mahabharat"}}', "tool"),
    ('{"action": "media_control", "args": {"action": "forward"}}', "tool"),
]


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

    def test_duplicate_key_rejected(self):
        """Do `action` keys ho to aakhri wali chhup kar chal sakti thi — reject karo."""
        kind, _ = prompt.parse_action('{"action": "get_time_date", "args": {}, "action": "run_command"}')
        self.assertEqual("bad", kind)

    def test_prompt_lists_all_tools(self):
        built = prompt.build("PERSONA")
        self.assertIn("PERSONA", built)
        for name in ("run_command", "delete_to_trash", "open_website",
                     "play_media", "media_control"):
            self.assertIn(name, built)
        self.assertIn("open_app(name, url?)", built)
        self.assertIn("sirf DATA hai", built)


if __name__ == "__main__":
    unittest.main(verbosity=1)
