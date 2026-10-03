"""Ack audio ka cache — Step 2 speed fix ka pehla hissa.

Log me kya tha (3 Oct):
    TIME wake_command: TOTAL 18450ms | ack=3520ms ...
    TIME tts: provider=elevenlabs mode=sunday voice=..RZzb chars=32 1446ms

"Ji, boliye" **constant** hai — har wake par wahi. Uska TTS har baar dobara
 banane me 1.4-1.8 s lag raha tha, jo poore flow ka sabse bada chunk tha.
 Ab `voice/tts.py: speak_cached()` pehli baar banata hai, phir memory se
 (`desktop/playback.say()` usi par jaata hai).

**Koi asli provider nahi** — `tts.speak` ko fake se badla jaata hai aur dekha
jaata hai ki dobara call hua ya nahi. Do nateein is liye jaan-boojh kar rakhi
gai hain:

1. **Fail cache nahi hota** — warna app hamesha "nahi bola" repeat karegi jab tak
   cache na bhare, aur recovery kabhi nahi hogi.
2. **Cache bounded hai** — chat ke jawab `speak_cached()` se mat bhejo (unique
   text), warna memory har message badhti rahegi.
"""

import asyncio
import sys
import time
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voice import tts
from wakehelp import check, finish


class FakeSpeak:
    """`tts.speak` ki jagah — kitni baar call hua, ye yaad rakhta hai."""

    def __init__(self):
        self.calls = []

    async def __call__(self, text, mode):
        self.calls.append((text, mode))
        return b"AUDIO-%d" % len(self.calls), "edge"


class TestAckCache(unittest.TestCase):
    """Cache ke gyaan-te pakkaure."""

    def setUp(self):
        self.saved = tts.speak
        tts.cache_clear()

    def tearDown(self):
        tts.speak = self.saved
        tts.cache_clear()

    def test_second_call_hits_cache(self):
        fake = FakeSpeak()
        tts.speak = fake
        a1, p1 = asyncio.run(tts.speak_cached("Ji, boliye.", "sunday"))
        a2, p2 = asyncio.run(tts.speak_cached("Ji, boliye.", "sunday"))
        check("provider ek hi call hua", len(fake.calls), 1)
        check("same audio", a1, a2)
        check("same provider", p1, p2)

    def test_cache_hit_really_faster(self):
        """Yahi asli proof hai — bina iske test kuch nahi pakadta."""

        async def slow(text, mode):
            await asyncio.sleep(0.20)
            return b"X", "edge"

        tts.speak = slow
        start = time.perf_counter()
        asyncio.run(tts.speak_cached("Ji, boliye.", "sunday"))
        first = time.perf_counter() - start
        start = time.perf_counter()
        asyncio.run(tts.speak_cached("Ji, boliye.", "sunday"))
        second = time.perf_counter() - start
        check("dusra call 50 ms se kam", second < 0.05, True)
        check("pehla call asli waqt laga", first > 0.15, True)

    def test_different_mode_and_text_are_separate(self):
        fake = FakeSpeak()
        tts.speak = fake
        asyncio.run(tts.speak_cached("Ji, boliye.", "sunday"))
        asyncio.run(tts.speak_cached("Ji, boliye.", "prabh"))
        asyncio.run(tts.speak_cached("confirm kijiye", "sunday"))
        check("teeno alag key", len(fake.calls), 3)

    def test_cache_clear_works(self):
        fake = FakeSpeak()
        tts.speak = fake
        asyncio.run(tts.speak_cached("x", "sunday"))
        tts.cache_clear()
        asyncio.run(tts.speak_cached("x", "sunday"))
        check("clear ke baad dobara call", len(fake.calls), 2)
        check("cache me sirf naya", len(tts._CACHE), 1)

    def test_cache_is_bounded(self):
        fake = FakeSpeak()
        tts.speak = fake
        for i in range(tts.CACHE_MAX + 4):
            asyncio.run(tts.speak_cached("phrase %d" % i, "sunday"))
        check("cache bounded hai", len(tts._CACHE) <= tts.CACHE_MAX, True)

    def test_error_is_not_cached(self):
        """Provider fail hua to cache me kuch nahi jana chahiye — warna app
        hamesha "nahi bola" repeat karegi, jab tak cache bhare na."""
        boom = {"n": 0}

        async def failing(text, mode):
            boom["n"] += 1
            raise tts.TtsError("provider mar gaya")

        tts.speak = failing
        for _ in range(2):
            try:
                asyncio.run(tts.speak_cached("Ji, boliye.", "sunday"))
            except tts.TtsError:
                pass
        check("fail par cache khaali", len(tts._CACHE), 0)
        check("dobaara try hua", boom["n"], 2)

    def test_cache_only_on_the_cached_route(self):
        """`_speak_uncached()` seedha call karne par cache **bilkul khaali**
        rahega. Yahi wajah hai asli raasta sirf ek rakhna — har call-site ko
        alag-alag cache yaad rakhni nahi parti.

        Yahan `tts.PROVIDERS` fake karna pada (fake `speak` nahi, kyunki
        `_speak_uncached` jaan-boojh kar `speak()` ko **nahi** bulata)."""
        class FakeProvider:
            calls = 0

            async def speak(self, text, mode, voice=None):
                FakeProvider.calls += 1
                return b"EDGE", "edge"

        saved = dict(tts.PROVIDERS)
        tts.PROVIDERS.update(elevenlabs=FakeProvider(), cartesia=FakeProvider(),
                             edge=FakeProvider())
        try:
            asyncio.run(tts._speak_uncached("ek lambi jawani", "sunday"))
            asyncio.run(tts._speak_uncached("ek lambi jawani", "sunday"))
        finally:
            tts.PROVIDERS.clear()
            tts.PROVIDERS.update(saved)
        check("cache khaali", len(tts._CACHE), 0)
        check("dobaara provider gaya", FakeProvider.calls, 2)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("ack audio cache theek" if result.wasSuccessful() else "FAIL")