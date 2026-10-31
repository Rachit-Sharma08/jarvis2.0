"""Path-hardening ke tests (JARVIS_NO_CARDS / gatekeeper/nocards.py).

Sirf fakes + temp folder. Asli delete/app close nahi. Junction admin ke bina
ban sakta hai (`mklink /J`); fail ho to test skip.
"""

import os
import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from gatekeeper import nocards, paths
from tools import files as files_mod

# `.env` me JARVIS_TRUST=1 ho to path-hardening ka DENY dikhta hi nahi.
config.TRUST_ALL = False

TEMP = None
OUTSIDE = None


def setUpModule():
    global TEMP, OUTSIDE
    TEMP = Path(tempfile.mkdtemp(prefix="prabh_ncpath_in_"))
    OUTSIDE = Path(tempfile.mkdtemp(prefix="prabh_ncpath_out_"))


class NoCardsPathsTest(unittest.TestCase):
    def setUp(self):
        self.patches = [
            mock.patch.object(config, "WORKSPACE", TEMP),
            mock.patch.object(config, "READ_FOLDERS", (TEMP,)),
            mock.patch.object(config, "NO_CARDS", True),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()

    def ask(self, tool, args):
        return nocards.resolve_ask(tool, args)

    # ---- trailing dot/space / ADS ----
    def test_trailing_dot_space_denied(self):
        for name in ("payload.exe.", "payload.exe "):
            verdict, reason = self.ask(
                "write_file", {"path": str(TEMP / name), "content": "x"})
            self.assertEqual("DENY", verdict, f"{name!r} bypass ho gaya")
            self.assertIn("dot/space", reason)

    def test_ntfs_stream_cases_denied(self):
        cases = [
            r"evil.exe:stream",
            r"notes.txt:hidden",
            r"C:\x:stream",
            r"sub\a.txt:s",
        ]
        for raw in cases:
            verdict, _reason = self.ask(
                "write_file", {"path": str(TEMP / raw), "content": "x"})
            self.assertEqual("DENY", verdict, f"{raw!r} stream bypass ho gaya")

    def test_new_exec_suffixes_denied(self):
        for name in ("a.js", "a.hta", "a.com", "a.pif", "a.py", "a.url",
                     "a.appref-ms", "a.psm1"):
            verdict, _reason = self.ask(
                "write_file", {"path": str(TEMP / name), "content": "x"})
            self.assertEqual("DENY", verdict, f"{name} bypass ho gaya")

    # ---- workspace ke andar ALLOW ----
    def test_plain_names_allowed(self):
        for raw in ("a.txt", "sub\\b.md"):
            verdict, reason = self.ask(
                "write_file", {"path": str(TEMP / raw), "content": "x"})
            self.assertEqual("ALLOW", verdict, f"{raw} allow hona chahiye: {reason}")

    # ---- junction ----
    def test_junction_escape_denied(self):
        link = TEMP / "j"
        marker = OUTSIDE / "keep.txt"
        marker.write_text("bacha ke rakho", encoding="utf-8")
        make = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(OUTSIDE)],
            capture_output=True, text=True, timeout=30)
        if make.returncode != 0:
            self.skipTest(f"mklink /J fail: {(make.stderr or make.stdout).strip()[:60]}")
        try:
            verdict, reason = self.ask(
                "write_file", {"path": str(link / "x.txt"), "content": "x"})
            self.assertEqual("DENY", verdict, "junction se bahar likhna bypass ho gaya")
            self.assertIn("workspace", reason)
            verdict2, _r = self.ask("delete_to_trash", {"path": str(link)})
            self.assertEqual("DENY", verdict2, "junction delete bypass ho gaya")
            self.assertTrue(marker.exists(), "junction ke pare ki file ko chhua!")
        finally:
            if link.is_dir():
                subprocess.run(["cmd", "/c", "rmdir", str(link)],
                               capture_output=True, timeout=30)
            if marker.exists():
                marker.unlink()

    # ---- nocards ka ALLOW path == files.write_file ka asli path ----
    def test_allow_path_exact_match_with_files(self):
        (TEMP / "sub").mkdir(exist_ok=True)
        arg = str(TEMP / "sub" / "b.md")
        written = []
        real_write = files_mod.Path.write_text

        def spy_write(self, *a, **k):
            written.append(str(self))
            return real_write(self, *a, **k)

        verdict, reason = self.ask("write_file", {"path": arg, "content": "x"})
        self.assertEqual("ALLOW", verdict, reason)
        with mock.patch.object(files_mod.Path, "write_text", spy_write):
            files_mod.write_file(arg, "x")
        self.assertEqual(1, len(written), "asli likhne ka raasta dobara chala")
        self.assertEqual(str(paths.resolve(arg)), written[0],
                         "nocards ka ALLOW path aur files ka asli path alag hain")

    # ---- delete root ke teen roop ----
    def test_delete_root_forms_denied(self):
        for raw in (str(TEMP), str(TEMP) + "\\", str(TEMP / ".")):
            verdict, _reason = self.ask("delete_to_trash", {"path": raw})
            self.assertEqual("DENY", verdict, f"{raw!r} root delete bypass ho gaya")

    def test_reason_sanitized(self):
        verdict, reason = self.ask("open_app", {"name": "ev\x07il\x00name"})
        self.assertEqual("DENY", verdict)
        self.assertNotIn("\x07", reason)
        self.assertNotIn("\x00", reason)
        verdict, reason = self.ask("open_app", {"name": "a" * 80})
        self.assertEqual("DENY", verdict)
        self.assertLessEqual(len(reason), 40 + 36, "naam 40 char se lamba nikla")


if __name__ == "__main__":
    unittest.main(verbosity=1)
