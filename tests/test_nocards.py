"""PRABH_NO_CARDS policy ka test - sirf fakes + temp folder.

Asli delete / app close / shell kuch nahi chalta: sirf `nocards.resolve_ask()`
ka faisla aur `keeper.review()` ka hook (executor yahan bulta hi nahi).
"""

import os
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from gatekeeper import keeper, nocards

TEMP = OUTSIDE = None


def setUpModule():
    global TEMP, OUTSIDE
    TEMP = Path(tempfile.mkdtemp(prefix="prabh_nocards_in_"))
    OUTSIDE = Path(tempfile.mkdtemp(prefix="prabh_nocards_out_"))


class NoCardsTest(unittest.TestCase):
    def setUp(self):
        self.patches = [
            mock.patch.object(config, "WORKSPACE", TEMP),
            mock.patch.object(config, "READ_FOLDERS", (TEMP,)),
            mock.patch.object(config, "NO_CARDS", True),
        ]
        for patch in self.patches:
            patch.start()
        keeper.LIMITER.set_enabled(True)

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()

    def ask(self, tool, args):
        return nocards.resolve_ask(tool, args)

    # ---- ALLOW ----
    def test_write_inside_workspace_allowed(self):
        verdict, reason = self.ask(
            "write_file", {"path": str(TEMP / "a.txt"), "content": "hi"})
        self.assertEqual("ALLOW", verdict, f"workspace ke andar likhna allow: {reason}")

    def test_delete_inside_workspace_allowed(self):
        verdict, reason = self.ask("delete_to_trash", {"path": str(TEMP / "a.txt")})
        self.assertEqual("ALLOW", verdict, f"workspace ke andar delete allow: {reason}")

    def test_delete_inside_subfolder_allowed(self):
        verdict, reason = self.ask("delete_to_trash", {"path": str(TEMP / "sub")})
        self.assertEqual("ALLOW", verdict, reason)

    # ---- write_file DENY ----
    def test_write_outside_workspace_denied(self):
        verdict, reason = self.ask(
            "write_file", {"path": str(OUTSIDE / "x.txt"), "content": "x"})
        self.assertEqual("DENY", verdict)
        self.assertIn("workspace", reason)

    def test_write_dotdot_denied(self):
        verdict, reason = self.ask(
            "write_file", {"path": str(TEMP / ".." / ".." / "x.txt"), "content": "x"})
        self.assertEqual("DENY", verdict)
        self.assertIn("..", reason)

    def test_write_unc_denied(self):
        verdict, reason = self.ask(
            "write_file", {"path": r"\\server\share\x.txt", "content": "x"})
        self.assertEqual("DENY", verdict)
        self.assertIn("UNC", reason)

    def test_write_ntfs_stream_denied(self):
        verdict, reason = self.ask("write_file", {"path": r"C:\x:stream", "content": "x"})
        self.assertEqual("DENY", verdict)
        self.assertIn("stream", reason)

    def test_write_dotenv_denied(self):
        verdict, reason = self.ask(
            "write_file", {"path": str(TEMP / ".env"), "content": "k=v"})
        self.assertEqual("DENY", verdict)
        self.assertIn("secret", reason)

    def test_write_git_path_denied(self):
        verdict, reason = self.ask(
            "write_file", {"path": str(TEMP / ".git" / "config"), "content": "x"})
        self.assertEqual("DENY", verdict)
        self.assertIn(".git", reason)

    def test_write_executable_suffixes_denied(self):
        for name in ("a.exe", "a.bat", "a.ps1", "a.reg"):
            verdict, _reason = self.ask("write_file", {"path": str(TEMP / name), "content": "x"})
            self.assertEqual("DENY", verdict, f"{name} block hona chahiye tha")

    def test_write_secret_style_names_denied(self):
        for name in ("id_rsa", "server.pem", "tls.key"):
            verdict, _reason = self.ask("write_file", {"path": str(TEMP / name), "content": "x"})
            self.assertEqual("DENY", verdict, f"{name} block hona chahiye tha")

    def test_symlink_escape_denied(self):
        link = TEMP / "link"
        try:
            os.symlink(str(OUTSIDE), str(link), target_is_directory=True)
        except OSError:
            self.skipTest("symlink ban nahi paya (permission) - junction raasta skip")
        try:
            verdict, reason = self.ask("write_file", {"path": str(link / "x.txt"), "content": "x"})
            self.assertEqual("DENY", verdict, reason)
            self.assertIn("workspace", reason)
        finally:
            if link.is_symlink():
                link.unlink()

    def test_delete_outside_denied(self):
        verdict, reason = self.ask("delete_to_trash", {"path": str(OUTSIDE / "x")})
        self.assertEqual("DENY", verdict)
        self.assertIn("workspace", reason)

    def test_delete_workspace_root_denied(self):
        verdict, reason = self.ask("delete_to_trash", {"path": str(TEMP)})
        self.assertEqual("DENY", verdict)
        self.assertIn("root", reason)

    def test_delete_executable_denied(self):
        verdict, _reason = self.ask("delete_to_trash", {"path": str(TEMP / "a.exe")})
        self.assertEqual("DENY", verdict)

    def test_close_app_denied_even_allowed_name(self):
        verdict, reason = self.ask("close_app", {"name": "notepad"})
        self.assertEqual("DENY", verdict)
        self.assertIn("close_app", reason)

    def test_close_app_protected_denied(self):
        verdict, reason = self.ask("close_app", {"name": "explorer"})
        self.assertEqual("DENY", verdict)
        self.assertIn("allowed nahi", reason)

    def test_run_command_denied(self):
        verdict, reason = self.ask("run_command", {"command": "Get-Date"})
        self.assertEqual("DENY", verdict)
        self.assertIn("shell command", reason)

    def test_read_outside_denied(self):
        verdict, reason = self.ask("read_file", {"path": str(OUTSIDE / "a.txt")})
        self.assertEqual("DENY", verdict)
        self.assertIn("allowed list", reason)

    def test_list_dir_outside_denied(self):
        verdict, _reason = self.ask("list_dir", {"path": str(OUTSIDE)})
        self.assertEqual("DENY", verdict)

    def test_read_secret_name_denied(self):
        verdict, reason = self.ask("read_file", {"path": str(OUTSIDE / "id_rsa")})
        self.assertEqual("DENY", verdict)
        self.assertIn("secret", reason)

    def test_open_app_outside_list_denied(self):
        verdict, reason = self.ask("open_app", {"name": "steam"})
        self.assertEqual("DENY", verdict)
        self.assertIn("allowed apps", reason)

    def test_unknown_tool_denied(self):
        verdict, reason = self.ask("send_email", {"to": "a@b.c"})
        self.assertEqual("DENY", verdict)
        self.assertIn("allowed nahi", reason)

    def test_review_allow_without_card(self):
        verdict, reason = keeper.review(
            "write_file", {"path": str(TEMP / "a.txt"), "content": "hi"}, "sunday")
        self.assertEqual("allow", verdict, reason)
        self.assertFalse(keeper.APPROVALS.busy(), "no-cards me card nahi banna chahiye")

    def test_review_deny_without_card(self):
        verdict, reason = keeper.review(
            "write_file", {"path": str(OUTSIDE / "x.txt"), "content": "x"}, "sunday")
        self.assertEqual("deny", verdict)
        self.assertIn("workspace", reason)
        self.assertFalse(keeper.APPROVALS.busy(), "no-cards me card nahi banna chahiye")

    def test_flag_off_card_comes_back(self):
        with mock.patch.object(config, "NO_CARDS", False):
            verdict, payload = keeper.review(
                "write_file", {"path": str(TEMP / "a.txt"), "content": "hi"}, "sunday")
        self.assertEqual("ask", verdict)
        self.assertIsNotNone(payload)
        self.assertIsNotNone(keeper.APPROVALS.current())
        keeper.APPROVALS.cancel()


if __name__ == "__main__":
    unittest.main(verbosity=1)
