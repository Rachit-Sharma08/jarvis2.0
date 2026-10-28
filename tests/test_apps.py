"""Apps + browser khulne ke tool ka test (test_tools.py se 28-Oct aaye).

Koi app asli me khulti nahi — sirf fakes/deny raaste.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import os
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tools import apps, closeall, keys, quick


class AppsTest(unittest.TestCase):
    def test_website_only_http(self):
        self.assertIn("sirf http", apps.open_website("file:///C:/Windows/win.ini"))
        self.assertIn("sirf http", apps.open_website("javascript:alert(1)"))

    def test_app_not_found_is_safe(self):
        result = apps.open_app("definitely_not_an_app_xyz")
        self.assertIn("nahi mila", result)

    def test_app_paths_registry(self):
        class FakeKey:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        fake = mock.Mock()
        fake.HKEY_CURRENT_USER = "hkcu"
        fake.HKEY_LOCAL_MACHINE = "hklm"
        fake.OpenKey.side_effect = [OSError(), FakeKey()]
        fake.QueryValueEx.return_value = (r"C:\Brave\brave.exe", 1)
        with mock.patch.object(apps, "winreg", fake), \
                mock.patch.object(apps.os.path, "isfile", return_value=True):
            self.assertEqual(r"C:\Brave\brave.exe", apps._app_paths("brave.exe"))
        self.assertEqual(2, fake.OpenKey.call_count)

    def test_find_uses_app_paths(self):
        with mock.patch.object(apps.shutil, "which", return_value=None), \
                mock.patch.object(apps.os.path, "isfile", return_value=False), \
                mock.patch.object(apps, "_app_paths",
                                  return_value=r"C:\Brave\brave.exe"):
            self.assertEqual(r"C:\Brave\brave.exe", apps._find("brave.exe"))

    def test_open_app_passes_url(self):
        calls = []
        with mock.patch.object(apps, "_find", return_value=r"C:\Brave\brave.exe"), \
                mock.patch.object(apps.subprocess, "Popen",
                                  side_effect=lambda argv, **kw: calls.append(argv)):
            out = apps.open_app("brave", "https://www.youtube.com/watch?v=abc")
        self.assertEqual([[r"C:\Brave\brave.exe",
                           "https://www.youtube.com/watch?v=abc"]], calls)
        self.assertIn("khol diya", out)

    def test_open_app_rejects_bad_url(self):
        with mock.patch.object(apps, "_find", return_value="brave.exe"), \
                mock.patch.object(apps.subprocess, "Popen") as popen:
            out = apps.open_app("brave", "file:///C:/Windows/win.ini")
        self.assertIn("sirf http", out)
        popen.assert_not_called()

    def test_execute_fills_optional_arg(self):
        import tools

        seen = {}

        def fake(name, url=""):
            seen.update(name=name, url=url)
            return "ok"

        with mock.patch.dict(tools.TOOLS, {"open_app": fake}):
            self.assertEqual("ok", tools.execute("open_app", {"name": "brave"}))
        self.assertEqual({"name": "brave", "url": ""}, seen)

    def test_vscode_terminal_no_window(self):
        with mock.patch.object(apps, "send_key", return_value=False):
            self.assertIn("nahi mili", apps.vscode_terminal())

    def test_vscode_terminal_sends_ctrl_backtick(self):
        calls = []
        with mock.patch.object(apps, "send_key",
                               side_effect=lambda names, key: calls.append((names, key)) or True):
            self.assertIn("terminal khol diya", apps.vscode_terminal())
        self.assertEqual([(("Code",), "^`")], calls)

    def test_send_key_result(self):
        with mock.patch.object(keys, "_ps", return_value="ok"):
            self.assertTrue(keys.send_key(("Code",), "^`"))
        with mock.patch.object(keys, "_ps", return_value="no-window"):
            self.assertFalse(keys.send_key(("Code",), "^`"))

    def test_open_url_only_http_https(self):
        opened = []

        def fake_open(url, *args, **kwargs):
            opened.append(url)
            return True

        blocked = ["file:///C:/x", "javascript:alert(1)", "ms-settings:display",
                   "ftp://x.com", "//host/path", "", "https://", "https://a.com\nb"]
        with mock.patch.object(quick, "webbrowser") as fake_wb:
            fake_wb.open = fake_open
            for url in blocked:
                result = quick.open_url(url)
                self.assertNotIn("browser me khul gaya", result,
                                 f"{url!r} block hona chahiye tha")
            self.assertEqual([], opened, "blocked URL browser ko ja hi nahi sakta")
            quick.open_url("https://example.com")
            quick.open_url("http://example.com")
        self.assertEqual(["https://example.com", "http://example.com"], opened)


class CloseAllTest(unittest.TestCase):
    """`all` ka faisla pure hai - test me koi asli app band nahi hota."""

    def test_system_aur_khud_nahi(self):
        pairs = [(1, "chrome.exe"), (2, "explorer.exe"), (3, "python.exe"),
                 (4, "notepad.exe"), (5, "chrome.exe"), (6, "")]
        self.assertEqual(["chrome", "notepad"], closeall.closable(pairs))

    def test_apna_pid_nahi(self):
        self.assertEqual([], closeall.closable([(os.getpid(), "someapp.exe")]))

    def test_image_me_exe(self):
        self.assertEqual("notepad.exe", apps._image("notepad"))
        self.assertEqual("definitely_not_running_xyz.exe",
                         apps._image("definitely_not_running_xyz"))

    def test_sab_par_close_all(self):
        with mock.patch.object(closeall, "close_all", return_value="ok") as all_:
            self.assertEqual("ok", apps.close_app("sab"))
        all_.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=1)
