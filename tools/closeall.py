"""`close_app(name="all")` ka hissa — kaun window khuli hai, kise chhodna hai.

Sirf `tools/apps.py` yahan aata hai (200-line niyam). Yahan app kholna/band
karna nahi, sirf "sab" ka faisla hai: `closable()` pure hai, is liye test me
koi asli process/speaker nahi chhoota.
"""

import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import time

import psutil

import config
from desktop.win_find import window_text

_USER32 = ctypes.windll.user32
_ENUM_PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)
_USER32.IsWindowVisible.argtypes = [wt.HWND]
_USER32.IsWindowVisible.restype = ctypes.c_bool
_USER32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]
_USER32.GetWindowThreadProcessId.restype = wt.DWORD

# "sab band" me ye kabhi nahi: system shell, security, aur khud Jarvis ka python.
# Explorer band = taskbar gayab, is liye wo bhi nahi.
_KEEP = {
    "explorer", "winlogon", "csrss", "services", "lsass", "system", "smss",
    "dwm", "sihost", "taskhostw", "fontdrvhost", "registry", "audiodg",
    "searchhost", "startmenuexperiencehost", "shellexperiencehost",
    "textinputhost", "lockapp", "securityhealthsystray", "python", "pythonw",
}

ALL_WORDS = {"all", "sab", "sabhi", "saare", "sab kuch", "all apps",
             "sab apps", "saare apps", "everything"}


def kill(args: list):
    return subprocess.run(
        ["taskkill", *args],
        cwd=str(config.ensure_workspace()),
        shell=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


def window_pids() -> list:
    """Dikhne wali top-level window wale PID (ek-ek baar)."""
    pids = []

    def cb(hwnd, lparam):
        try:
            if _USER32.IsWindowVisible(hwnd) and window_text(hwnd):
                pid = wt.DWORD()
                _USER32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value and pid.value not in pids:
                    pids.append(pid.value)
        except Exception:
            pass
        return True

    try:
        _USER32.EnumWindows(_ENUM_PROC(cb), 0)
    except Exception:
        pass
    return pids


def process_names() -> list:
    """(pid, exe) — sirf jinke apne dikhne wale window hain."""
    pairs = []
    for pid in window_pids():
        try:
            pairs.append((pid, psutil.Process(pid).name()))
        except Exception:
            continue
    return pairs


def closable(pairs) -> list:
    """(pid, exe) -> band karne layak naam (bina .exe). Pure — test me process nahi."""
    mine = os.getpid()
    names = []
    for pid, name in pairs:
        low = str(name or "").strip().lower()
        if low.endswith(".exe"):
            low = low[:-4]
        if pid == mine or not low or low in _KEEP or low in names:
            continue
        names.append(low)
    return names


def close_all() -> str:
    names = closable(process_names())
    if not names:
        return "band karne ke liye koi app khula nahi tha."
    kill([arg for name in names for arg in ("/IM", name + ".exe")])
    left = set(names)
    for _ in range(6):              # WM_CLOSE async hai - 3 s tak asli haal dekho
        time.sleep(0.5)
        left &= set(closable(process_names()))
        if not left:
            break
    if left:
        return (f"{len(names) - len(left)} app band; abhi bhi khula: "
                f"{', '.join(sorted(left)[:5])} (save ka prompt aaya ho to usi par haan dabao).")
    return f"{len(names)} app band kar diye: {', '.join(names[:6])}."
