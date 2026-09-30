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


def _target(name: str) -> str:
    return config.ALLOWED_APPS.get(str(name).strip().lower(), str(name).strip())


def open_app(name: str) -> str:
    target = _target(name)
    exe = shutil.which(target) or (target if os.path.isfile(target) else "")
    if not exe:
        return f"{target} is PC par nahi mila."
    subprocess.Popen([exe], cwd=str(config.ensure_workspace()), shell=False)
    return f"{target} khol diya."


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
