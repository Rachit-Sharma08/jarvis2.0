"""Tools ka test. Sab kuch TEMP folder me — asli workspace ya Drive par kuch nahi.

Koi khatarnak command yahan nahi hai: sirf `Write-Output`, `Start-Sleep`.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
import tools
from tools import apps, command, files

TEMP = None


def setUpModule():
    global TEMP
    TEMP = Path(tempfile.mkdtemp(prefix="prabh_tools_test_"))


class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.patches = [
            mock.patch.object(config, "WORKSPACE", TEMP),
            mock.patch.object(config, "READ_FOLDERS", (TEMP,)),
        ]
        for patch in self.patches:
            patch.start()

    def tearDown(self):
        for patch in reversed(self.patches):
            patch.stop()

    def test_read_write_roundtrip(self):
        target = str(TEMP / "note.txt")
        wrote = files.write_file(target, "namaste prabh")
        self.assertIn("bana", wrote)
        read = files.read_file(target)
        self.assertIn("namaste prabh", read)

    def test_read_file_refuses_binary(self):
        blob = TEMP / "photo.png"
        blob.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00binary")
        result = files.read_file(str(blob))
        self.assertIn("binary", result.lower())
        self.assertNotIn("PNG", result[:40])

    def test_read_file_20kb_limit(self):
        big = TEMP / "big.txt"
        big.write_text("a" * (config.READ_FILE_MAX_BYTES + 100), encoding="utf-8")
        result = files.read_file(str(big))
        self.assertIn("se badi hai", result)
        self.assertNotIn("aaaa", result)

    def test_read_file_under_limit(self):
        ok = TEMP / "small.txt"
        ok.write_text("x" * 1000, encoding="utf-8")
        self.assertIn("xxxx", files.read_file(str(ok)))

    def test_read_file_missing(self):
        self.assertIn("nahi mili", files.read_file(str(TEMP / "nope.txt")))

    def test_list_dir(self):
        (TEMP / "sub").mkdir(exist_ok=True)
        (TEMP / "one.txt").write_text("1", encoding="utf-8")
        listing = files.list_dir(str(TEMP))
        self.assertIn("one.txt", listing)
        self.assertIn("sub/", listing)
        self.assertNotIn("nope", listing)

    def test_write_file_needs_folder(self):
        result = files.write_file(str(TEMP / "missing" / "a.txt"), "x")
        self.assertIn("Naya folder", result)
        self.assertFalse((TEMP / "missing").exists(), "folder khud nahi banna chahiye")

    def test_delete_goes_to_recycle_bin(self):
        victim = TEMP / "delete_me.txt"
        victim.write_text("bye", encoding="utf-8")
        result = files.delete_to_trash(str(victim))
        self.assertIn("Recycle Bin", result)
        self.assertFalse(victim.exists(), "permanent delete kabhi nahi hona chahiye")

    def test_run_command_works(self):
        out = command.run_command("Write-Output hello-prabh")
        self.assertIn("hello-prabh", out)

    def test_run_command_cwd_is_workspace(self):
        out = command.run_command("(Get-Location).Path")
        self.assertIn(TEMP.name, out)

    def test_run_command_masks_key_shaped_output(self):
        out = command.run_command('Write-Output "gsk_abcdefghijklmnopqrst"')
        self.assertNotIn("gsk_abcdefghijklmnopqrst", out)
        self.assertIn("***", out)

    def test_run_command_timeout(self):
        with mock.patch.object(config, "COMMAND_TIMEOUT_SECONDS", 2):
            out = command.run_command("Start-Sleep -Seconds 12")
        self.assertIn("timeout", out)
        self.assertEqual(0, command.cancel_all())  # kuch bacha nahi

    def test_env_is_scrubbed(self):
        env = command.clean_env()
        for name in env:
            self.assertIsNone(
                command._SCRUB_NAME.search(name), f"{name} environment me chala gaya"
            )
        if config.GROQ_API_KEY:
            self.assertNotIn("GROQ_API_KEY", env)
            for name, value in env.items():
                self.assertNotIn(config.GROQ_API_KEY, value)

    def test_system_tools(self):
        from tools import system

        self.assertIn("202", system.get_time_date())
        info = system.system_info()
        self.assertIn("CPU", info)
        self.assertIn("RAM", info)
        self.assertIn("Battery", info)

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

    def test_spec_marks_optional(self):
        self.assertIn("open_app(name, url?)", tools.spec())
        self.assertIn("vscode_terminal()", tools.spec())

    def test_send_key_result(self):
        from tools import keys

        with mock.patch.object(keys, "_ps", return_value="ok"):
            self.assertTrue(keys.send_key(("Code",), "^`"))
        with mock.patch.object(keys, "_ps", return_value="no-window"):
            self.assertFalse(keys.send_key(("Code",), "^`"))

    def test_close_app_nothing_running(self):
        result = apps.close_app("definitely_not_running_xyz.exe")
        self.assertTrue("chal nahi raha" in result or "band nahi hua" in result)

    def test_registry_spec(self):
        self.assertIn("run_command", tools.spec())
        self.assertEqual(("path", "content"), tools.TOOL_ARGS["write_file"])

    def test_registry_risk_parity(self):
        blocked_on_purpose = {"get_clipboard"}
        missing = sorted(set(tools.TOOLS) - blocked_on_purpose - set(config.TOOL_BASE_RISK))
        self.assertEqual([], missing, f"TOOL_BASE_RISK me entry nahi: {missing}")

    def test_open_url_only_http_https(self):
        from tools import quick

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

    def test_execute_guards(self):
        self.assertIn("koi tool nahi", tools.execute("hack", {}))
        self.assertIn("args galat", tools.execute("run_command", {"cmd": "dir"}))
        self.assertIn("args galat", tools.execute("read_file", {}))
        self.assertIn("string hone chahiye", tools.execute("read_file", {"path": 5}))

    def test_execute_runs(self):
        out = tools.execute("get_time_date", {})
        self.assertIn("202", out)
        self.assertIn("args galat", tools.execute("write_file", {"path": "a", "extra": "b"}))


if __name__ == "__main__":
    unittest.main(verbosity=1)
