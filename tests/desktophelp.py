"""Desktop test suite ka shared helper (tests/poolhelp.py jaisa).

Sirf `check()` aur runner — koi asli mic, browser, tray ya registry nahi.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def show(name):
    print(f"       {name}")


def finish(title):
    print()
    if FAILED:
        print(f"{len(FAILED)} test fail: {FAILED}")
        sys.exit(1)
    print(title)
    sys.exit(0)