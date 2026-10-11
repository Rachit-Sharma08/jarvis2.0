"""Quick clipboard/window helpers via PowerShell (local, safe)."""
import os
import subprocess
import webbrowser
from urllib.parse import urlparse


def _ps(cmd: str, timeout: int = 8) -> str:
    try:
        p = subprocess.run(
            ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        out = (p.stdout or '').strip()
        err = (p.stderr or '').strip()
        if err:
            return f'err: {err}'
        return out or '(ok)'
    except Exception as exc:
        return f'err: {type(exc).__name__}'


def copy_text(text: str = '') -> str:
    if not text or not str(text).strip():
        return 'Kya copy karun? (text do)'
    t = str(text).strip().replace("'", "''")
    return _ps(f'Set-Clipboard -Value \"{t}\"')


def get_clipboard() -> str:
    return _ps('Get-Clipboard')


def _web_url(url: str) -> str:
    """Wajah lautao ('' = theek hai). http/https + host; koi space/newline/control nahi.

    Ye check tools/apps.py (open_website) aur gatekeeper/rules.py
    (_open_website) me bhi hai — baad me ek hi jagah karenge.
    """
    text = str(url or "").strip()
    if not text:
        return "URL kya hai? (example: https://example.com)"
    if any(ch in text for ch in (" ", "\n", "\r", "\t")) or any(
        ord(ch) < 32 for ch in text
    ):
        return "URL me space/newline nahi chahiye"
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "sirf http/https link khulte hain"
    return ""


def open_url(url: str = '') -> str:
    bad = _web_url(url)
    if bad:
        return bad
    u = str(url).strip()
    try:
        opened = webbrowser.open(u)
    except Exception as exc:
        return f"err: {type(exc).__name__}"
    if opened:
        return f"browser me khul gaya: {u}"
    return "browser nahi khula"


def focus_app(name: str = '') -> str:
    if not name or not str(name).strip():
        return 'App ka naam kya hai? (example: chrome, notepad)'
    n = str(name).strip().replace("'", "''")
    return _ps(f'=Get-Process -Name \"{n}\" -ErrorAction SilentlyContinue; if(){{ (New-Object -ComObject Shell.Application).Windows() | Where-Object {{ .Name -match \"{n}\" }} | ForEach-Object {{ .Activate() }}; \"focused\" }} else {{ \"process nahi mila\" }}')
