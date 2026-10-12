"""Phase 4 — HUD ka test runner.

Sirf yahan se sab checks chalte hain. Assertions do hisse me hain:
  `hud_check_ui.py`  — UI source, XSS, CSS, orb, clock, layout (browser-free)
  `hud_check_api.py` — weather/stats mock, endpoint security, gatekeeper
  `hud_common.py`    — `check()`/`read()`/`headers()` + file list (shared)

Yahan koi asli tool ya brain call nahi hota. Sab mock ya source-check.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from fastapi.testclient import TestClient

import config
import hud_check_api
import hud_check_get
import hud_check_ui
from hud_common import FAILED


def main():
    client = TestClient(__import__("server.app", fromlist=["app"]).app)

    hud_check_ui.run()
    hud_check_get.run(client)
    hud_check_api.run(client)

    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        sys.exit(1)
    print("HUD test pass.")


main()