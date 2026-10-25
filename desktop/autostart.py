r"""Windows login par auto-start — `HKCU\\...\\Run` me ek value (Phase 5 Step 3).

Value: `pythonw.exe D:\Projects\jarvis\jarvis2.0\desktop\launcher.py` — supervisor wahi hai jo
`start_jarvis.bat` chalaata hai, bas pythonw se. Is liye login par koi black
console nahi aata, aur crash `logs/desktop.out` me padha jaata hai
(`desktop/launcher.py` ka `_tee`). Haath se chalane ka raasta waise hi hai.

**`-m` mat likhna.** Windows Run key ka cwd `C:\Windows\System32` hota hai, aur
wahin se `-m desktop.launcher` import hi nahi hota (ModuleNotFoundError) — app
chup-chaap mar jaata. File ka path likhne se launcher apna `BASE_DIR` khud
`sys.path` me daal leta hai, aur `main()` cwd bhi theek kar deta hai (child ko
bhi chahiye).

Teen niyam, is file me chipke:

1. **HKCU** = sirf is user ka. Admin ya UAC nahi chahiye.
2. **Module me koi module-level registry call nahi.** Sirf `main()` se
   (`python -m desktop.autostart install`) likha jaata hai, aur wo tabhi jab
   user ne "haan" bola ho. Baaki har function me `reg` daala ja sakta hai —
   test me fake registry dete hain, asli kabhi nahi chhooti.
3. **Ek hi raasta:** value yahi banti hai jo supervisor chalaata hai. Alag
   command ya shortcut yahan nahi — wo `desktop/shortcut.py` (HUD) ka kaam hai.

`install()` pehle `reg export` backup ka faisla nahi leta — wo asli kaam hai
(README + AGENTS.md), kyunki is module ko registry ka backup banana nahi pata.
"""
import subprocess
import sys
from pathlib import Path

import config
from log_setup import get_logger

log = get_logger("autostart")


def value_name() -> str:
    """Registry value ka naam. Naam ek hi jagah se (`config_name`), isliye
    `AUTOSTART_NAME` pehle se hi `ASSISTANT_NAME` hai."""
    return config.AUTOSTART_NAME


def pythonw() -> str:
    """`pythonw.exe` — console na dikhe. Na ho to `python.exe` (waise hi chalta
    hai, bas console dikhega). `desktop/shortcut.py` ka wahi faisla, dobara
    nahi likha gaya — dono me se ek ko badalna ho to dono socho."""
    exe = Path(sys.executable).with_name("pythonw.exe")
    return str(exe if exe.is_file() else Path(sys.executable))


def script() -> Path:
    """`desktop/launcher.py` ka full path. **Script** `-m` se nahi, file se:
    Windows login par Run key ka cwd `C:\Windows\System32` hota hai, aur wahin
    se `-m desktop.launcher` import hi nahi hota (ModuleNotFoundError) — isi
    liye login par app chup-chaap mar jaata. `launcher.py` apne aap BASE_DIR ko
    `sys.path` me daalta hai, is liye file se chalane se bhi wahi supervisor
    chalta hai (ek hi raasta)."""
    return Path(config.BASE_DIR) / config.AUTOSTART_SCRIPT


def command(exe: str = "", script_path: Path = None) -> list:
    """Run value ke liye argv. Test yahi list check karta hai — koi process
    nahi chalta."""
    return [exe or pythonw(), str(script_path or script())]


def run_value(exe: str = "", script_path: Path = None) -> str:
    """-> wo ek string jo registry me jaati hai. Path me space ho to `list2cmdline`
    khud quote kar deta hai — haath se quote karna mat karo."""
    return subprocess.list2cmdline(command(exe, script_path))


def _winreg():
    """`winreg` sirf asli kaam ke waqt import — non-Windows par ye module import
    hota to bhi crash na ho, aur test me fake chala sake."""
    import winreg
    return winreg


def read(reg=None) -> str:
    """Abhi ki value, ya "" (value hi nahi hai)."""
    reg = reg or _winreg()
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, config.AUTOSTART_RUN_KEY) as key:
            return str(reg.QueryValueEx(key, value_name())[0])
    except OSError:
        return ""


def enabled(reg=None) -> bool:
    """Auto-start laga hai ya nahi. Ye sirf **padhne** wala hai — kabhi khud
    apne aap value nahi likhta."""
    return bool(read(reg))


def install(reg=None) -> tuple:
    """Value likh do. -> (ok, reason). Value pehle se sahi ho to `reason` me
    wahi command wapas milti hai, dobara likhne ki zarurat nahi."""
    reg = reg or _winreg()
    value, name = run_value(), value_name()
    try:
        with reg.CreateKeyEx(reg.HKEY_CURRENT_USER, config.AUTOSTART_RUN_KEY,
                            0, reg.KEY_SET_VALUE) as key:
            reg.SetValueEx(key, name, 0, reg.REG_SZ, value)
    except OSError as exc:
        log.error("auto-start value nahi likhi: %s", exc)
        return False, str(exc)
    log.info("auto-start ON: %s = %s", name, value)
    return True, value


def remove(reg=None) -> tuple:
    """Value hata do. Pehle se nahi thi to bhi `ok` — user ka maqsad wahi tha."""
    reg = reg or _winreg()
    name = value_name()
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, config.AUTOSTART_RUN_KEY) as key:
            reg.DeleteValue(key, name)
    except FileNotFoundError:
        return True, "pehle se nahi tha"
    except OSError as exc:
        log.error("auto-start value nahi hata: %s", exc)
        return False, str(exc)
    log.info("auto-start OFF: %s hata diya", name)
    return True, "hat gaya"


def status(reg=None) -> dict:
    """-> {name, value, on}. Sirf padhta hai."""
    value = read(reg)
    return {"name": value_name(), "value": value, "on": bool(value)}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    action = argv[0] if argv else "status"
    if action not in ("install", "remove", "status"):
        print("Sirf ye chal sakta hai: install | remove | status")
        return 1
    if action == "status":
        info = status()
        print("%s: auto-start %s" % (info["name"], "ON" if info["on"] else "OFF"))
        if info["value"]:
            print("  %s" % info["value"])
        return 0
    ok, reason = install() if action == "install" else remove()
    print("%s: auto-start %s (%s)" % (value_name(), action, reason))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())