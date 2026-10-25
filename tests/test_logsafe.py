"""KAAM 0: test ka log asli `logs/jarvis.log` se alag.

**Galti jo thi:** `logs/jarvis.log` ek hi file — app aur test dono likhte the.
S-1 audit me isi wajah se mic ka asli level galat nikaala gaya tha
(`tests/wakehelp.py` ka `loud()` = RMS **exactly 0.129**, aur wahi number
asli app ke log me bhi aa raha tha).

**Raasta:** `config.py` ka `LOG_DIR` `JARVIS_LOG_DIR` env se aata hai;
`tests/logsafe.py` wo env **import ke time** set karta hai. Har test file me

Ye test do baatein pakadta hai:
1. Har test file me wo import hai (`config` seedha ya helper ke through).
2. Test likhta hai **temp** log me, aur `logs/jarvis.log` bilkul nahi chhuta.

**App chalu nahi kiya gaya** — sirf file check + logger se ek line.
"""

import logging
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.wakehelp import check, finish

STAMP = "TESTLOGSAFETY-PROBE-7731"


class TestLogLocation(unittest.TestCase):
    """Log kaha jaa raha hai."""

    def test_not_app_log(self):
        check("config.LOG_DIR asli logs/ nahi hai",
              config.LOG_DIR.resolve(), logsafe.LOG_DIR.resolve())
        check("app wala folder nahi",
              config.LOG_DIR.resolve() == (ROOT / "logs").resolve(), False)

    def test_log_file_under_temp(self):
        check("LOG_FILE temp ke andar hai",
              str(config.LOG_FILE.resolve()).lower().startswith(
                  str(logsafe.LOG_DIR.resolve()).lower()), True)

    def test_writes_go_to_temp_log(self):
        """Asli logger se line likhwa kar dekho kaha gira."""
        logsafe.clear()
        from log_setup import get_logger
        get_logger("logsafe_probe").warning(STAMP)
        text = logsafe.read()
        check("temp log me mila", STAMP in text, True)
        check("app log me nahi mila",
              self._app_log_has(STAMP), False)

    def _app_log_has(self, needle):
        app_log = ROOT / "logs" / "jarvis.log"
        if not app_log.exists():
            return False
        return needle in app_log.read_text(encoding="ascii", errors="replace")

    def test_config_honours_env(self):
        """`JARVIS_LOG_DIR` env se badalta hai (`.env` wale knob jaisa)."""
        import importlib
        import os
        saved = os.environ.get("JARVIS_LOG_DIR")
        want = logsafe.LOG_DIR.parent / "prabh-test-logs-alt"
        os.environ["JARVIS_LOG_DIR"] = str(want)
        try:
            import config as config_mod
            reloaded = importlib.reload(config_mod)
            check("env ka folder mila", reloaded.LOG_DIR.resolve(),
                  want.resolve())
        finally:
            if saved is None:
                os.environ.pop("JARVIS_LOG_DIR", None)
            else:
                os.environ["JARVIS_LOG_DIR"] = saved
            importlib.reload(config)

    def test_no_test_file_writes_app_log(self):
        """Har `tests/test_*.py` me `logsafe` import hona chahiye."""
        missing = []
        for path in sorted((ROOT / "tests").glob("test_*.py")):
            if "logsafe" not in path.read_text(encoding="utf-8"):
                missing.append(path.name)
        check(f"sab {len(list((ROOT / 'tests').glob('test_*.py')))} test file me logsafe",
              missing, [])


class TestPrivacy(unittest.TestCase):
    """Test log bhi wahi ASCII rule follow kare (AGENTS ka pakkaura)."""

    def test_ascii_only(self):
        logsafe.clear()
        from log_setup import get_logger
        before = 0
        try:
            before = config.LOG_FILE.stat().st_size
        except OSError:
            before = 0
        get_logger("logsafe_ascii").error("em-dash \u2014 -> %s", "ok")
        raw = config.LOG_FILE.read_bytes()
        check("non-ASCII byte nahi", [b for b in raw[before:] if b > 127], [])
        check("message likhi", "em-dash" in logsafe.read(), True)


if __name__ == "__main__":
    logging.raiseExceptions = False
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("test ka log alag" if result.wasSuccessful() else "FAIL")
