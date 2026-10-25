"""STEP 1: naam "Sunday" -> "Jarvis". Config-driven, aur UI me purana naam nahi.

Ye test teen cheezein pakadta hai:

Wake phrase + grammar ka test ab `tests/test_wake_phrases.py` me hai (5-Oct
split, 200-line niyam). Yahan bacha hai:

1. **UI text me "Sunday" na bache** — `ui/*.js` + `ui/*.html` grep. Do cheezein
   jaan-boojh kar bachayi hain: `hud_clock.js` ka weekday `DAYS` array (wo
   calendar ka din hai, assistant ka naam nahi) aur `x-jarvis-token` jaise
   **internal** ids (token/security ka hissa hai, naam nahi).

Koi asli Vosk/mic/API nahi.
"""

import re
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from core import modes
from server import app as server_app

ROOT = Path(__file__).resolve().parent.parent
UI_DIR = ROOT / "ui"

# `x-jarvis-token` / `JARVIS_*` / meta `prabh-*` — token + security ka hissa hai.
INTERNAL_RE = re.compile(r"prabh[-_]|JARVIS_", re.IGNORECASE)

# ---- UI scan ka rule (teen chhoti baatein jaan-boojh kar) -------------------
#
# 1. **Comment** lines chhoot dete hain — wahan "sunday" sirf padhne ke liye hai.
# 2. **Mode id** `"sunday"` (chhote akshar, quoted) jaane diya jaata hai. Ye
#    internal id hai (Step 1 me naam badla, id nahi) aur kabhi screen par nahi
#    aata — sirf `voice_for()` jaise lookup me jaata hai.
# 3. `hud_clock.js` ka `DAYS` array **calendar ka din** hai, assistant ka naam
#    nahi — warna Sunday ka din galat dikhta.
#
# Baaqi har "Sunday"/"sunday" ek user-visible string hai aur FAIL hona chahiye.
COMMENT_MARK = ("//", "*", "<!--")
MODE_ID = re.compile(r"""['"]sunday['"]""")
ALLOWED_FILES = {"hud_clock.js": ['"Sunday", "Monday"']}


def ui_files() -> list:
    return sorted([*UI_DIR.glob("*.js"), *UI_DIR.glob("*.html")],
                  key=lambda p: p.name)


def offenders() -> list:
    """-> [(file, line_no, text)] — jahan "Sunday" user ko dikhta hai."""
    bad = []
    for path in ui_files():
        for no, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            if "sunday" not in line.lower():
                continue
            if any(mark in line for mark in COMMENT_MARK):   # (1)
                continue
            if INTERNAL_RE.search(line):                     # prabh-token
                continue
            if MODE_ID.search(line):                         # (2)
                continue
            if any(token in line for token in ALLOWED_FILES.get(path.name, [])):
                continue                                    # (3)
            bad.append((path.name, no, line.strip()))
    return bad


def render_index() -> str:
    """`GET /` wala HTML — asli `server.app.fill_html()` se, server chala ke nahi."""
    html = (UI_DIR / "index.html").read_text(encoding="utf-8")
    return server_app.fill_html(html)


class TestName(unittest.TestCase):
    """Naam + wake phrase."""

    def test_assistant_name(self):
        self.assertEqual(config.ASSISTANT_NAME, "Jarvis")
        self.assertEqual(config.DISPLAY_NAME, "J.A.R.V.I.S")

    def test_display_name_is_jarvis(self):
        # Mode id "sunday" hai, par dikhne wala naam Jarvis.
        self.assertEqual(modes.display_name("sunday"), "Jarvis")
        self.assertEqual(modes.label("sunday"), "JARVIS")
        self.assertEqual(modes.label("prabh"), "PRABH")

    def test_persona_is_jarvis(self):
        # Persona file ka naam badla (jarvis.txt), mode id wahi.
        self.assertEqual(config.PERSONA_FILES["sunday"], "jarvis.txt")
        self.assertTrue((ROOT / "personas" / "jarvis.txt").is_file())
        first = modes.persona_for("sunday").splitlines()[0]
        self.assertIn("Jarvis", first)

    def test_tray_and_shortcut(self):
        self.assertEqual(config.HUD_SHORTCUT_NAME, "Jarvis HUD")
        for state in (config.TRAY_OFF, config.TRAY_LISTENING, config.TRAY_ERROR):
            self.assertTrue(config.tray_title(state).startswith("Jarvis"),
                            config.tray_title(state))
        # Single-instance message bhi user-facing hai.
        msg = config.ASSISTANT_NAME
        self.assertTrue(msg.startswith("Jarvis"))

    def test_prabh_dormant(self):
        # Prabh ka apna naam + persona waise hi, sirf dormant.
        self.assertEqual(modes.display_name("prabh"), "Prabh")
        self.assertTrue(config.SUNDAY_ONLY)
        self.assertEqual(modes.detect_mode("Prabh, kya haal", "sunday")[0],
                         "sunday")


class TestUiHasNoSunday(unittest.TestCase):
    """Grep proof — UI text me "Sunday" nahi rehna chahiye."""

    def test_no_sunday_in_ui(self):
        bad = offenders()
        self.assertEqual(bad, [], "UI me Sunday bacha: %s" % bad)

    def test_ui_says_jarvis(self):
        html = (UI_DIR / "index.html").read_text(encoding="utf-8")
        # Naam **config se** aata hai (server `/` placeholder replace karta hai) —
        # is liye HTML me "Jarvis" hard-code nahi, placeholder hai.
        self.assertIn("<title>__JARVIS_ASSISTANT_NAME__ HUD</title>", html)
        self.assertIn('name="jarvis-name" content="__JARVIS_ASSISTANT_NAME__"', html)
        self.assertIn('id="brand">__JARVIS_DISPLAY_NAME__<', html)
        self.assertIn('id="orbMode">__JARVIS_DISPLAY_NAME__<', html)

    def test_server_replaces_name_placeholders(self):
        # `GET /` par placeholder sach me badal jaana chahiye. Sirf file me
        # dekhte hi kaafi nahi — jaisa Phase 4 me `hud_check_get.py` ka bug tha.
        served = render_index()
        self.assertNotIn("__JARVIS_ASSISTANT_NAME__", served)
        self.assertNotIn("__JARVIS_DISPLAY_NAME__", served)
        self.assertIn("<title>Jarvis HUD</title>", served)
        self.assertIn('id="brand">J.A.R.V.I.S<', served)

    def test_allowed_exceptions_still_allowed(self):
        # Jo bachaya gaya hai wo sach me maujoud hona chahiye — warna ye test
        # chup-chaap kuch bhi chhod dega.
        clock = (UI_DIR / "hud_clock.js").read_text(encoding="utf-8")
        self.assertIn('"Sunday", "Monday"', clock)   # weekday, sahi


if __name__ == "__main__":
    unittest.main(verbosity=2)
