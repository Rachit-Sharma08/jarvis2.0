"""KAAM 4: tez jawab — awaaz chhoti, fixed jawab ka cache.

Do hisse:

1. **Awaaz 1-2 poore vaakya** (`tts_text.voice_answer`). Pehle `clip_answer()`
   220 **char** par kaatta tha, jo beech se vaakya tod sakta tha. Ab pehle
   vaakya pura bolta hai; limit aayi to wahi purana kaat.
2. **Time/date jawaab ka cache** (`voice/answer_cache.py`). `get_time_date`
   `core/directreply.py` me DIRECT_TOOL hai — yaani uska jawab LLM se nahi,
   seedha tool-result se aata hai, aur har baar **naya text** hota hai
   ("Abhi 3:20 ho raha hai"). Purana cache `(text, mode)` tha, to iska
   **kabhi hit nahi** hua aur TTS har sawal dobara banti thi. Ab volatile
   jawab ka key me **minute ka bucket** judta hai.

**HUD par poora jawab rehta hai** — ye dono sirf awaaz wale raaste par hain.
Koi TTS provider nahi chalta: `tts.speak` fake se badla jaata hai.
"""

import asyncio
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
from tests.wakecmdhelp import patch
from voice import answer_cache, tts, tts_text

LONG = ("Aaj mausam saaf hai. Bahut dhoop hai. Dhoop me lamba nahi chalna "
        "chahiye. Chai piyo aur paani bhi.")


class TestVoiceAnswer(unittest.TestCase):
    """Awaaz: pehle 1-2 **poore** vaakya."""

    def test_takes_two_sentences(self):
        check("do vaakya liye",
              tts_text.voice_answer(LONG), "Aaj mausam saaf hai. Bahut dhoop hai.")

    def test_one_sentence_answer_unchanged(self):
        check("ek vaakya waisa hi", tts_text.voice_answer("Chai laao."),
              "Chai laao.")

    def test_never_cuts_mid_sentence(self):
        """Purana `clip_answer` 220 char par beech se kaat sakta tha."""
        got = tts_text.voice_answer(LONG)
        check("vaakya pura hai", got.endswith("."), True)
        check("tee vaakya nahi aayi", "Dhoop me lamba" in got, False)

    def test_respects_char_limit(self):
        big = " ".join(["Ye ek lambi baat hai jo chalegi."] * 30)
        check("limit ke andar", len(tts_text.voice_answer(big)) <=
              config.VOICE_ANSWER_MAX_CHARS, True)

    def test_sentences_helper(self):
        check("4 vaakya mile", len(tts_text.sentences(LONG)), 4)
        check("bina full stop = 1", len(tts_text.sentences("koi vaakya nahi")), 1)
        check("khaali text", tts_text.sentences(""), [])
        check("danda bhi vaakya todta hai",
              len(tts_text.sentences("Pehla। Doosra। Teesra।")), 3)

    def test_config_default_two(self):
        check("default 2 vaakya", config.VOICE_SENTENCES, 2)
        check("waisa hi 1-2 ke beech", 1 <= config.VOICE_SENTENCES <= 3, True)

    def test_empty_and_none_safe(self):
        check("khaali", tts_text.voice_answer(""), "")
        check("None", tts_text.voice_answer(None), "")

    def test_command_uses_voice_answer(self):
        """Asli wiring: `wake/command.py` `clip_answer` ki jagah."""
        src = (ROOT / "wake" / "command.py").read_text(encoding="utf-8")
        check("voice_answer use hua", "tts.voice_answer(" in src, True)
        check("purana clip_answer nahi", "tts.clip_answer(answer)" in src, False)

    def test_re_exported_from_tts(self):
        """`tts.voice_answer` se bhi mile (tests aur `command.py` yahi use karte
        hain — ek hi raasta)."""
        check("re-export", tts.voice_answer(LONG),
              tts_text.voice_answer(LONG))


