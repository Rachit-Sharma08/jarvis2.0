"""KAAM B — Arc Reactor theme ka test runner.

Assertions `arccheck.py` me hain (200-line niyam), yahan sirf wiring.
Playwright **headless**, apne bundled Chromium se, naye profile ke saath.
Rachit ke Chrome/Edge ka koi user profile kabhi use nahi hota.

Screenshot `%TEMP%\\opencode\\hudshots` me — repo me nahi.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import arccheck  # noqa: E402
from arccheck import FAILED

if __name__ == "__main__":
    arccheck.main()
    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        sys.exit(1)
    print("Arc theme test pass (Playwright headless, nakli data).")