"""Phase 4 HUD test ka shared helper — check/read/headers + file list.

`test_hud.py` sirf runner hai. Assertions do hisse me hain:
  `hud_check_ui.py` — UI source, XSS, CSS, orb, clock, layout (browser-free)
  `hud_check_api.py` — weather/stats mock + endpoint security + gatekeeper

Dono yahan se `check()`/`read()` import karte hain taaki FAILED ek hi jagah
jurta rahe.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

FAILED = []
GOOD_HOST = f"localhost:{config.SERVER_PORT}"
GOOD_ORIGIN = f"http://localhost:{config.SERVER_PORT}"

UI = config.UI_DIR

# Har UI file — naye Phase 4 files + purane + KAAM B ke arc files.
# Arc sirf tab boot hota hai jab `data-theme === "arc"` ho, par XSS/line
# limit ka niyam **dono** theme par lagta hai — is liye ye list me hain.
UI_JS = ("app.js", "tools.js", "hud_clock.js", "hud_stats.js", "hud_activity.js",
         "hud_status.js", "hud_orb.js", "hud_weather.js", "hud_quick.js",
         "recorder.js", "speaker.js", "voice_ui.js",
         "arc_config.js", "arc_reactor.js", "arc_dom.js", "arc_live.js",
         "arc_shell.js", "arc_wire.js", "arc_boot.js", "arc_load.js")
UI_CSS = ("hud_base.css", "hud_panel.css", "hud_left.css", "hud_center.css",
          "hud_right.css", "hud_bottom.css", "hud_card.css", "fonts.css",
          "arc.css", "arc_layout.css", "arc_core.css", "arc_bottom.css")


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def read(name):
    """UI ka source text (sirf padhna, kabhi koi file chhoota nahi)."""
    return (UI / name).read_text(encoding="utf-8")


def headers(token):
    return {"host": GOOD_HOST, "origin": GOOD_ORIGIN, "x-prabh-token": token}