"""App aur website tools.

- open_app: sirf config.ALLOWED_APPS me SAFE, baaki ASK
- open_website: sirf http/https, baaki scheme BLOCKED
- close_app: hamesha ASK
"""

import os
import shutil
import subprocess
import webbrowser
from urllib.parse import urlparse

import config
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


def open_website(url: str) -> str:
    parsed = urlparse(str(url))
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "sirf http ya https link khul sakta hai."
    webbrowser.open(str(url))
    return f"browser me khul gaya: {parsed.scheme}://{parsed.netloc}"


def close_app(name: str) -> str:
    target = _target(name)
    result = subprocess.run(
        ["taskkill", "/IM", target, "/F"],
        cwd=str(config.ensure_workspace()),
        shell=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    out = (result.stdout or "") + (result.stderr or "")
    lines = [line.strip() for line in out.splitlines() if line.strip()]
    if result.returncode == 0:
        return f"{target} band kar diya. {lines[-1] if lines else ''}".strip()
    if "not found" in out or "No running instance" in out:
        return f"{target} to pehle se chal nahi raha tha."
    return f"{target} band nahi hua: {' '.join(lines[:2])}"