class TestAnswerCacheKey(unittest.TestCase):
    """(2) key: static waisa, volatile me minute ka bucket."""

    def test_detects_volatile(self):
        for text in ("Abhi 3:20 ho raha hai", "3 ghante 20 minute ho gaye",
                     "shaam 7 pm ho gayi", "14 October 2026"):
            check(f"volatile: {text[:18]}", answer_cache.is_volatile(text), True)
        for text in ("Ji, boliye.", "Screen par confirm kijiye.",
                     "WhatsApp khol diya", "4 files likh diye"):
            check(f"static: {text[:18]}", answer_cache.is_volatile(text), False)

    def test_static_key_unchanged(self):
        """Purana cache key bilkul waisa — prewarm aur tts_cache safe."""
        check("static key shape", answer_cache.key("Ji, boliye.", "sunday"),
              ("Ji, boliye.", "sunday"))

    def test_same_minute_hits(self):
        a = answer_cache.key("Abhi 3:20", "sunday", now=1000)      # minute 16
        b = answer_cache.key("Abhi 3:20", "sunday", now=1010)      # minute 16
        check("usi minute me same key", a, b)

    def test_next_minute_is_new(self):
        a = answer_cache.key("Abhi 3:20", "sunday", now=1000)      # minute 16
        b = answer_cache.key("Abhi 3:20", "sunday", now=1061)      # minute 17
        check("agli minute nayi key", a != b, True)

    def test_bucket_is_minute(self):
        check("bucket minute", answer_cache.bucket(now=1000), 16)
        check("minute badla", answer_cache.bucket(now=1061), 17)

    def test_mode_still_part_of_key(self):
        check("mode alag rasta",
              answer_cache.key("x", "sunday", now=1000) !=
              answer_cache.key("x", "prabh", now=1000), True)


class TestCacheWiring(unittest.TestCase):
    """`speak_cached()` ab `answer_cache.key()` use karta hai."""

    def test_cache_hit_within_minute(self):
        """Do "abhi 3:20" puchho (usi minute) → provider **ek** hi baar."""
        calls = []

        async def fake_speak(text, mode):
            calls.append(text)
            return b"AUDIO", "edge"

        tts.cache_clear()
        with patch(tts, "speak", fake_speak), \
                patch(answer_cache, "bucket", lambda now=None: 7):
            for _ in range(3):
                asyncio.run(tts.speak_cached("Abhi 3:20 ho raha hai", "sunday"))
        check("provider 1 hi baar", len(calls), 1)
        check("cache me hai", len(tts._CACHE), 1)

    def test_new_minute_rebuilds(self):
        calls = []

        async def fake_speak(text, mode):
            calls.append(text)
            return b"AUDIO", "edge"

        tts.cache_clear()
        buckets = [7, 7, 8]        # pehla 7, doosra 7 (hit), teesra 8 (miss)

        def fake_bucket(now=None):
            return buckets.pop(0) if len(buckets) > 1 else buckets[0]

        with patch(tts, "speak", fake_speak), \
                patch(answer_cache, "bucket", fake_bucket):
            for _ in range(3):
                asyncio.run(tts.speak_cached("Abhi 3:20 ho raha hai", "sunday"))
        check("agli minute me dobara bana", len(calls), 2)

    def test_static_still_hits_forever(self):
        calls = []

        async def fake_speak(text, mode):
            calls.append(text)
            return b"AUDIO", "edge"

        tts.cache_clear()
        with patch(tts, "speak", fake_speak):
            for _ in range(3):
                asyncio.run(tts.speak_cached("Ji, boliye.", "sunday"))
        check("static 1 hi baar", len(calls), 1)
        tts.cache_clear()

    def test_cache_stays_bounded(self):
        """Naye keys memory tez bharayein — CACHE_MAX abhi bhi chalti hai."""
        check("bounded hai", tts.CACHE_MAX <= 16, True)
        check("bounded value", tts.CACHE_MAX, 8)

    def test_tts_uses_answer_cache(self):
        src = (ROOT / "voice" / "tts.py").read_text(encoding="utf-8")
        check("answer_cache.key use hai", "answer_cache.key(text, mode)" in src, True)
        check("purana raw tuple nahi", "key = (text, mode)" in src, False)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("tez jawab" if result.wasSuccessful() else "FAIL")
