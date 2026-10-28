"""App aur website tools.

- open_app: sirf config.ALLOWED_APPS me SAFE, baaki ASK
- open_website: sirf http/https, baaki scheme BLOCKED
- close_app: graceful band (WM_CLOSE, jaisa window ka X). `name="all"` =
  saare khule app ek saath. Force kill sirf tab jab app normal band hone se
  na maane. ASK ka faisla `gatekeeper/nocards.py` deta hai.
"""

import os
import shutil
import subprocess
import webbrowser
from urllib.parse import urlparse

import config
from tools import closeall
from tools.keys import send_key
from tools.quick import _web_url

try:
    import winreg
except ImportError:  # Windows ke bahar
    winreg = None


def _target(name: str) -> str:
    return config.ALLOWED_APPS.get(str(name).strip().lower(), str(name).strip())


def _app_paths(exe: str) -> str:
    """Windows App Paths registry se exe dhoondo — PATH me na ho to bhi.

    Brave isi jagah milta hai (`HKLM\\...\\App Paths\\brave.exe`), PATH me nahi.
    """
    if winreg is None:
        return ""
    key = rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{exe}"
    for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(root, key) as handle:
                path, _ = winreg.QueryValueEx(handle, "")
        except OSError:
            continue
        if path and os.path.isfile(path):
            return path
    return ""


def _find(target: str) -> str:
    return (shutil.which(target) or (target if os.path.isfile(target) else "")
            or _app_paths(target))


def open_app(name: str, url: str = "") -> str:
    target = _target(name)
    exe = _find(target)
    if not exe:
        return f"{target} is PC par nahi mila."
    args = [exe]
    if str(url or "").strip():
        bad = _web_url(url)
        if bad:
            return bad
        args.append(str(url).strip())
    subprocess.Popen(args, cwd=str(config.ensure_workspace()), shell=False)
    return f"{target} khol diya." + (f" {args[-1]}" if len(args) > 1 else "")


def vscode_terminal() -> str:
    """Khuli VS Code window me terminal (Ctrl+`) kholo."""
    if not send_key(("Code",), "^`"):
        return "VS Code window nahi mili (pehle kholo)."
    return "VS Code me terminal khol diya."


def open_website(url: str) -> str:
    parsed = urlparse(str(url))
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "sirf http ya https link khul sakta hai."
    webbrowser.open(str(url))
    return f"browser me khul gaya: {parsed.scheme}://{parsed.netloc}"


def _image(target: str) -> str:
    """taskkill ko image naam chahiye (`notepad.exe`, `notepad` nahi)."""
    raw = target if target.lower().endswith(".exe") else f"{target}.exe"
    found = _find(raw) or _find(target)
    return os.path.basename(found) if found else raw


def _close_one(name: str) -> str:
    image = _image(_target(name))
    result = closeall.kill(["/IM", image])
    out = (result.stdout or "") + (result.stderr or "")
    low = out.lower()
    if result.returncode == 0:
        return f"{image} band kar diya."
    if "not found" in low or "no running instance" in low:
        return f"{image} to pehle se chal nahi raha tha."
    if "could not be terminated" in low or "forcefully" in low:
        forced = closeall.kill(["/IM", image, "/F"])
        if forced.returncode == 0:
            return f"{image} force band kiya (normal close se nahi maana)."
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    return f"{image} band nahi hua: {' '.join(lines[:2])[:160]}"


def close_app(name: str) -> str:
    """App band karo. `all` = saare khule app + browser tabs (system chhod ke)."""
    text = str(name).strip()
    if text.lower() in closeall.ALL_WORDS:
        return closeall.close_all()
    return _close_one(text)
