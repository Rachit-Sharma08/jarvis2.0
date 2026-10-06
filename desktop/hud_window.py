import subprocess
import sys
from pathlib import Path
import ctypes
import ctypes.wintypes as wt

import config
from log_setup import get_logger

log = get_logger('hud_window')

KILL_CMD = ["taskkill", "/F", "/T", "/PID"]

_USER32 = ctypes.windll.user32
_KERNEL32 = ctypes.windll.kernel32
_ENUMWINDOWS_PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)


def url() -> str:
    return config.SERVER_ORIGIN + config.HUD_PATH


def command(exe: str, profile_dir: Path = None, target: str = "") -> list:
    profile = Path(profile_dir or config.HUD_PROFILE_DIR)
    return [
        exe,
        f"--app={target or url()}",
        f"--user-data-dir={profile}",
        f"--window-size={config.HUD_WIDTH},{config.HUD_HEIGHT}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-features=Translate,MediaRouter",
        "--disable-background-networking",
    ]


class HudWindow:
    def __init__(self, exe: str = "", name: str = ""):
        self.exe = exe or config.browser_path()[0]
        self.name = name or config.browser_path()[1]
        self._proc = None

    def available(self) -> bool:
        return bool(self.exe) and Path(self.exe).is_file()

    def is_open(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def open(self) -> bool:
        if not self.available():
            log.error("Edge/Chrome nahi mila - HUD nahi khulega")
            return False
        if self._focus_existing():
            log.info("HUD focus kiya")
            return True
        self._spawn()
        log.info("HUD khola: %s -> %s", self.name, url())
        return True

    def close(self) -> bool:
        if self._proc is None:
            return False
        pid = self._proc.pid
        try:
            subprocess.run(
                KILL_CMD + [str(pid)], shell=False, capture_output=True,
                creationflags=0x08000000, timeout=10,
            )
            log.info("HUD band kiya (pid=%s)", pid)
        except Exception as exc:
            log.warning("HUD band nahi hua (pid=%s): %s", pid, exc)
        finally:
            self._proc = None
        return True

    def _spawn(self):
        config.HUD_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self._proc = subprocess.Popen(
            command(self.exe), shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=0x08000000,
        )

    def _focus_existing(self):
        target = url()
        def cb(hwnd, lparam):
            try:
                length = _USER32.GetWindowTextLengthW(hwnd)
                if length < 1:
                    return True
                buf = ctypes.create_unicode_buffer(length + 1)
                _USER32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if target in title or 'Jarvis' in title or config.DISPLAY_NAME in title:
                    try:
                        _USER32.SetForegroundWindow(hwnd)
                        _USER32.ShowWindow(hwnd, 9)
                        return False
                    except Exception:
                        pass
            except Exception:
                pass
            return True
        try:
            _USER32.EnumWindows(_ENUMWINDOWS_PROC(cb), 0)
        except Exception:
            pass
        return False


def main():
    h = HudWindow()
    h.open()


if __name__ == '__main__':
    sys.exit(main() if 'main' in globals() else 0)
