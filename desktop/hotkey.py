"""Global hotkey (default Ctrl+Alt+S) - HUD kholne ka dusra raasta.

Tray icon Windows ke overflow `^` me chhup jaata hai, is liye system-wide
hotkey zaroori tha. Ye `RegisterHotKey` se banta hai: koi naya package nahi,
sirf `ctypes`. Fail ho to sirf log - app chalti rehti hai, aur app band ho to
key apne aap free ho jaati hai.

**Register + pump + unregister EK HI thread par** (pakkaura): `hWnd=NULL`
hone se `WM_HOTKEY` usi thread ki queue me aata hai jisne `RegisterHotKey`
call kiya. Do alag thread = key kabhi trigger hi nahi hogi.
"""

import ctypes
import threading
from ctypes import wintypes

from log_setup import get_logger

log = get_logger("hotkey")

# ---- Windows ke constants (MSDN ke hisaab se) ----
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN = 0x0001, 0x0002, 0x0004, 0x0008
WM_HOTKEY, PM_REMOVE, HOTKEY_ID = 0x0312, 0x0001, 0x5150  # 'QP' - koi app se takra nahi

_MODS = {"alt": MOD_ALT, "option": MOD_ALT, "ctrl": MOD_CONTROL,
         "control": MOD_CONTROL, "shift": MOD_SHIFT, "win": MOD_WIN,
         "windows": MOD_WIN, "cmd": MOD_WIN, "super": MOD_WIN}
_NAMES = {MOD_CONTROL: "Ctrl", MOD_ALT: "Alt", MOD_SHIFT: "Shift", MOD_WIN: "Win"}
_SPECIAL = {"space": 0x20, "esc": 0x1B, "escape": 0x1B, "enter": 0x0D, "return": 0x0D,
            "tab": 0x09, "backspace": 0x08, "delete": 0x2E, "insert": 0x2D, "home": 0x24,
            "end": 0x23, "pageup": 0x21, "pagedown": 0x22, "up": 0x26, "down": 0x28,
            "left": 0x25, "right": 0x27}
_PRETTY = {"esc": "Esc", "escape": "Esc", "enter": "Enter", "return": "Enter",
           "backspace": "Backspace", "pageup": "PgUp", "pagedown": "PgDn"}


def _parts(spec: str) -> list:
    return [p.strip() for p in str(spec or "").lower().replace("-", "+").split("+") if p.strip()]


def _key(part: str) -> int:
    """'s' -> 0x53 · '5' -> 0x35 · 'f5' -> 0x74 · 'space' -> 0x20 · pata na ho -> 0"""
    if part in _SPECIAL:
        return _SPECIAL[part]
    if len(part) == 1 and (part.isalpha() or part.isdigit()):
        return ord(part.upper())
    if len(part) in (2, 3) and part[0] == "f" and part[1:].isdigit():
        num = int(part[1:])
        return 0x70 + num - 1 if 1 <= num <= 24 else 0
    return 0


def parse(spec: str) -> tuple:
    """'ctrl+alt+s' -> (3, 0x53)  ·  galat spec -> (0, 0). Sirf **ek modifier +
    ek key**; galat spec par `start()` `False` deta hai, app chalti rehti hai."""
    mods, keys = 0, []
    for part in _parts(spec):
        if part in _MODS:
            mods |= _MODS[part]
        else:
            keys.append(_key(part))
    if len(keys) != 1 or not mods or not keys[0]:
        return 0, 0
    return mods, keys[0]


def _pretty(part: str) -> str:
    """UI text: 's'->'S', 'f5'->'F5', 'space'->'Space'."""
    if len(part) == 1:
        return part.upper()
    if len(part) in (2, 3) and part[0] == "f" and part[1:].isdigit():
        return "F" + part[1:]
    return _PRETTY.get(part, part.capitalize())


