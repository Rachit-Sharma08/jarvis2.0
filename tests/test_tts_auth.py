"""S-2: ElevenLabs ka 401 **ek baar** — phir seedha Edge.

**Asli wajah (S-1 me pakdi):** `brain/health_words.py` me 401 ka koi pattern hi
nahi tha. `CODE_RE` sirf `402|429|500|502|503` tha, is liye 401 `"other"` ban
kar `classify_and_skip()` se **guzar hi nahi pata tha** (wo sirf
`busy/billing/auth/empty` par kuch karta hai). Matlab har jawab me ElevenLabs
dobara poochha jaata tha — `TIME tts: elevenlabs-fail 957ms` log me.

Do rule yahan pakde ja rahe hain:

1. **401 -> `auth` -> is session me BAND.** Ek baar log, phir Edge.
2. **Key khaali ho to bilkul try na ho** — voice id check alag hai, pehle yahi
   missing tha, is liye network call bekaar jaata tha.

**Koi asli provider nahi** — `tts.PROVIDERS` fake se badla jaata hai.
"""

import asyncio
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import config_voice
from brain import health
from tests.wakehelp import check, finish
from tests.wakecmdhelp import patch
from voice import tts

AUTH_401 = ("ElevenLabs error: Client error '401 Unauthorized' for url "
            "'https://api.elevenlabs.io/v1/text-to-speech/xxxx'")


class FakeProvider:
    """`tts.PROVIDERS[name].speak` ka nakli — sirf **bytes** (asli bhi yahi
    deta hai), plus kitni baar bula aur kya fail karta."""

    def __init__(self, fail=None):
        self.calls = []
        self.fail = fail

    async def speak(self, text, mode):
        self.calls.append((text, mode))
        if self.fail:
            raise self.fail
        return b"AUDIO" * 10


def chain(fake_map):
    return patch(tts, "PROVIDERS", fake_map)


class TestClassify(unittest.TestCase):
    """401/403 ab `auth` hai — aur purane categories nahi bigde."""

    def setUp(self):
        health.reset_all()

    def tearDown(self):
        health.reset_all()

    def test_401_is_auth(self):
        check("401 = auth", health.classify(Exception(AUTH_401)), "auth")
        check("403 = auth", health.classify(Exception("403 Forbidden")), "auth")
        check("unauthorized word",
              health.classify(Exception("Unauthorized")), "auth")
        check("invalid api key word",
              health.classify(Exception("invalid_api_key")), "auth")

    def test_old_categories_intact(self):
        """Ye pehle se the — naya pattern inhe chhed nahi sakta."""
        check("429 = busy", health.classify(Exception("429 Rate Limit Error")), "busy")
        check("503 = busy", health.classify(Exception("503 overloaded")), "busy")
        check("402 = busy", health.classify(Exception("402 payment_required")), "busy")
        check("404 = gone", health.classify(Exception("404 model_not_found")), "gone")
        check("timeout = other", health.classify(Exception("APITimeoutError")), "other")
        check("voice id me 401 nahi pakda",
              health.classify(Exception("voice id JBFqnCB401sdRMkjVDRZzb")), "other")


class TestSessionSkip(unittest.TestCase):
    """401 ke baad poore session me ElevenLabs dobara nahi — sirf Edge."""

    def setUp(self):
        health.reset_all()
        self.eleven = FakeProvider(fail=RuntimeError(AUTH_401))
        self.edge = FakeProvider()
        self.cartesia = FakeProvider(fail=RuntimeError("cartesia voice id nahi"))
        self.fake = {"elevenlabs": self.eleven, "cartesia": self.cartesia,
                     "edge": self.edge}

    def tearDown(self):
        health.reset_all()

    def test_first_call_fails_then_band(self):
        health.classify_and_skip("elevenlabs", AUTH_401)
        check("401 ke baad BAND", "BAND" in health.blocked_reason("elevenlabs"), True)

    def test_two_answers_elevenlabs_called_once(self):
        """"Ek baar log karo, seedha Edge" — do jawab, ek hi ElevenLabs call."""

        async def go():
            with chain(self.fake):
                out = []
                for text in ("pehla jawab", "dusra jawab"):
                    tts.cache_clear()          # dono alag text -> dono asli call
                    out.append(await tts.speak(text, "sunday"))
                return out

        first, second = asyncio.run(go())
        check("pehla jawab edge par gaya (401 ke baad)", first[1], "edge")
        check("dusra jawab bhi edge", second[1], "edge")
        check("elevenlabs sirf 1 hi baar bula", len(self.eleven.calls), 1)
        check("edge dono baar bula", len(self.edge.calls), 2)

    def test_band_message_user_ko_bhi(self):
        health.classify_and_skip("elevenlabs", AUTH_401)
        check("reset_provider se khol sakte ho",
              health.reset_provider("elevenlabs") or
              health.blocked_reason("elevenlabs"), "")


class TestMissingKey(unittest.TestCase):
    """Key khaali ho to network call hi nahi — voice id se alag check."""

    def setUp(self):
        health.reset_all()

    def tearDown(self):
        health.reset_all()

    def test_missing_key_pure(self):
        with patch(config_voice, "ELEVENLABS_API_KEY", ""):
            check("elevenlabs key nahi", tts.missing_key("elevenlabs"),
                  "elevenlabs: key nahi hai")
        with patch(config_voice, "CARTESIA_API_KEY", ""):
            check("cartesia key nahi", tts.missing_key("cartesia"),
                  "cartesia: key nahi hai")
        check("edge ko key chahiye hi nahi", tts.missing_key("edge"), "")
        check("key hai to khaali", tts.missing_key("elevenlabs"), "")

    def test_key_empty_provider_not_called(self):
        """Voice id maujood hai (female list me bhi), key nahi — phir bhi
        provider **bilkul na bule**. Voice id wala check alag hai; agar sirf
        wahi hota to network call chalti.

        `os.environ` ka **purana value wapas** rakhna zaroori hai — `.env` ki
        asli value `pop()` se mit jaati aur bade test silent fail ho jaate."""
        import os
        eleven = FakeProvider()
        edge = FakeProvider()
        fake = {"elevenlabs": eleven, "cartesia": FakeProvider(), "edge": edge}
        saved = os.environ.get("ELEVENLABS_VOICE_SUNDAY")
        os.environ["ELEVENLABS_VOICE_SUNDAY"] = "JBFqnCBsd6RMkjVDRZzb"
        try:
            check("voice id sach me set tha",
                  config.voice_for("elevenlabs", "sunday"), "JBFqnCBsd6RMkjVDRZzb")
            with patch(config_voice, "ELEVENLABS_API_KEY", ""), chain(fake):
                tts.cache_clear()
                audio, provider = asyncio.run(tts.speak("kya haal", "sunday"))
        finally:
            if saved is None:
                os.environ.pop("ELEVENLABS_VOICE_SUNDAY", None)
            else:
                os.environ["ELEVENLABS_VOICE_SUNDAY"] = saved
        check("seedha edge", provider, "edge")
        check("elevenlabs provider 0 baar", len(eleven.calls), 0)
        check("audio mila", len(audio) > 0, True)
        check("asli voice id wapas", os.environ.get("ELEVENLABS_VOICE_SUNDAY"), saved)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("TTS 401 = ek baar, phir Edge" if result.wasSuccessful() else "FAIL")
