"""HUD window - **ek hi** window, har "Jarvis" par nahi.

Do raaste se khulta hai: app ke andar (wake + Ctrl+Alt+S,
`desktop/callbacks.py`) aur alag process me (Desktop shortcut / tray,
`desktop/open_hud.py`). Dono ka **ek hi** hissa yahi `HudWindow.open()` hai.

**Purana bug (R-2, 13-Oct):** har wake par nayi window khulti thi.
`_focus_existing()` `EnumWindows` se window dhoondta tha, par aakhir me
`return False` likha tha - "window mili" ka faisla **lapiset** ho jaata tha,
is liye `open()` hamesha naya browser chala deta tha. 4 wake = 4 window.

Ab pehle HUD ki window dhoondi jaati hai (`desktop/win_find.py` - title se,
process se nahi) aur **usi par le jaaya** jaata hai; sirf sach me na mile tab
nayi kholi jaati hai. Edge window 1-2 s me banata hai, is liye abhi-bani
window ka thoda intezaar bhi rakhta hai (`SPAWN_GRACE_SECONDS`) - warna do
jaldi wake se 2 window ban jaati hain.
"""

import subprocess
import sys
import time
from pathlib import Path

import config
from desktop.win_find import (bring_front, find_hud_window, hud_url,
                              still_open)
from log_setup import get_logger

log = get_logger('hud_window')

KILL_CMD = ["taskkill", "/F", "/T", "/PID"]

SPAWN_GRACE_SECONDS = 8.0      # itni der me dobara spawn nahi (Edge slow hai)


def url() -> str:
    return hud_url()


def command(exe: str, profile_dir: Path = None, target: str = "") -> list:
    """Browser ko chalaane ki command. Test me sirf yehi check hota hai —
    asal launch `HudWindow._spawn()` karta hai."""
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
    def __init__(self, exe: str = "", name: str = "", finder=None, spawner=None):
        self.exe = exe or config.browser_path()[0]
        self.name = name or config.browser_path()[1]
        self._proc = None
        self._hwnd = 0
        self._spawned_at = 0.0
        # `finder`/`spawner` test me fake daale ja sakte hain - asli Edge kabhi
        # nahi. Default asli `EnumWindows`-based dhoondhna hai.
        self._finder = finder or find_hud_window
        self._spawner = spawner

    def available(self) -> bool:
        return bool(self.exe) and Path(self.exe).is_file()

    def is_open(self) -> bool:
        """HUD ki window abhi khuli hai? Process se **nahi** puchh rahe - Edge
        `--app` launch par `Popen` ka process window bane se pehle hi mar
        sakta hai. Sirf window (title) pakka signal hai."""
        return bool(still_open(self._hwnd)) or bool(self._finder())

    def open(self) -> bool:
        """HUD kholo - par sirf **ek** window. Pehle khuli hai to usi par le
        jao. Wake, hotkey aur shortcut teeno ka yahi ek raasta hai."""
        if not self.available():
            log.error("Edge/Chrome nahi mila - HUD nahi khulega")
            return False
        if self.focus_existing():
            return True
        if self._opening():
            log.info("HUD abhi khul raha hai - doosri window nahi banayi")
            return True
        self._spawn()
        log.info("HUD khola: %s -> %s", self.name, url())
        return True

    def focus_existing(self) -> bool:
        """HUD pehle se khuli hai to usi par le jao. Naya window mat kholo.

        Pehle yeh hamesha `False` deta tha (bug) - is liye `open()` har baar
        naya browser chala deta tha. Test: `tests/test_desktop_hud_single.py`."""
        hwnd = still_open(self._hwnd) or int(self._finder() or 0)
        if not hwnd:
            return False
        self._hwnd = hwnd
        self._spawned_at = 0.0            # ab intezaar ki zarurat nahi
        bring_front(hwnd)
        log.info("HUD pehle se khuli thi - wahi par le gaya (hwnd=%s)", hwnd)
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
            self._hwnd = 0
            self._spawned_at = 0.0
        return True

    def _opening(self) -> bool:
        """Abhi-hi spawn kiya tha par window nahi dikhi (Edge ko der lagti
        hai). Isi der me dobara spawn = do window, is liye ruk jaate hain."""
        if not self._spawned_at:
            return False
        if time.monotonic() - self._spawned_at > SPAWN_GRACE_SECONDS:
            self._spawned_at = 0.0
            return False
        return True

    def _spawn(self):
        config.HUD_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        self._spawned_at = time.monotonic()
        if self._spawner is not None:
            self._proc = self._spawner(command(self.exe))
            return
        self._proc = subprocess.Popen(
            command(self.exe), shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=0x08000000,
        )


def main():
    h = HudWindow()
    h.open()


if __name__ == '__main__':
    sys.exit(main() if 'main' in globals() else 0)
