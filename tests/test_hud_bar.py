"""KAAM A — HUD ka bottom bar 1366x768 par "neeche se kat raha tha".

VERIFIED (Playwright headless, nakli data, port 8731+):
- Bar ka **box** kabhi viewport se bahar nahi gaya — 800x540 se 1920x1080
  tak 100 viewport, browser zoom 1.0-1.5, Windows 125/150/175% scale, fonts
  load na hone par, aur 60 chat + 30 orb lines bhar kar — **0 fail**.
- Asli wajah ye thi: `.remind-pill` `position:absolute; bottom:8px` tha par
  `.bottombar` par `position:relative` **nahi** tha. Is liye wo `.hud`
  (height:100vh) ke against position hua, yaani viewport ke bilkul neeche —
  1366x768 par y=746..760, jabki quick-button label (.qlbl) y=745..754.
  Yaani reminder text un label par **chadh** diya tha aur bar ke apne
  bottom edge se 4px neeche. `.notice`/`.micflag` (`bottom:84px`) bhi
  left/right panels par chadh rahe the, `.brainwarn` (`top:6px`) topbar par.

Ye test wahi baat dobara check karta hai — browser me, har size par.
Screenshot `%TEMP%\\opencode` me (repo me NAHI).
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import hudcheck_bar  # noqa: E402

FAILED = hudcheck_bar.FAILED
if __name__ == "__main__":
    hudcheck_bar.main()
    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        sys.exit(1)
    print("HUD bar test pass (Playwright headless, nakli data).")