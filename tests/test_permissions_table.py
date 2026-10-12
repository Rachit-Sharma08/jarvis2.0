"""Permissions v2 ki TABLE kahan hai — sirf placement aur purana table bhaara.

`test_permissions_v2.py` (apps + always-ask + injection) ka saathi, sirf do
sawaal:

1. `ALWAYS_ASK` / `NEVER_ALLOW` **config** me hain, `gatekeeper/rules.py` me
   hard-coded nahi — is liye badalna code chhede bina ho jaata hai.
2. **Har** faisle ke saath karan bhara hua hai (UI/log ke liye). Pehle
   `decide()` ke aakhir me `return base, ""` tha, jabki uski docstring
   "reason hamesha bhari hui" kehta tha.

Pure functions — koi tool chalta hi nahi.
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from gatekeeper import rules
from tests.wakehelp import check, finish


def why(tool, args):
    return rules.decide(tool, args)[1]


class TestConfigTable(unittest.TestCase):
    """(d) table config me hai, code me hard-coded nahi."""

    def test_tables_are_in_config(self):
        check("ALWAYS_ASK config me", len(config.ALWAYS_ASK) >= 7, True)
        check("NEVER_ALLOW config me", len(config.NEVER_ALLOW) >= 2, True)
        src = (ROOT / "gatekeeper" / "rules.py").read_text(encoding="utf-8")
        check("rules.py config se padhta hai",
              "config.ALWAYS_ASK" in src and "config.NEVER_ALLOW" in src, True)
        check("extra blocked patterns bhi maujood",
              len(config.EXTRA_BLOCKED_PATTERNS) >= 4, True)

    def test_every_reason_is_non_empty(self):
        """Har faisle ke saath karan bhi aana chahiye (log/UI ke liye)."""
        tools = [("run_command", {"command": "git push"}),
                 ("open_app", {"name": "nope"}),
                 ("list_dir", {"path": "C:/Windows"}),
                 ("get_time_date", {})]
        for tool, args in tools:
            check(f"{tool} ki wajah bhari hui", bool(why(tool, args)), True)


