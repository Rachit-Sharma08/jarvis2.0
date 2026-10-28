"""Personal profile (`core/profile.py` + `remember`/`forget` tool) - isolated data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401

import unittest

import config
import tools
from brain import prompt
from core import memory, modes, profile
from datasafe import isolated_data


class ProfileTest(unittest.TestCase):
    def setUp(self):
        self._ctx = isolated_data()
        self.data_dir = self._ctx.__enter__()
        memory.MEM.clear()

    def tearDown(self):
        memory.MEM.clear()
        self._ctx.__exit__(None, None, None)

    def test_remember_persists(self):
        self.assertIn("Yaad rakh liya", profile.remember("User Name", "Rachit"))
        self.assertEqual({"user_name": "Rachit"}, profile.load())
        self.assertIn("Rachit", profile.block())

    def test_same_key_updates(self):
        profile.remember("city", "Delhi")
        profile.remember("city", "Noida")
        self.assertEqual({"city": "Noida"}, profile.load())

    def test_forget(self):
        profile.remember("city", "Delhi")
        self.assertIn("Bhula diya", profile.forget("city"))
        self.assertEqual({}, profile.load())
        self.assertIn("tha hi nahi", profile.forget("city"))

    def test_sanitize(self):
        profile.remember("note", "line1\nline2\tline3")
        self.assertEqual("line1 line2 line3", profile.load()["note"])
        profile.remember("long", "x" * 500)
        self.assertEqual(profile.MAX_VALUE, len(profile.load()["long"]))
        self.assertIn("dono chahiye", profile.remember("", "value"))

    def test_cap(self):
        for index in range(profile.MAX_FACTS):
            profile.remember(f"k{index}", "v")
        self.assertIn("Profile full", profile.remember("extra", "v"))
        self.assertNotIn("extra", profile.load())

    def test_empty_block(self):
        self.assertEqual("", profile.block())

    def test_profile_in_prompt(self):
        self.assertEqual("", profile.block())
        self.assertNotIn("user_name: Rachit",
                         prompt.build(modes.persona_for("sunday"), True))
        profile.remember("user_name", "Rachit")
        built = prompt.build(modes.persona_for("sunday"), True)
        self.assertIn("user_name: Rachit", built)

    def test_tool_wired(self):
        self.assertIn("remember", tools.visible())
        out = tools.execute("remember", {"key": "city", "value": "Delhi"})
        self.assertIn("Yaad rakh liya", out)
        self.assertEqual("Delhi", profile.load()["city"])

    def test_profile_file_is_tmp(self):
        profile.remember("x", "y")
        self.assertNotEqual(Path(config.BASE_DIR) / "data", profile.PFILE.parent)

    def test_brief_uses_name(self):
        from tools import brief

        self.assertIn(", Sir", brief.daily_brief())
        self.assertNotIn("Rachit", brief.daily_brief())
        profile.remember("user_name", "Rachit")
        self.assertIn("Rachit Sir", brief.daily_brief())

    def test_nocards_allows(self):
        from unittest import mock

        from gatekeeper import nocards

        with mock.patch.object(config, "TRUST_ALL", False):
            verdict, reason = nocards.resolve_ask("remember", {"key": "a", "value": "b"})
        self.assertEqual("ALLOW", verdict, reason)


if __name__ == "__main__":
    unittest.main(verbosity=1)