def describe(spec: str) -> str:
    """'ctrl+alt+s' -> 'Ctrl+Alt+S' (UI ke liye). Galat spec -> ''"""
    out = []
    for part in _parts(spec):
        if part in _MODS:
            out.append(_NAMES[_MODS[part]])
        else:
            text = _pretty(part)
            if text not in out:
                out.append(text)
    return "+".join(out)


class WinApi:
    """`RegisterHotKey` + message pump. Test me iske bajaye stub daalte hain."""

    def __init__(self):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int,
                                               ctypes.c_uint, ctypes.c_uint]
        self.user32.RegisterHotKey.restype = wintypes.BOOL
        self.user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.UnregisterHotKey.restype = wintypes.BOOL
        # MSG pointer hai - argtypes ke bina 64-bit par lParam kat jaata hai.
        self.user32.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND,
                                              ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        self.user32.PeekMessageW.restype = wintypes.BOOL

    def register(self, mods: int, vk: int) -> bool:
        return bool(self.user32.RegisterHotKey(None, HOTKEY_ID, mods, vk))

    def unregister(self) -> bool:
        return bool(self.user32.UnregisterHotKey(None, HOTKEY_ID))

    def reason(self) -> str:
        code = ctypes.get_last_error()
        return "Windows error %d" % code if code else "wajah nahi mili"

    def pump(self, stop, on_press, idle: float = 0.05) -> None:
        """Sirf WM_HOTKEY. `GetMessage` block karta hai - `PeekMessage` + chhota
        wait, is liye `stop()` turant mano kar leta hai."""
        msg = wintypes.MSG()
        while not stop.is_set():
            hit = False
            while self.user32.PeekMessageW(ctypes.byref(msg), None,
                                           WM_HOTKEY, WM_HOTKEY, PM_REMOVE):
                hit = True
                on_press()
            if not hit:
                stop.wait(idle)


def _safe_api():
    try:
        return WinApi()
    except Exception as exc:
        log.warning("Win32 hotkey nahi ban sakta: %s: %s", type(exc).__name__, exc)
        return None


class Hotkey:
    """Ek thread: register + pump + unregister usi thread par."""

    def __init__(self, spec: str = "", on_press=None, api=None):
        self.spec = spec or ""
        self.mods, self.vk = parse(self.spec)
        self.on_press = on_press or (lambda: None)
        self.api = _safe_api() if api is None else api
        self._stop, self._live, self._thread = threading.Event(), threading.Event(), None
        self._ok = False

    def valid(self) -> bool:
        return bool(self.mods and self.vk and self.api)

    def start(self) -> bool:
        if not self.valid():
            log.info("hotkey chalti nahi (spec=%r) - baaki sab theek hai", self.spec)
            return False
        if self._thread is not None:
            return True
        self._stop.clear()
        self._live.clear()
        self._ok = False
        self._thread = threading.Thread(target=self._run, name="hotkey", daemon=True)
        self._thread.start()
        self._live.wait(2.0)        # thread ne register kar liya ya nahi
        if not self._ok:
            if self._thread.is_alive():
                self._thread.join(timeout=1.0)
            self._thread = None
            return False
        log.info("hotkey chalu: %s", describe(self.spec))
        return True

    def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=2.0)

    def _reason(self) -> str:
        return self.api.reason() if hasattr(self.api, "reason") else "wajah nahi mili"

    def _run(self) -> None:
        try:
            self._ok = bool(self.api.register(self.mods, self.vk))
            if not self._ok:
                log.warning("hotkey %s book nahi hui (shayad dusra app pakad raha "
                            "hai): %s", describe(self.spec), self._reason())
            self._live.set()       # `start()` ko turant bata do
            if self._ok:
                self.api.pump(self._stop, self._fire)
        except Exception as exc:
            log.error("hotkey thread gira: %s: %s", type(exc).__name__, exc)
        finally:
            if self._ok:
                self.api.unregister()
            self._live.set()

    def _fire(self) -> None:
        try:
            self.on_press()
        except Exception as exc:
            log.error("hotkey ka kaam fail: %s: %s", type(exc).__name__, exc)