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

import config  # noqa: E402  (logsafe ke BAAD — isi order ka niyam hai)
import hudserve  # noqa: E402
import arccheck  # noqa: E402
from arccheck import FAILED

# Asli default DONO jagah bharte hain, taaki test me koi theme hard-code na ho:
# - `hudserve.DEFAULT_THEME` — nakli server yehi serve karega
# - `arccheck.EXPECTED_DEFAULT` — check isi ke khilaf karega
# `hudserve` khud config nahi padhta (`.env` se bachne ke liye), is liye
# yahin `config.hud_theme()` ek hi sach hai. Test runner config import kar
# sakta hai — `logsafe` pehle aa chuka hai (isi order ka niyam).
hudserve.DEFAULT_THEME = config.hud_theme()
arccheck.EXPECTED_DEFAULT = config.hud_theme()

if __name__ == "__main__":
    print(f"Asli config ka default theme: {arccheck.EXPECTED_DEFAULT!r}")
    arccheck.main()
    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        sys.exit(1)
    print("Arc theme test pass (Playwright headless, nakli data).")