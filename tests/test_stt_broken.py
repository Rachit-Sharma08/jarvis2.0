"""Toota local model yaad rehta hai - har command par dobara load nahi.

**Kyun:** pehle `_load()` ka exception sirf `warm_async` ke thread me pakda
jata tha. Model file kharab ho to har command 4 s load me barbaad karti aur
wahi error deti. Ab pehla fail `_BROKEN` me likha jata hai.

Asli model load nahi hota - `faster_whisper` module fake hai.
"""

import sys
import time
import types
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tests.wakehelp import check, finish
from voice import stt_local


class TestBrokenRemembers(unittest.TestCase):
    def setUp(self):
        self.saved = (stt_local._MODEL, stt_local._BROKEN,
                      sys.modules.get("faster_whisper"))
        stt_local._MODEL = None
        stt_local._BROKEN = ""

        def boom(*_a, **_kw):
            raise OSError("model file kharab")
        sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=boom)

    def tearDown(self):
        stt_local._MODEL, stt_local._BROKEN, old = self.saved
        if old is None:
            sys.modules.pop("faster_whisper", None)
        else:
            sys.modules["faster_whisper"] = old

    def test_load_fail_yaad(self):
        with self.assertRaises(OSError):
            stt_local._load()
        check("fail yaad raha", bool(stt_local._BROKEN), True)

    def test_doosri_call_turant(self):
        with self.assertRaises(OSError):
            stt_local._load()
        start = time.perf_counter()
        with self.assertRaises(RuntimeError):
            stt_local._load()
        check("doosri call 50ms se tez", time.perf_counter() - start < 0.05, True)

    def test_available_band(self):
        with self.assertRaises(OSError):
            stt_local._load()
        check("available() band", stt_local.available(), False)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("broken model yaad" if result.wasSuccessful() else "FAIL")
