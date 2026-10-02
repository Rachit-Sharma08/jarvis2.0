"""Global hotkey - parse/describe (pure) + `Hotkey` ka flow (stub api).

Asli `RegisterHotKey` **kabhi call nahi hota**: `Hotkey` me `api` stub daala
jaata hai. Sabse zaroori check `test_hotkey_thread_ownership` hai - bug 2-Oct
me isi se pakda gaya: `RegisterHotKey` aur `PeekMessageW` alag thread par
hone se `WM_HOTKEY` kisi aur queue me chala jaata tha, yaani key kabhi trigger
hi nahi hoti.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from desktophelp import FAILED, check, finish, show
from desktop import hotkey

ROOT = Path(__file__).resolve().parent.parent


class StubApi:
    """WinApi ka nakli. `pump()` WM_HOTKEY ki jagah khud press bana deta hai."""

    def __init__(self, ok=True):
        self.ok, self.events, self.presses, self.ids = ok, [], 0, {}

    def register(self, mods, vk):
        self.events.append(("register", mods, vk))
        self.ids["register"] = threading.get_ident()
        return self.ok

    def unregister(self):
        self.events.append(("unregister",))
        self.ids["unregister"] = threading.get_ident()
        return True

    def pump(self, stop, on_press, idle=0.05):
        self.events.append(("pump",))
        self.ids["pump"] = threading.get_ident()
        while not stop.is_set():
            self.presses += 1
            on_press()
            stop.wait(0.01)


def _wait_for(pred, tries=50, step=0.02):
    for _ in range(tries):
        if pred():
            return True
        time.sleep(step)
    return False


def test_hotkey_parse():
    print("HOTKEY PARSE (pure)")
    ctrl, alt = hotkey.MOD_CONTROL, hotkey.MOD_ALT
    check("ctrl+alt+s", hotkey.parse("ctrl+alt+s"), (ctrl | alt, 0x53))
    check("case par nahi chinta", hotkey.parse("CTRL+ALT+S"), (ctrl | alt, 0x53))
    check("dash bhi chalega", hotkey.parse("ctrl-alt-s"), (ctrl | alt, 0x53))
    check("spaces kat jaate hain", hotkey.parse(" Ctrl + Alt + S "), (ctrl | alt, 0x53))
    check("F5", hotkey.parse("ctrl+shift+f5"), (ctrl | hotkey.MOD_SHIFT, 0x74))
    check("F12", hotkey.parse("ctrl+f12")[1], 0x7B)
    check("sirf ek digit", hotkey.parse("ctrl+alt+7")[1], 0x37)
    check("space", hotkey.parse("ctrl+space")[1], 0x20)
    check("win bhi", hotkey.parse("win+alt+s")[0], hotkey.MOD_WIN | alt)

    # --- galat spec: app crash nahi hogi, sirf hotkey nahi chalegi ---
    for bad in ("", "   ", "s", "ctrl", "ctrl+alt", "ctrl+alt+shift",
                "ctrl+alt+s+x", "ctrl+nosuchkey", "f99", "ctrl+f0", None):
        check(f"galat spec {bad!r} -> (0,0)", hotkey.parse(bad), (0, 0))
    check("F0 hai hi nahi", hotkey.parse("ctrl+f0"), (0, 0))


def test_hotkey_describe():
    print("HOTKEY DESCRIBE (UI text)")
    check("ctrl+alt+s", hotkey.describe("ctrl+alt+s"), "Ctrl+Alt+S")
    check("order waisa hi", hotkey.describe("shift+ctrl+alt+s"), "Shift+Ctrl+Alt+S")
    check("f5", hotkey.describe("ctrl+f5"), "Ctrl+F5")
    check("space", hotkey.describe("ctrl+space"), "Ctrl+Space")
    check("khali", hotkey.describe(""), "")
    check("label aur parse dono config se",
          hotkey.describe(config.HUD_HOTKEY), "Ctrl+Alt+S")


def test_hotkey_lifecycle():
    print("HOTKEY LIFECYCLE (stub api)")
    api = StubApi()
    hits = []
    key = hotkey.Hotkey("ctrl+alt+s", on_press=lambda: hits.append(1), api=api)
    check("valid", key.valid(), True)
    check("start OK", key.start(), True)
    reg = [e for e in api.events if e[0] == "register"][0]
    check("RegisterHotKey sahi args", reg[:1], ("register",))
    check("  mods", reg[1], hotkey.MOD_CONTROL | hotkey.MOD_ALT)
    check("  vk = S", reg[2], 0x53)
    check("dobara start par naya thread nahi", key.start(), True)
    check("register sirf ek baar",
          len([e for e in api.events if e[0] == "register"]), 1)
    check("press par on_press chala", _wait_for(lambda: bool(hits)), True)
    key.stop()
    check("stop par Unregister", ("unregister",) in api.events, True)
    check("thread bhar band", key._thread, None)

    # Register fail (dusra app ne pakad liya) -> app safe, koi crash nahi
    bad = StubApi(ok=False)
    key2 = hotkey.Hotkey("ctrl+alt+s", api=bad)
    check("register fail par start False", key2.start(), False)
    check("  koi thread nahi bana", key2._thread, None)
    check("  unregister nahi hua (kuch book hi nahi)", ("unregister",) in bad.events, False)
    key2.stop()                       # crash nahi hona chahiye

    # Galat spec -> kabhi start nahi hota
    key3 = hotkey.Hotkey("ctrl+alt", api=StubApi())
    check("galat spec valid nahi", key3.valid(), False)
    check("galat spec start False", key3.start(), False)


def test_hotkey_thread_ownership():
    """**Ye test asli bug pakdega.** `hWnd=NULL` hone se `WM_HOTKEY` usi thread
    ki queue me aata hai jisne `RegisterHotKey` call kiya - is liye register,
    pump aur unregister teenon **ek hi thread** par hone chahiye."""
    print("HOTKEY THREAD OWNERSHIP ( asli bug ka pakkaura)")
    api = StubApi()
    key = hotkey.Hotkey("ctrl+alt+s", api=api)
    check("start OK", key.start(), True)
    check("register aur pump ek hi thread",
          api.ids.get("register") == api.ids.get("pump"), True)
    check("  wo thread 'hotkey' naam wali hai",
          key._thread is not None and key._thread.name, "hotkey")
    check("register main thread par nahi hua",
          api.ids.get("register") != threading.get_ident(), True)
    key.stop()
    check("unregister bhi usi thread par",
          api.ids.get("unregister") == api.ids.get("register"), True)

    # on_press crash kare to thread na gire
    class Boom(StubApi):
        def pump(self, stop, on_press, idle=0.05):
            while not stop.is_set():
                on_press()
                stop.wait(0.01)
    key4 = hotkey.Hotkey("ctrl+alt+s",
                         on_press=lambda: (_ for _ in ()).throw(RuntimeError("x")),
                         api=Boom())
    key4.start()
    time.sleep(0.05)
    check("crash-safe on_press", key4._thread is not None, True)
    key4.stop()


def test_hotkey_hygiene():
    print("HYGIENE (hotkey file)")
    path = ROOT / "desktop/hotkey.py"
    lines = len(path.read_text(encoding="utf-8").splitlines())
    check(f"hotkey.py <200 lines ({lines})", lines < 200, True)
    src = path.read_text(encoding="utf-8")
    check("sirf ctypes (koi naya package nahi)", "import ctypes" in src, True)
    check("pyaudio/sounddevice nahi", "pyaudio" in src.lower(), False)
    show(f"hotkey.py = {lines} lines")


for fn in (test_hotkey_parse, test_hotkey_describe, test_hotkey_lifecycle,
           test_hotkey_thread_ownership, test_hotkey_hygiene):
    fn()

finish("Global hotkey ke test pass.")