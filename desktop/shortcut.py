"""Desktop ka "Jarvis HUD" shortcut - banao ya hatao.

Tray icon Windows ke overflow `^` me chhup jaata hai (ye Windows ka normal
behaviour hai, pystray ki galti nahi). Is liye tray ke alawa **ek aur**
raasta chahiye - aapke desktop par ek shortcut.

`.lnk` banane ke liye koi package nahi: Windows ka apna `WScript.Shell`
(`desktop/hud_shortcut.ps1` se) `.lnk` likhta hai. Script alag file me hai taaki
PowerShell ki quoting se koi jhanjhat na ho.

Ek hi raasta: `python -m desktop.shortcut install|remove|status`.
Shortcut `python -m desktop.open_hud` chalaata hai - yahi wahi raasta hai jo
global hotkey bhi chalata hai.

**Is file me registry ka koi kaam nahi.** Login par auto-start alag raasta
hai (`config_desktop.AUTOSTART_*`), aur wo tabhi likha jaata hai jab user
manually "haan" bole.
"""

import os
import subprocess
import sys
from pathlib import Path

import config
from log_setup import get_logger

log = get_logger("shortcut")

_NO_WINDOW = 0x08000000          # naya console window na khule
_TIMEOUT = 20

# Desktop ka asli path registry se - OneDrive wale PC par `Path.home()/Desktop`
# galat hota hai. Test me ye function inject karke temp dir dete hain.
_FOLDER_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"


def desktop_dir() -> Path:
    """Asli Desktop folder (OneDrive redirect samet kar)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _FOLDER_KEY) as key:
            raw = winreg.QueryValueEx(key, "Desktop")[0]
        return Path(os.path.expandvars(raw))
    except (OSError, ImportError):
        return Path(os.path.expanduser("~")) / "Desktop"


def link_path(name: str = "", folder: Path = None) -> Path:
    return Path(folder or desktop_dir()) / f"{name or config.HUD_SHORTCUT_NAME}.lnk"


def script() -> Path:
    return Path(__file__).resolve().with_name("hud_shortcut.ps1")


def target() -> str:
    """`pythonw.exe` - console na dikhe. Na ho to `python.exe`."""
    exe = Path(sys.executable).with_name("pythonw.exe")
    return str(exe if exe.is_file() else Path(sys.executable))


def description() -> str:
    return "%s ka HUD window kholo (server chalu hona chahiye)" % config.ASSISTANT_NAME


def command(mode: str, link: Path = None, script_path: Path = None,
            exe: str = "", work_dir: str = "") -> list:
    """Poora PowerShell command. Test yahi list check karta hai - script kabhi
    chalti nahi. `shell=False` (AGENTS ka niyam)."""
    return [
        "powershell.exe", "-NoProfile", "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", str(script_path or script()),
        "-Mode", mode,
        "-Link", str(link or link_path()),
        "-Target", exe or target(),
        "-ArgLine", "-m desktop.open_hud",
        "-WorkDir", work_dir or str(config.BASE_DIR),
        "-Icon", config.browser_path()[0],
        "-Desc", description(),
    ]


def run(mode: str, folder: Path = None) -> tuple:
    """-> (ok, reason). Reason user ko dikhne layak Hinglish/English."""
    link = link_path(folder=folder)
    try:
        done = subprocess.run(
            command(mode, link), shell=False, capture_output=True, text=True,
            creationflags=_NO_WINDOW, timeout=_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log.error("shortcut %s nahi hua: %s", mode, exc)
        return False, str(exc)
    out = (done.stdout or "").strip().lower()
    if done.returncode != 0:
        reason = (done.stderr or "PowerShell error").strip().splitlines()[-1]
        log.error("shortcut %s fail: %s", mode, reason)
        return False, reason
    log.info("shortcut %s: %s (%s)", mode, out or "ok", link)
    return True, out or "ok"


def install(folder: Path = None) -> tuple:
    return run("install", folder)


def remove(folder: Path = None) -> tuple:
    return run("remove", folder)


def status(folder: Path = None) -> tuple:
    return run("status", folder)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    action = argv[0] if argv else "status"
    if action not in ("install", "remove", "status"):
        print("Sirf ye chal sakta hai: install | remove | status")
        return 1
    ok, reason = {"install": install, "remove": remove, "status": status}[action]()
    print(f"{config.ASSISTANT_NAME} HUD shortcut {action}: {reason}")
    return 0 if ok or reason == "missing" else 1


if __name__ == "__main__":
    sys.exit(main())