"""Quick clipboard/window helpers via PowerShell (local, safe)."""
import os
import subprocess


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


def open_url(url: str = '') -> str:
    if not url or not str(url).strip():
        return 'URL kya hai? (example: https://example.com)'
    u = str(url).strip().replace("'", "''")
    return _ps(f'Start-Process \"{u}\"')


def focus_app(name: str = '') -> str:
    if not name or not str(name).strip():
        return 'App ka naam kya hai? (example: chrome, notepad)'
    n = str(name).strip().replace("'", "''")
    return _ps(f'=Get-Process -Name \"{n}\" -ErrorAction SilentlyContinue; if(){{ (New-Object -ComObject Shell.Application).Windows() | Where-Object {{ .Name -match \"{n}\" }} | ForEach-Object {{ .Activate() }}; \"focused\" }} else {{ \"process nahi mila\" }}')
