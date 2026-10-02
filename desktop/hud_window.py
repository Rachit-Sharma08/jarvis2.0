"""HUD window — Edge/Chrome `--app` mode me ek native jaisa window.

`pywebview` nahi chuna: uske liye `pythonnet` + `clr_loader` + `bottle` +
`proxy_tools` chahiye, aur pythonnet CLR baaki packages se takra sakta hai.
`--app` mode me koi naya package nahi lagta, security model bilkul waisa hi
rehta hai — wahi `http://127.0.0.1:8000/`, wahi per-start token, wahi CSP.

Do window nahi honge: `--user-data-dir` ek apna (data/hud-profile) hai.
Browser ka apna singleton usi profile par kaam karta hai — doosri baar
`--app` bulao to naya window nahi banta, purana focus ho jaata hai aur
naya process khud exit ho jaata hai.

Tumhare normal browsing se alag profile = alag cookies, alag history.
"""

import subprocess
import sys
from pathlib import Path

import config
from log_setup import get_logger

log = get_logger("hud_window")

# Naya console window nahi khulna chahiye.
_NO_WINDOW = 0x08000000
_KILL = ["taskkill", "/T", "/F", "/PID"]


def url() -> str:
    return config.SERVER_ORIGIN + config.HUD_PATH


def command(exe: str, profile_dir: Path = None, target: str = "") -> list:
    """`--app` mode ka pura command. Test yahi list check karta hai."""
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
    """Ek window. `open()` idempotent hai — dobara `open()` sirf focus karega."""

    def __init__(self, exe: str = "", name: str = ""):
        self.exe = exe or config.browser_path()[0]
        self.name = name or config.browser_path()[1]
        self._proc = None

    def available(self) -> bool:
        return bool(self.exe) and Path(self.exe).is_file()

    def is_open(self) -> bool:
        """Best effort. Browser `--app` par ek 'starter' process bana kar asli
        process par chala jaata hai, is liye poll() jaldi hi None de sakta hai
        jabki window khuli hai. Isi liye `open()` par is par bharosa nahi —
        dobara spawn karna safe hai (browser focus kar deta hai)."""
        return self._proc is not None and self._proc.poll() is None

    def open(self) -> bool:
        """Window kholo. Pehle se khuli ho to sirf focus ho jaati hai. -> khuli"""
        if not self.available():
            log.error("Edge/Chrome nahi mila — HUD nahi khulega")
            return False
        self._spawn()
        log.info("HUD khola: %s -> %s", self.name, url())
        return True

    def close(self) -> bool:
        """Window aur uska poora browser process tree band karo."""
        if self._proc is None:
            return False
        pid = self._proc.pid
        try:
            subprocess.run(
                _KILL + [str(pid)], shell=False, capture_output=True,
                creationflags=_NO_WINDOW, timeout=10,
            )
            log.info("HUD band kiya (pid=%s)", pid)
        except (OSError, subprocess.SubprocessError) as exc:
            log.warning("HUD band nahi hua (pid=%s): %s", pid, exc)
        finally:
            self._proc = None
        return True

    def _spawn(self):
        config.HUD_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self._proc = subprocess.Popen(
            command(self.exe), shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=_NO_WINDOW,
        )


def main() -> int:
    """`python -m desktop.hud_window` — test/manual ke liye ek window kholo."""
    window = HudWindow()
    if not window.available():
        print("Edge ya Chrome nahi mila. Ek inme se install karo.")
        return 1
    print(f"HUD khul raha hai ({window.name}) -> {url()}")
    print("Band karne ke liye is window ko Ctrl+C se bhi rok sakte ho.")
    window.open()
    try:
        return window._proc.wait()
    except KeyboardInterrupt:
        window.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
