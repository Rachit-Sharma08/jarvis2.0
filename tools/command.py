"""run_command — PowerShell, hamesha ASK ke baad.

- 30 second timeout, non-interactive, `shell=False`
- cwd = workspace
- environment SCRUBBED: jisme naam me KEY/TOKEN/SECRET/PASSWORD/CREDENTIAL ho
  ya jisme value koi asli API key ho, wo bahar nahi jaata
- output 2000 character tak + secrets mask karke
"""

import os
import re
import subprocess
import threading

import config
from gatekeeper.audit import _live_values, mask

_SCRUB_NAME = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.IGNORECASE)
_active = {}
_lock = threading.Lock()


def clean_env() -> dict:
    """Bina kisi key/secret wale variables ka environment."""
    env = {}
    for name, value in os.environ.items():
        if _SCRUB_NAME.search(name):
            continue
        if any(secret and secret in value for secret in _live_values()):
            continue
        env[name] = value
    return env


def run_command(command: str) -> str:
    if not str(command).strip():
        return "command khaali hai."

    started = subprocess.Popen(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", str(command)],
        cwd=str(config.ensure_workspace()),
        env=clean_env(),
        shell=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    with _lock:
        _active[started.pid] = started

    note = ""
    try:
        out, err = started.communicate(timeout=config.COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        started.kill()
        out, err = started.communicate()
        note = f"[{config.COMMAND_TIMEOUT_SECONDS}s par timeout — command rok diya]"
    finally:
        with _lock:
            _active.pop(started.pid, None)

    text = (out or "").strip()
    if err and err.strip():
        text = f"{text}\n[error] {err.strip()}".strip()
    if note:
        text = f"{note}\n{text}".strip()
    text = mask(text)[: config.TOOL_OUTPUT_LIMIT]
    return text or "(khaali output)"


def cancel_all() -> int:
    """STOP dabane par chalte hue commands band. Kitne band hue wapas deta hai."""
    with _lock:
        running = list(_active.values())
    for process in running:
        try:
            process.terminate()
        except Exception:
            pass
    return len(running)
