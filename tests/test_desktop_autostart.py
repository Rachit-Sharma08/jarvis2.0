"""STEP 3: Windows login par auto-start (`HKCU\\...\\Run`).

Ye test **asli registry kabhi nahi chhooti** — `desktop/autostart.py` har
registry function me `reg` daal sakta hai, aur yahan `FakeReg` (dict-based
nakli) diya gaya hai. Isi liye `install()`/`remove()` ko fake ke saath hi
call kiya gaya hai.

Pakdi hui baatein:

1. Value ka naam **config se** aata hai (`Jarvis`), "Prabh"/"Sunday" nahi.
2. Command `pythonw.exe -m desktop.launcher` hai — pythonw (koi black console
   nahi), aur wahi supervisor jo `start_prabh.bat` chalaata hai.
3. Path me space ho to value quoted jaati hai (`list2cmdline`).
4. `install`/`remove`/`read`/`status` ka cycle, + error aur "pehle se nahi
   tha" wala raasta.
5. `main()` ka CLI dispatch registry ke baghair check karta hai (fake patch).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from desktop import autostart, launcher
from desktophelp import FAILED, check, finish, show, truthy


class FakeKey:
    """`winreg` key — context manager hi hai, koi asli handle nahi."""

    def __init__(self, reg):
        self.reg = reg

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeReg:
    """`winreg` ka nakli. `values` dict me value; `written` me likha gaya."""

    HKEY_CURRENT_USER = "HKCU"
    KEY_READ = 0
    KEY_SET_VALUE = 1
    REG_SZ = 1

    def __init__(self, values=None, boom=False):
        self.values = dict(values or {})
        self.boom = boom
        self.written = []

    def _key(self):
        if self.boom:
            raise OSError("access denied")
        return FakeKey(self)

    def OpenKey(self, root, path):                      # noqa: N802 - winreg ka naam
        return self._key()

    def CreateKeyEx(self, root, path, reserved=0, access=None):   # noqa: N802
        return self._key()

    def QueryValueEx(self, key, name):                  # noqa: N802
        if name not in self.values:
            raise FileNotFoundError(name)
        return (self.values[name], self.REG_SZ)

    def SetValueEx(self, key, name, reserved, kind, value):        # noqa: N802
        self.values[name] = value
        self.written.append((name, value))

    def DeleteValue(self, key, name):                   # noqa: N802
        if name not in self.values:
            raise FileNotFoundError(name)
        del self.values[name]


def fake(values=None, boom=False):
    return FakeReg(values=values, boom=boom)


# ---- naam + command (registry ke baghair) ----

def test_name():
    print("[autostart] naam")
    check("value ka naam Jarvis", autostart.value_name(), "Jarvis")
    check("config bhi wahi", config.AUTOSTART_NAME, config.ASSISTANT_NAME)
    check("purana naam nahi", "Prabh" in autostart.value_name(), False)
    check("Run key wahi", config.AUTOSTART_RUN_KEY,
          r"Software\Microsoft\Windows\CurrentVersion\Run")


def test_command():
    print("[autostart] command")
    cmd = autostart.command()
    truthy("pythonw hi", Path(cmd[0]).name == "pythonw.exe")
    check("module flag", cmd[1], "-m")
    check("supervisor hi", cmd[2], config.AUTOSTART_TARGET)
    check("target launcher hai", config.AUTOSTART_TARGET, "desktop.launcher")
    # Haath se chalane ka raasta alag: .bat pythonw se nahi, python se.
    check("run value ek string", autostart.run_value(), cmd[0] + " -m " + cmd[2])
    # Space wale path me quote khud lagta hai.
    quoted = autostart.run_value(exe=r"D:\My Drive\pythonw.exe")
    check("quote khud laga", quoted,
          '"D:\\My Drive\\pythonw.exe" -m ' + config.AUTOSTART_TARGET)
    show(quoted)


def test_cycle():
    print("[autostart] install / remove / status")
    reg = fake()
    check("pehle OFF", autostart.enabled(reg), False)
    check("khaali value", autostart.read(reg), "")

    ok, reason = autostart.install(reg)
    check("install ok", ok, True)
    check("REG_SZ likha", reg.written, [(config.AUTOSTART_NAME, reason)])
    check("value sahi", autostart.read(reg), autostart.run_value())
    check("ab ON", autostart.enabled(reg), True)

    info = autostart.status(reg)
    check("status on", info["on"], True)
    check("status naam", info["name"], config.AUTOSTART_NAME)

    ok, reason = autostart.remove(reg)
    check("remove ok", ok, True)
    check("value gaya", autostart.read(reg), "")
    ok, reason = autostart.remove(reg)
    check("dobara hatao: phir bhi ok", ok, True)
    check("reason saaf", reason, "pehle se nahi tha")
    show("cycle: " + str(reg.values))


def test_errors():
    print("[autostart] error raasta")
    reg = fake(boom=True)
    ok, reason = autostart.install(reg)
    check("install fail", ok, False)
    truthy("wajah bata", "access denied" in reason)
    check("kuch likha nahi", reg.written, [])
    check("read crash nahi", autostart.read(reg), "")
    ok, _ = autostart.remove(reg)
    check("remove bhi fail", ok, False)


def test_cli():
    print("[autostart] CLI dispatch (registry ke baghair)")
    check("galat argument", autostart.main(["kuch-aur"]), 1)

    calls = []
    saved = {name: getattr(autostart, name)
             for name in ("install", "remove", "status")}
    autostart.install = lambda: (calls.append("install"), (True, "x"))[1]
    autostart.remove = lambda: (calls.append("remove"), (True, "x"))[1]
    autostart.status = lambda: {"name": "Jarvis", "value": "v", "on": True}
    try:
        check("install exit 0", autostart.main(["install"]), 0)
        check("remove exit 0", autostart.main(["remove"]), 0)
        check("status exit 0", autostart.main([]), 0)   # khali = status
        autostart.install = lambda: (calls.append("install"), (False, "denied"))[1]
        check("fail par exit 1", autostart.main(["install"]), 1)
    finally:
        for name, func in saved.items():
            setattr(autostart, name, func)
    check("teeno route bane", calls, ["install", "remove", "install"])


def test_no_import_side_effect():
    print("[autostart] module-level koi registry call nahi")
    src = Path(autostart.__file__).read_text(encoding="utf-8")
    body = src.split('log = get_logger("autostart")', 1)[-1]
    top = [line.strip() for line in body.splitlines()
           if line and not line[0].isspace() and "(" in line]
    check("sirf def/if __name__", [t for t in top if not t.startswith(("def ", "if "))], [])


def test_launcher_no_console():
    print("[autostart] launcher par console na khule")
    src = Path(launcher.__file__).read_text(encoding="utf-8")
    truthy("creationflags lagi", "creationflags=_NO_WINDOW" in src)
    check("flag value", launcher._NO_WINDOW, 0x08000000)
    check("child wahi python", launcher.child_command()[0], sys.executable)


for fn in (test_name, test_command, test_cycle, test_errors, test_cli,
           test_no_import_side_effect, test_launcher_no_console):
    fn()

finish("AUTO-START TESTS GREEN")