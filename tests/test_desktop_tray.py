"""Tray icon + menu + shared state + Windows permission/lock ka test.

Asli tray message loop, asli mic aur asli registry write **kabhi nahi**
chalti — sirf icon draw, menu build aur state badlav check hote hain.
Shell ka baaki hissa `test_desktop.py` me hai.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from desktophelp import FAILED, check, finish, show
from desktop import lockwatch, micperm
from desktop import trayicon
from desktop.state import DesktopState
from desktop.tray import Tray

STATES = (config.TRAY_OFF, config.TRAY_IDLE, config.TRAY_LISTENING,
          config.TRAY_MUTED, config.TRAY_ERROR)


class _FakeActions:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        def call():
            self.calls.append(name)
        return call


def test_tray_icon():
    print("TRAY ICON")
    check("paanch state", len(STATES), 5)
    pixels = {}
    for state in STATES:
        img = trayicon.image(state)
        check(f"{state} 64x64", (img.size, img.mode), ((64, 64), "RGBA"))
        pixels[state] = img.tobytes()
    check("sab rang alag", len(set(pixels.values())), len(STATES))
    for state in STATES:
        img = trayicon.image(state)
        check(f"{state} mic nishaan", img.getpixel((32, 28))[3] > 200, True)
    check("mute me tir hai", pixels[config.TRAY_MUTED] != pixels[config.TRAY_LISTENING], True)
    check("title har state ke liye", all(config.tray_title(s) for s in STATES), True)


def test_tray_menu():
    print("TRAY MENU")
    state = DesktopState()
    actions = _FakeActions()
    tray = Tray(actions, state)
    labels = [item.text for item in tray.build()]
    show(f"items = {labels}")
    check("status + 6 button + hint", len(labels), 10)   # 8 asli + 2 divider
    for wanted in ("Mic Mute", "Open HUD", config.SLEEP_FROM_TRAY, "TOOLS",
                   "Restart", "Quit"):
        check(f"'{wanted}' hai", wanted in labels, True)
    check("pehla item haalat", labels[0].startswith("Jarvis"), True)
    check("Quit sabse neeche", labels[-1], "Quit")
    # Hotkey ki tafseer - sirf text, click se kuch nahi hota (disabled item)
    hints = [t for t in labels if t.startswith("  ya phir")]
    check("ek hint hai", len(hints), 1)
    check("  usme current hotkey", config.HUD_HOTKEY and "Ctrl+Alt+S" in hints[0], True)
    # pystray ka `action` private hai — wahi method call karte hain jo click par chalti hai
    tray._toggle_mute(None, None)
    tray._open_hud(None, None)
    tray._toggle_tools(None, None)
    tray._restart(None, None)
    tray._quit(None, None)
    check("sab button ne sahi call kiya", sorted(set(actions.calls)),
          ["open_hud", "quit", "restart", "toggle_mute", "toggle_tools"])
    Tray(_FakeActions())._guard(lambda: (_ for _ in ()).throw(RuntimeError("test crash")))
    print("  OK   crash guard (app nahi giri)")


def test_state():
    print("DESKTOP STATE")
    state = DesktopState()
    start = state.version()
    check("shuru me mic off", state.mic(), "off")
    check("badlav hua", state.set_mic(config.TRAY_LISTENING), True)
    check("version badha", state.version() > start, True)
    check("wahi value par version nahi badla", state.set_mic(config.TRAY_LISTENING), False)
    check("mute on", state.set_muted(True), True)
    check("toggle se mute off", state.toggle_muted(), False)
    check("toggle se mute on", state.toggle_muted(), True)
    state.set_muted(False)
    try:
        state.set_mic("kuch-aur")
        FAILED.append("bad mic state block nahi hua")
        print("  FAIL bad mic state block nahi hua")
    except ValueError:
        print("  OK   bad mic state block hua")
    check("snapshot me sab", sorted(state.snapshot()),
          ["asleep", "hud_open", "mic", "mic_reason", "muted", "tools_on",
           "version", "wake"])
    check("HUD khola", state.set_hud(True), True)
    check("wake state", state.set_wake("listening"), True)
    check("HUD event publish crash nahi kiya", state.set_tools(True), True)


def test_mic_permission():
    print("WINDOWS MIC PERMISSION")
    allowed, reason = micperm.status(sys.executable)
    check("tuple mila", isinstance(allowed, bool) and isinstance(reason, str), True)
    show(f"allowed={allowed} reason={reason or '-'}")
    key = micperm._nonpackaged_key(r"D:\prabh\.venv\Scripts\pythonw.exe")
    check("NonPackaged key ka naam",
          key.endswith(r"NonPackaged\D##prabh#.venv#Scripts#pythonw.exe"), True)
    check("chhota error", len(micperm.explain("A" * 300)) <= 160, True)


def test_lock_watch():
    print("WINDOWS LOCK (heuristic)")
    check("bool deta hai", isinstance(lockwatch.is_locked(), bool), True)
    show(f"abhi locked={lockwatch.is_locked()}  (PC lock karke dekh sakte ho)")


for fn in (test_tray_icon, test_tray_menu, test_state, test_mic_permission, test_lock_watch):
    fn()

finish("Saare tray/state test pass.")