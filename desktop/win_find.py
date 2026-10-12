"""Windows se HUD window dhoondhna — sirf yeh ek kaam.

`desktop/hud_window.py` se alag is liye ki yahan **koi `subprocess` nahi**
hai. Sirf `ctypes` (`EnumWindows`) - matlab is file ko test me bina browser ke
chala sakte hain aur `HudWindow` ki file chhoti rehti hai (200-line niyam).

**Pakka signal title hai, process nahi.** Edge `--user-data-dir` wale launch
par `Popen` ka process window bane se **pehle** hi mar sakta hai (kaam dusre
browser process ko bhej deta hai), is liye process dekh kar "HUD khuli hai"
ka faisla galat hota hai. Window ka title sach me pakka hai.

Session ke **sab** top-level windows dekhte hain - is liye dusre process
(Desktop shortcut `desktop/open_hud.py`) se bhi sahi chalta hai.
"""

import ctypes
import ctypes.wintypes as wt

import config
from log_setup import get_logger

log = get_logger('win_find')

SW_RESTORE = 9                 # minimized window wapas normal dikhane ke liye

_USER32 = ctypes.windll.user32
_ENUMWINDOWS_PROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

# 64-bit par argtypes ke bina lParam/atatype kat-ta hai - chup-chaap bug.
_USER32.GetWindowTextLengthW.argtypes = [wt.HWND]
_USER32.GetWindowTextLengthW.restype = ctypes.c_int
_USER32.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
_USER32.GetWindowTextW.restype = ctypes.c_int
_USER32.IsWindow.argtypes = [wt.HWND]
_USER32.IsWindow.restype = ctypes.c_bool
_USER32.ShowWindow.argtypes = [wt.HWND, ctypes.c_int]
_USER32.ShowWindow.restype = ctypes.c_bool
_USER32.SetForegroundWindow.argtypes = [wt.HWND]
_USER32.SetForegroundWindow.restype = ctypes.c_bool


def hud_title() -> str:
    """Browser window ka title. `--app` me title **page** ka hota hai (URL
    nahi) - `ui/index.html` ka `<title>__PRABH_ASSISTANT_NAME__ HUD</title>`,
    jise `server/app.py` ka `fill_html()` bhar deta hai."""
    return f"{config.ASSISTANT_NAME} HUD"


def is_hud_title(text: str) -> bool:
    """Ye title HUD ki window ka hai? Pure function - browser ke bina test.

    Ache se pakadta hai: exact title (`Jarvis HUD`), ya URL (`--app` me title
    load ke dauran URL ho sakta hai), ya display naam (`J.A.R.V.I.S`).
    **Sirf 'Jarvis' nahi** - warna user ka apna tab bhi pakad lenge."""
    t = (text or "").strip()
    if not t:
        return False
    return t == hud_title() or hud_url() in t or config.DISPLAY_NAME in t


def hud_url() -> str:
    """HUD ka URL (`config` me hai - yahan duplicate mat karo)."""
    return config.SERVER_ORIGIN + config.HUD_PATH


def window_text(hwnd) -> str:
    """Window ka title ('' agar title hi na ho - Edge ke khali windows)."""
    length = _USER32.GetWindowTextLengthW(hwnd)
    if length < 1:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    _USER32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def find_hud_window() -> int:
    """HUD window ka hwnd - 0 agar abhi khuli nahi hai.

    Yahi se pata chalta hai ki HUD pehle se khuli hai ya nahi: `HudWindow.open()`
    pehle yeh puchhta hai, window mili to **usi par le jaata** hai.
    """
    found = 0

    def cb(hwnd, lparam):
        nonlocal found
        try:
            if is_hud_title(window_text(hwnd)):
                found = int(hwnd)
                return False            # EnumWindows yahin ruk jaata hai
        except Exception:
            pass
        return True

    try:
        _USER32.EnumWindows(_ENUMWINDOWS_PROC(cb), 0)
    except Exception as exc:
        log.warning("window list nahi mili: %s", exc)
    return found


def still_open(hwnd) -> int:
    """Ye hwnd abhi bhi zinda hai? -> wahi hwnd ya 0. (`IsWindow` - tez,
    `EnumWindows` se pehle wala tez raasta.)"""
    if not hwnd:
        return 0
    try:
        return int(hwnd) if _USER32.IsWindow(hwnd) else 0
    except Exception:
        return 0


def bring_front(hwnd) -> bool:
    """Window ko aage lao (minimized ho to wapas khada). Ye guarantee nahi
    ki screen par dikha - is liye return par koi faisla nahi, sirf log."""
    try:
        _USER32.ShowWindow(hwnd, SW_RESTORE)
        _USER32.SetForegroundWindow(hwnd)
        return True
    except Exception as exc:
        log.warning("HUD window (hwnd=%s) aage nahi la saka: %s", hwnd, exc)
        return False
