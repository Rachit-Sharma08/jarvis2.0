"""HUD ke backup raaste ka dusra raasta - Desktop "Jarvis HUD" shortcut.

Sirf **command / path / wiring** check karta hai. Asli `.lnk` **kabhi nahi**
banata ya delete hota hai (warna user ka asli Desktop badal jaata), asli Edge
spawn nahi hota. Shortcut aur hotkey dono ka ek hi raasta `desktop/open_hud.py`
hai - uska test `test_desktop_hotkey.py` me hai.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from desktophelp import FAILED, check, finish, show
from desktop import hud_window, open_hud, shortcut

ROOT = Path(__file__).resolve().parent.parent


def test_open_hud():
    print("OPEN HUD (shortcut + hotkey ka ek hi raasta)")
    check("server up -> kholo", open_hud.plan(True), ("open", ""))
    check("server down -> mat kholo", open_hud.plan(False)[0], "down")
    check("  message Start.bat bataye", "start_prabh.bat" in open_hud.plan(False)[1], True)
    check("koi side effect nahi", callable(open_hud.main), True)
    check("exit codes alag-alag", len({open_hud.EXIT_OK, open_hud.EXIT_NO_BROWSER,
                                       open_hud.EXIT_SERVER_DOWN}), 3)

    # Wahi URL/wahi profile jo app use karti hai - dusra window nahi banega.
    check("HUD ka URL", hud_window.url(), f"{config.SERVER_ORIGIN}/")
    check("profile ek hi", config.HUD_PROFILE_DIR.name, "hud-profile")


def test_shortcut_command():
    print("SHORTCUT (sirf command check)")
    link = Path("D:/fake-Desktop") / "Jarvis HUD.lnk"
    cmd = shortcut.command("install", link)
    check("shell=False ki list hai", isinstance(cmd, list), True)
    check("pehla powershell", cmd[0], "powershell.exe")
    check("-Profile band", "-NoProfile" in cmd, True)
    check("policy bypass", "Bypass" in cmd, True)
    check("script -File se", cmd[cmd.index("-File") + 1], str(shortcut.script()))
    check("Mode install", cmd[cmd.index("-Mode") + 1], "install")
    check("Link sahi", cmd[cmd.index("-Link") + 1], str(link))
    check("Target pythonw", Path(cmd[cmd.index("-Target") + 1]).name, "pythonw.exe")
    check("ArgLine", cmd[cmd.index("-ArgLine") + 1], "-m desktop.open_hud")
    check("WorkDir repo", cmd[cmd.index("-WorkDir") + 1], str(config.BASE_DIR))
    check("script maujood hai", shortcut.script().is_file(), True)
    check("shell=True nahi hai",
          "shell=True" in (ROOT / "desktop/shortcut.py").read_text(encoding="utf-8"),
          False)

    show(f"pythonw = {shortcut.target()}")
    check("naam sahi", shortcut.link_path(folder=Path("D:/fake-Desktop")).name,
          f"{config.HUD_SHORTCUT_NAME}.lnk")


def test_shortcut_desktop_dir():
    """Asli Desktop path padhna hai, par **kuch banaya nahi** jaata."""
    print("SHORTCUT DESKTOP DIR (sirf padhna)")
    real = shortcut.desktop_dir()
    check("Desktop path aaya", real.is_dir(), True)
    check("  naam Desktop", real.name, "Desktop")
    show(f"Desktop = {real}")
    check("folder inject ho sakta hai",
          shortcut.link_path("X", folder=Path("D:/x")).as_posix(), "D:/x/X.lnk")


def test_wiring():
    print("WIRING (app + tray + config)")
    app_src = (ROOT / "desktop/app.py").read_text(encoding="utf-8")
    check("app hotkey banata hai", "hotkey_mod.Hotkey(" in app_src, True)
    check("app hotkey.start() karta hai", "self.hotkey.start()" in app_src, True)
    check("app hotkey.stop() karta hai", "self.hotkey.stop()" in app_src, True)
    cb_src = (ROOT / "desktop/callbacks.py").read_text(encoding="utf-8")
    # Hotkey aur wake dono ka ek hi raasta ab `desktop/callbacks.py` me hai
    # (app.py sirf wahan bhejta hai) - dono `hud.open()` se kaam karte hain.
    check("app dono callbacks.py me bhejta hai",
          app_src.count("callbacks.on_") >= 2, True)
    check("hotkey wake jaisa hi kaam karta hai",
          cb_src.count("hud.open()") >= 2 and "def on_hotkey" in cb_src
          and "def on_wake" in cb_src, True)
    check("tray menu me hint hai",
          "hotkey_mod.describe(config.HUD_HOTKEY)" in
          (ROOT / "desktop/tray.py").read_text(encoding="utf-8"), True)
    check("config me shortcut ka naam", config.HUD_SHORTCUT_NAME, "Jarvis HUD")
    check("config me hotkey", config.HUD_HOTKEY, "ctrl+alt+s")
    check(".env.example me hotkey",
          "PRABH_HUD_HOTKEY" in (ROOT / ".env.example").read_text(encoding="utf-8"), True)
    # .env se badalne wala hona chahiye, matlab .env padha jaata hai
    check("hotkey env se aata hai",
          "PRABH_HUD_HOTKEY" in (ROOT / "config_desktop.py").read_text(encoding="utf-8"),
          True)


def test_hygiene():
    print("HYGIENE")
    for path in ("desktop/open_hud.py", "desktop/shortcut.py", "desktop/app.py",
                 "desktop/tray.py", "config_desktop.py"):
        lines = len((ROOT / path).read_text(encoding="utf-8").splitlines())
        check(f"{path} <200 lines ({lines})", lines < 200, True)


for fn in (test_open_hud, test_shortcut_command, test_shortcut_desktop_dir,
           test_wiring, test_hygiene):
    fn()

finish("HUD shortcut ke test pass.")