"""S-2: STT tez + pakka — apna chhota timeout, 1 retry, aur ceiling.

**S-1 audit ka saboot:** `voice/stt.py` brain wala `BRAIN_TIMEOUT_GROQ` (10 s)
use karta tha aur Groq SDK 2 baar khud retry karta tha. 3.5 s ki audio par call
**43 s** tak atak sakta tha — user ko 43 s kuch nahi dikhta, sirf "Sun nahi paya"
baad me aata tha.

Teen rule yahan pakde ja rahe hain:

1. **STT ka apna timeout** (`STT_TIMEOUT_SECONDS = 6`) — brain wala nahi.
2. **`max_retries=1`** — SDK 3 koshish nahi, 2 koshish karta hai.
3. **Ceiling** (`config.stt_deadline()`) — SDK ke budget se upar. Usse zyada
   matlab app ka thread atka hai; caller turant aage badhta hai, saaf message
   ke saath.

**Koi asli Groq call nahi** — `voice.stt.Groq` aur `_transcribe` dono fake.
"""

import asyncio
import sys
import time
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
import config_brain
from tests.wakehelp import check, finish
from tests.wakecmdhelp import patch
from voice import stt


class FakeGroq:
    """`Groq(api_key=..., timeout=..., max_retries=...)` ka nakli — kwargs pakadta."""

    made = []

    def __init__(self, api_key="", timeout=None, max_retries=None, **_kw):
        FakeGroq.made.append({"key": api_key, "timeout": timeout,
                              "max_retries": max_retries})

    @property
    def audio(self):
        class _A:
            class transcriptions:
                @staticmethod
                def create(file=None, model=None, **_kw):
                    class R:
                        text = "namaste"
                    return R()
        return _A()


class TestSettings(unittest.TestCase):
    """Config numbers — `.env` se badalne ka raasta bhi."""

    def test_small_timeout_and_few_retries(self):
        check("STT timeout 6s", config.STT_TIMEOUT_SECONDS, 6.0)
        check("max_retries 1", config.STT_MAX_RETRIES, 1)

    def test_deadline_is_above_sdk_budget(self):
        budget = config.STT_TIMEOUT_SECONDS * (config.STT_MAX_RETRIES + 1)
        check("ceiling SDK ke budget se upar",
              config.stt_deadline() > budget, True)
        check("ceiling 16s (6*2+4)", config.stt_deadline(), 16.0)
        check("ceiling brain ke 10s se bada", config.stt_deadline() > 10.0, True)

    def test_env_can_override(self):
        import importlib
        import os
        import config_voice
        os.environ["JARVIS_STT_TIMEOUT"] = "3"
        os.environ["JARVIS_STT_RETRIES"] = "0"
        try:
            importlib.reload(config_voice)
            check("env se timeout 3", config_voice.STT_TIMEOUT_SECONDS, 3.0)
            check("env se retries 0", config_voice.STT_MAX_RETRIES, 0)
            check("retries 0 par ceiling = timeout+margin",
                  config_voice.stt_deadline(), 7.0)
        finally:
            os.environ.pop("JARVIS_STT_TIMEOUT", None)
            os.environ.pop("JARVIS_STT_RETRIES", None)
            importlib.reload(config_voice)

    def test_not_brain_timeout(self):
        """Purana bug: STT brain wala timeout uthata tha. `_client_kwargs`
        me asal numbers check hote hain — yahan source grep nahi (weak hota hai)."""
        src = (Path(__file__).resolve().parent.parent
               / "voice" / "stt.py").read_text(encoding="utf-8")
        check("timeout STT wala use hai",
              "timeout=config.STT_TIMEOUT_SECONDS" in src, True)
        check("max_retries pass kiya",
              "max_retries=config.STT_MAX_RETRIES" in src, True)
        check("daemon thread + deadline hai",
              "threading.Thread(target=run, daemon=True)" in src, True)


class TestClient(unittest.TestCase):
    """`_client()` sach me naye numbers use kare."""

    def setUp(self):
        FakeGroq.made.clear()

    def test_client_kwargs(self):
        with patch(config_brain, "GROQ_API_KEY", "test-key"), \
                patch(stt, "Groq", FakeGroq):
            stt._client()
        got = FakeGroq.made[0]
        check("timeout STT wala", got["timeout"], config.STT_TIMEOUT_SECONDS)
        check("retries 1", got["max_retries"], config.STT_MAX_RETRIES)
        check("brain wala timeout nahi", got["timeout"] == config.BRAIN_TIMEOUT_GROQ,
              False)


class TestCeiling(unittest.TestCase):
    """Hang par saaf message — thread atka nahi rehna chahiye."""

    def run_with(self, deadline, body, duration_ms=None):
        async def go():
            with patch(config_brain, "GROQ_API_KEY", "test-key"), \
                    patch(config, "stt_deadline", lambda: deadline), \
                    patch(stt, "_transcribe", body):
                return await stt.transcribe(b"RIFF-fake", duration_ms or 1500)
        return asyncio.run(go())

    def test_hang_gives_clean_error_fast(self):
        """SDK hang: caller ceiling par turant lautna chahiye.

        Ye S-1 ka asli point hai — `asyncio.run` (`wake/listen.py`) hung thread
        ka join wait karta hai, is liye sirf `asyncio.wait_for` kaafi nahi tha.
        3 s ka fake sleep diya hai: ceiling 0.25 s par bhi `asyncio.run` ka
        shutdown nahi aisa chala padega, warna test apne aap 3 s lega."""
        def slow(_audio):
            time.sleep(3.0)
            return "kabhi nahi"

        start = time.perf_counter()
        with self.assertRaises(stt.SttError) as box:
            self.run_with(0.25, slow)
        took = time.perf_counter() - start
        check("saaf message", "waqt" in str(box.exception), True)
        check(f"caller turant luta ({took:.2f}s, ceiling 0.25s)", took < 1.2, True)

    def test_fast_answer_still_works(self):
        text = self.run_with(5.0, lambda _a: "kaise ho")
        check("tez jawab wapas mila", text, "kaise ho")

    def test_provider_error_message_kept(self):
        def boom(_audio):
            raise RuntimeError("Connection error.")

        with self.assertRaises(stt.SttError) as box:
            self.run_with(5.0, boom)
        check("purana message shape", "Sun nahi paya" in str(box.exception), True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("STT tez + pakka" if result.wasSuccessful() else "FAIL")
