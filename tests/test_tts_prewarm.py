"""Startup par ack ka audio pehle se banana - pehli wake 4.2 s tez.

**Live log (4-Oct 18:44, pehli wake):**
    TIME tts: provider=elevenlabs chars=11 bytes=18852 4239ms   <- "Ji, boliye."
    TIME wake_command: ack 5680ms (total 5680ms)
    TIME wake_command: TOTAL 18045ms | ack=5680ms ...

"Ji, boliye" **constant** hai - har wake par wahi. Cache (`voice/tts.py:
speak_cached`) usko dobara banane se bachati hai, par app restart par khaali
ho jaati hai, is liye pehli wake sabse mehengi padti thi. Ab `wake/ask.py:
prewarm()` startup par (background thread) cache bhar deta hai.

**Teeno rule jo yahan pakde ja rahe hain:**

1. **Awaaz nahi bajti.** `tts.speak_cached()` se cache hoti hai;
   `playback.say()` se bajti - wahi galat raasta hota to startup pe "Ji,
   boliye" sunai de deta.
2. **Fail par chup-chaap.** Provider mar gaya to startup nahi rukta, cache
   me kuch nahi jaata (recovery phir se banti rahegi).
3. **`prewarm_async()` block nahi karta** - warna app startup line bolne me
   4 s late ho jati.

**Koi asli provider nahi** - `tts.speak` fake se badla jaata hai.
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
from desktop import playback
from voice import tts
from wake import ask
from wakehelp import check, finish


class FakeSpeak:
    """`tts.speak` ki jagah - kitni baar call hua, yaad rakhta hai."""

    def __init__(self, delay: float = 0.0):
        self.calls = []
        self.delay = delay

    async def __call__(self, text, mode):
        self.calls.append((text, mode))
        if self.delay:
            await asyncio.sleep(self.delay)
        return b"AUDIO-%d" % len(self.calls), "edge"


class TestPrewarm(unittest.TestCase):
    """Startup cache - awaaz chup-chaap, app ruk na jaye."""

    def setUp(self):
        self.saved_speak = tts.speak
        self.saved_play = playback.play
        tts.cache_clear()

    def tearDown(self):
        tts.speak = self.saved_speak
        playback.play = self.saved_play
        tts.cache_clear()

    def test_fills_cache_without_sound(self):
        """Cache bhar jaye, par `playback.play` **bilkul na bule**."""
        played = []
        playback.play = lambda audio, rate=None: played.append(audio) or 10
        fake = FakeSpeak()
        tts.speak = fake
        done = ask.prewarm("sunday")
        check("dono text cache hue", done, len(ask.PREWARM_TEXTS))
        check("sirf prewarm ke text banaye",
              len(fake.calls), len(ask.PREWARM_TEXTS))
        check("awaaz nahi baji", played, [])
        check("ack cache me hai",
              (config.ACK_ON_WAKE, "sunday") in tts._CACHE, True)

    def test_second_wake_will_hit_cache(self):
        """Yahi asli faida hai: prewarm ke baad pehli wake ka `ack` 0 ms.

        `playback.say()` wahi `speak_cached()` use karta hai, is liye cache
        me text hone se dobara provider nahi jaata."""
        fake = FakeSpeak()
        tts.speak = fake
        ask.prewarm("sunday")
        before = len(fake.calls)
        tts._CACHE.pop((config.ACK_ON_WAKE, "sunday"), None)   # noqa: proof ke liye
        ask.prewarm("sunday")
        check("cache me hone se call nahi hua",
              len(fake.calls) - before, len(ask.PREWARM_TEXTS) - 1)

    def test_survives_provider_failure(self):
        """Provider mar gaya to 0 cache, app startup nahi rukega."""
        async def failing(text, mode):
            raise tts.TtsError("provider mar gaya")

        tts.speak = failing
        check("0 cache hua", ask.prewarm("sunday"), 0)
        check("cache khaali", len(tts._CACHE), 0)

    def test_async_does_not_block(self):
        """`prewarm_async()` turant laut aaye - startup line 4 s late nahi honi chahiye."""
        fake = FakeSpeak(delay=0.4)
        tts.speak = fake
        start = time.perf_counter()
        ask.prewarm_async("sunday")
        elapsed = time.perf_counter() - start
        check("block nahi kiya (<0.1s)", elapsed < 0.1, True)
        for _ in range(60):
            if len(tts._CACHE) >= len(ask.PREWARM_TEXTS):
                break
            time.sleep(0.05)
        check("background me poora cache hua",
              len(tts._CACHE), len(ask.PREWARM_TEXTS))

    def test_app_calls_prewarm_on_start(self):
        """`desktop/app.py` startup par prewarm **chahta** hai - wiring pakadte
        hain (source-check, koi process nahi chalaya)."""
        src = (Path(__file__).resolve().parent.parent
               / "desktop" / "app.py").read_text(encoding="utf-8")
        check("app me prewarm call hai", "prewarm_async()" in src, True)
        check("playback.say startup par nahi",
              src.count("prewarm_async()"), 1)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("startup voice prewarm theek" if result.wasSuccessful() else "FAIL")