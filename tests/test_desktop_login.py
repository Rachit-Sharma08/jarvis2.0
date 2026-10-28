r"""STEP 3: **login par cwd** ka asli pakkaura (4 Oct 2026).

Ye test `tests/test_desktop_autostart.py` se pada hai — file 200 se badi ho
gayi thi (AGENTS ka niyam).

**Asli bug:** Windows Run key ka cwd `C:\Windows\System32` hota hai. Wahan se
`pythonw -m desktop.launcher` chalane par Python ModuleNotFoundError deta hai
(`Error while finding module specification`), yaani login par app **chup-chaap
mar jaata** — koi tray nahi, koi HUD nahi. Isi liye Run value me `-m module`
ki jagah **file ka path** likha jaata hai, aur `desktop/launcher.py` khud apna
`BASE_DIR` `sys.path` me daalta hai + `main()` me cwd theek kar deta hai (child
`desktop.app` ko bhi sahi cwd chahiye, warna wahi mar jaata).

Yahan **asli launcher start nahi** hota — sirf module load hota hai (app start /
mic / tray kabhi nahi).
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from desktop import autostart, launcher
from desktophelp import check, finish, truthy

OTHER_CWD = r"C:\Windows\System32"


def launcher_text() -> str:
    return Path(launcher.__file__).read_text(encoding="utf-8")


def test_value_has_no_dash_m():
    print("[login] Run value me -m nahi")
    value = autostart.run_value()
    check("-m nahi", "-m" in value, False)
    check("pythonw + launcher.py",
          value, autostart.pythonw() + " " + str(autostart.script()))
    truthy("launcher.py waqai hai", autostart.script().is_file())
    check("config se bana", config.AUTOSTART_SCRIPT, "desktop/launcher.py")


def test_loads_from_other_cwd():
    print("[login] dusre cwd se load")
    src = ("import importlib.util, os\n"
           "os.chdir(r'%s')\n"
           "spec = importlib.util.spec_from_file_location('lj', r'%s')\n"
           "mod = importlib.util.module_from_spec(spec)\n"
           "spec.loader.exec_module(mod)\n"
           "print('BASE', mod.BASE)\n" % (OTHER_CWD, launcher.__file__))
    out = subprocess.run([sys.executable, "-c", src], cwd=OTHER_CWD,
                         capture_output=True, text=True, timeout=60)
    check("System32 par bhi load", out.returncode, 0)
    truthy("BASE sahi", ("BASE %s" % config.BASE_DIR) in (out.stdout or ""))


def test_bootstrap_order():
    print("[login] bootstrap ka order")
    text = launcher_text()
    # `sys.path` ka kaam `import config` se **pehle** hona chahiye, warna
    # System32 par wahi ModuleNotFound wapas aa jaata hai.
    truthy("sys.path pehle",
           text.index("sys.path.insert") < text.index("import config"))
    truthy("cwd theek hota hai", "os.chdir(config.BASE_DIR)" in text)
    truthy("creationflags lagi", "creationflags=_NO_WINDOW" in text)
    check("flag value", launcher._NO_WINDOW, 0x08000000)
    check("child wahi python", launcher.child_command()[0], launcher.child_python())


for fn in (test_value_has_no_dash_m, test_loads_from_other_cwd,
           test_bootstrap_order):
    fn()

finish("LOGIN-CWD TESTS GREEN")