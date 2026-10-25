"""`start_prabh.bat` ka test - koi app chala kar nahi, sirf file padhi jaati hai
aur ek nayi copy par `cmd` se check hota hai.

Ye Step 3a ke sabse burre live bug ka pakka test hai: file me ek `echo` line
par raw `( )` hone se `cmd` ka `if not exist` block beech me toot gaya, `exit`
line HAMESHA chala gaya, aur python **bilkul launch nahi hua** - na tray icon,
na process. User ko sirf "Press any key to continue" dikha.
"""

import os
import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from desktophelp import FAILED, check, finish, show

ROOT = Path(__file__).resolve().parent.parent
BAT = ROOT / "start_prabh.bat"

# Ye line bat ko nahi chala ke bas apna raasta dikhati hai.
LAUNCH = '".venv\\Scripts\\python.exe" -m desktop.launcher'
# Test me ise se badal kar echo daalte hain - asli python kabhi chalta hi nahi.
MARKER = "JARVIS_TEST_LAUNCH_LINE_RAN"


def _lines():
    return BAT.read_text(encoding="ascii").splitlines()


def test_crlf():
    print("BAT: CRLF line ending")
    raw = BAT.read_bytes()
    lf = raw.count(b"\n")
    crlf = raw.count(b"\r\n")
    check("sab LF CRLF ke saath hain", lf, crlf)
    check("kam se kam ek line hai", lf > 0, True)


def test_ascii_only():
    print("BAT: ASCII only")
    non_ascii = [c for c in BAT.read_bytes() if c > 127]
    check("koi UTF-8 char nahi", len(non_ascii), 0)


def test_no_stray_bracket():
    """Raw `(` / `)` sirf `if` / `for` / `else` line par ya akele `)` par.

    Ye wahi rule hai jisne Step 3a ka bug pakda: kisi bhi dusri line par
    bracket `if` block ko beech me tor deta hai.
    """
    print("BAT: kahin bhi raw bracket nahi")
    allowed_tail = (")", ")", ")", ")")
    for i, line in enumerate(_lines(), 1):
        stripped = line.strip()
        low = stripped.lower()
        if "(" not in line and ")" not in line:
            continue
        if low.startswith("rem ") or low == "rem":
            continue                                   # comment - cmd ignore karta hai
        if low.startswith(("if ", "for ", "while ", "goto ", "else (")) or \
                stripped == ")" or stripped in allowed_tail:
            continue
        check(f"line {i} par bracket: {stripped[:60]}", False, True)
    check("bracket rule pass", FAILED, [])


def test_uses_goto_not_block():
    """Abhi file `goto` use karti hai - `if (...)` block nahi. Regression guard."""
    print("BAT: goto style (bracket block nahi)")
    text = BAT.read_text(encoding="ascii")
    check("if not exist ... goto", "if not exist" in text and " goto " in text, True)
    opens = [ln.strip() for ln in _lines() if ln.strip().endswith("(")]
    check("koi line block nahi kholti", opens, [])


def test_launch_line_present():
    print("BAT: launch line maujood hai")
    lines = [ln.strip() for ln in _lines()]
    check("python launcher wali line", LAUNCH in lines, True)


def test_cmd_actually_runs_the_line():
    """Asli pakka test: `cmd` se copy chala kar dekho ki python wali line
    sach me pahunchti hai ya nahi. App is liye nahi chalta kyunki us line ki
    jagah `echo` daal diya gaya hai.

    Copy ROOT ke andar hi banti hai - `cd /d "%~dp0"` se `.venv` milna zaroori
    hai, warna test `if` ke ulti raaste pe chala jaayega.
    """
    print("BAT: cmd par sach me chalti hai")
    check("launch line mili", LAUNCH in BAT.read_text(encoding="ascii"), True)
    copy = ROOT / "_bat_probe_tmp.bat"
    try:
        copy.write_bytes(BAT.read_bytes().replace(
            LAUNCH.encode("ascii"), ("echo " + MARKER).encode("ascii")))
        out = subprocess.run(["cmd", "/c", str(copy)], capture_output=True,
                             text=True, stdin=subprocess.DEVNULL, timeout=60,
                             cwd=str(ROOT))
        seen = MARKER in (out.stdout + out.stderr)
        check(f"{MARKER} console par dikha", seen, True)
        if not seen:
            print("  cmd output:", repr((out.stdout + out.stderr)[:400]))
    finally:
        copy.unlink(missing_ok=True)


for fn in (test_crlf, test_ascii_only, test_no_stray_bracket,
           test_uses_goto_not_block, test_launch_line_present,
           test_cmd_actually_runs_the_line):
    fn()

finish("Saare start_prabh.bat test pass.")