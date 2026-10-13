"""`config.X` ka AttributeError pehle se rokne wala test.

Ye project ka **sabse aam** galti hai (AGENTS 8.1.2): koi naya constant banta
hai, aur bhool se `config.py` ke import list me nahi jaata — phir test (ya
worse, runtime) par `AttributeError: module 'config' has no attribute 'X'`.

Ye test wahi rokta hai, aur **runtime** par (AST/source guess nahi):

1. Poora production code scan hota hai `config.NAME` aur
   `from config import NAME` dhoondhne ke liye. Har `NAME` ke liye
   `getattr(config, NAME)` sach me chalna chahiye.
2. Har `config_*.py` jo `config.py` import karta hai, disk par hona chahiye
   (warna `config.py` import hi nahi hoga — app chup-chaap mar jayega).
3. `config_wake.py` ke do naye hisse (`config_lines`, `config_audio`) uske
   through wapas export hone chahiye — purane callers `config_wake.X` se bhi
   chalte hain (kuch test wahi karte hain).

**Source-scan se jaan-boojh kar bacha gaya hai.** Pehle is test ka pehla
version `ast` se `X = ...` assignments dhoondhta tha, is liye `config.py` ke
**import kiye** naam usme dikhai nahi dete the aur 6 part ke har constant
"missing" report ho gaye — jabki runtime par sab resolve ho rahe the. Lesson:
import kiye hue naam dekhne ke liye `ast.Assign` nahi, **asli getattr**
chahiye.

Sirf production source padha jaata hai (`.py`, `tests/` bahar), koi module
import nahi hota — is liye ye `.env` ke bina chalta hai aur koi asli setting
nahi badalta.
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FAILED = []

# Production ke ye top-level folders — `tests/` jaan-boojh kar bahar hai.
SOURCE_DIRS = ("desktop", "server", "tools", "voice", "wake", "gatekeeper",
               "core", "brain", "ui", "personas")
SOURCE_FILES = ("config.py", "main.py", "log_setup.py")

# Test files me bhi `config.X` hota hai, par wahi file define bhi kar sakti
# hain (test ka apna stub) — is liye production-only scan sahi hai.
CALL_RE = re.compile(r"\bconfig\.([A-Z][A-Z0-9_]*)\b")
FROM_RE = re.compile(r"^\s*from\s+config\s+import\s+(.+)$", re.M)


def check(name, got, want=True):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def production_files():
    out = []
    for d in SOURCE_DIRS:
        p = ROOT / d
        if p.is_dir():
            out.extend(sorted(p.rglob("*.py")))
    for f in SOURCE_FILES:
        p = ROOT / f
        if p.is_file():
            out.append(p)
    return out


def used_names():
    """`config.NAME` + `from config import ...` — sab production se."""
    used = {}
    for p in production_files():
        text = p.read_text(encoding="utf-8", errors="replace")
        # Apni hi file me define kar raha hai? (config.py `config.X` likhta hi
        # nahi, par defensive.)
        for m in CALL_RE.finditer(text):
            used.setdefault(m.group(1), set()).add(p.relative_to(ROOT).as_posix())
        for m in FROM_RE.finditer(text):
            body = m.group(1)
            for part in body.replace("(", "").replace(")", "").split(","):
                nm = part.strip().split(" as ")[0].strip()
                if re.fullmatch(r"[A-Z][A-Z0-9_]*", nm):
                    used.setdefault(nm, set()).add(p.relative_to(ROOT).as_posix())
    return used


def test_every_used_name_resolves():
    """Sabse zaroori: production jo `config.X` maange, wo **asli** mile."""
    print("config.X jo production maanga — sab resolve hona chahiye")
    used = used_names()
    check("production config.X maangta hai", len(used) > 20, True)
    broken = {n: sorted(v)[:2] for n, v in sorted(used.items())
              if not hasattr(config, n)}
    for name, where in broken.items():
        print(f"    {name} -> {where}")
    check("koi bhi config.X nahi mila", sorted(broken), [])


def test_config_parts_exist():
    """`config.py` jo part import karta hai, wo disk par hona chahiye."""
    print("config.py ke saare part disk par")
    src = (ROOT / "config.py").read_text(encoding="utf-8")
    named = sorted(set(re.findall(r"from\s+(config_\w+)\s+import", src)))
    check("kam se kam ek part import hota hai", len(named) > 0, True)
    missing = [n for n in named if not (ROOT / f"{n}.py").is_file()]
    for n in missing:
        print(f"    {n}.py disk par nahi")
    check("har imported part ki file hai", missing, [])


def test_reexports():
    """`config_wake` ke naye hisse uske through wapas export hote hain."""
    print("config_wake ka re-export poora hai")
    import config_wake
    src = (ROOT / "config_wake.py").read_text(encoding="utf-8")
    for part, mod in (("config_lines", "config_lines"), ("config_audio", "config_audio")):
        check(f"config_wake {part} se import karta hai", f"from {part} import" in src, True)
        p = ROOT / f"{part}.py"
        if not p.is_file():
            check(f"{part}.py disk par hai", False, True)
            continue
        import importlib
        names = [n for n in dir(importlib.import_module(mod))
                 if n.isupper() and not n.startswith("_")]
        gap = sorted(n for n in names if not hasattr(config_wake, n))
        check(f"{part} ka har constant config_wake me bhi ({len(names)} naam)", gap, [])
        gap2 = sorted(n for n in names if not hasattr(config, n))
        check(f"{part} ka har constant config me bhi", gap2, [])


def main():
    test_every_used_name_resolves()
    test_config_parts_exist()
    test_reexports()
    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        return 1
    print("config poora hai - production ka koi bhi config.X nahi toota.")
    return 0


if __name__ == "__main__":
    sys.exit(main())