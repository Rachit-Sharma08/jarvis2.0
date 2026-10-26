"""Groq girne par local STT - `auto` me JARVIS behra nahi hota.

**Kyun:** pehle `provider()` key hone par "groq" chun leta tha aur Groq ka
network/429/5xx error seedha user tak jata tha ("Sun nahi paya"). Key hone par
bhi JARVIS behra - wahi purana bug, doosre raaste se.

Do niyam yahan pakde ja rahe hain:
1. Turant error (network/429/5xx) par local model se sun lo.
2. **Timeout par nahi** - budget khatam hone ke baad local 75 s aur leta,
   caller ko turant saaf message chahiye (`test_stt_speed.py` ka niyam).

Asli network kabhi nahi - `_transcribe` fake hai.
"""

import asyncio
import sys
import unittest
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.stthelper import FakeModel, wav_bytes
from tests.wakehelp import check, finish
from voice import stt, stt_local

AUDIO = wav_bytes(np.full(16000, 0.2, dtype=np.float32))


class TestFallback(unittest.TestCase):
    def setUp(self):
        self.saved = (config.STT_LOCAL, config.has_groq, stt_local.available,
                      stt_local._MODEL, stt._transcribe)
        config.STT_LOCAL = "auto"
        config.has_groq = lambda: True
        stt_local.available = lambda: True
        stt_local._MODEL = FakeModel(text="local ne suna")

    def tearDown(self):
        (config.STT_LOCAL, config.has_groq, stt_local.available,
         stt_local._MODEL, stt._transcribe) = self.saved

    def run_stt(self):
        async def go():
            return await stt.transcribe(AUDIO, 1200)
        return asyncio.run(go())

    def test_groq_error_local_par(self):
        def boom(_audio):
            raise ConnectionError("429 rate limit")
        stt._transcribe = boom
        check("Groq gira to local sunta hai", self.run_stt(), "local ne suna")

    def test_groq_timeout_fallback_nahi(self):
        def slow(_audio):
            raise TimeoutError("deadline 6.0s")
        stt._transcribe = slow
        with self.assertRaises(stt.SttError) as box:
            self.run_stt()
        check("timeout par saaf message", "waqt" in str(box.exception), True)

    def test_forced_groq_fallback_nahi(self):
        config.STT_LOCAL = "groq"

        def boom(_audio):
            raise ConnectionError("down")
        stt._transcribe = boom
        with self.assertRaises(stt.SttError):
            self.run_stt()

    def test_local_bhi_gire_to_saaf_error(self):
        def boom(_audio):
            raise ConnectionError("groq down")
        stt._transcribe = boom
        stt_local._MODEL = None
        stt_local.available = lambda: False
        with self.assertRaises(stt.SttError) as box:
            self.run_stt()
        check("message me Groq ka reason", "groq down" in str(box.exception), True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("STT fallback theek" if result.wasSuccessful() else "FAIL")
