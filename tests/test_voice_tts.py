"""TTS side: provider chain + female allowlist + text cleaning + 500 char limit."""

import asyncio
import os
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from voice import tts, tts_female

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


class Boom:
    def __init__(self):
        self.calls = []

    async def speak(self, text, mode):
        self.calls.append((text, mode))
        raise RuntimeError("limit khatam")


class Good:
    def __init__(self, audio=b"AUDIO", name="good"):
        self.audio = audio
        self.name = name
        self.calls = []

    async def speak(self, text, mode):
        self.calls.append((text, mode))
        return self.audio


def test_chain_order():
    print("TTS PROVIDER CHAIN")
    check("chain ka order", config.TTS_CHAIN, ("elevenlabs", "cartesia", "edge"))
    check("edge aakhri hai", config.TTS_CHAIN[-1], "edge")

    # Round 2: har provider ka voice id female allowlist me hona zaroori hai.
    # Test allowlist ko pata ids se badalta hai — asli .env ids par depend na kare.
    saved_allow = dict(tts_female.ALLOW)
    saved_env = {k: os.environ.get(k) for k in
                 ("ELEVENLABS_VOICE_SUNDAY", "ELEVENLABS_VOICE_PRABH",
                  "CARTESIA_VOICE_SUNDAY", "CARTESIA_VOICE_PRABH")}
    tts_female.ALLOW.clear()
    tts_female.ALLOW.update({"elevenlabs": {"T-EL-S", "T-EL-P"},
                             "cartesia": {"T-CART"},
                             "edge": {"hi-IN-SwaraNeural"}})
    os.environ.update({"ELEVENLABS_VOICE_SUNDAY": "T-EL-S",
                       "ELEVENLABS_VOICE_PRABH": "T-EL-P",
                       "CARTESIA_VOICE_SUNDAY": "T-CART",
                       "CARTESIA_VOICE_PRABH": "T-CART"})
    try:
        _chain_body()
    finally:
        tts_female.ALLOW.clear()
        tts_female.ALLOW.update(saved_allow)
        for key, val in saved_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val


def _chain_body():
    eleven, cart, edge = Boom(), Boom(), Good(b"EDGE")
    saved = dict(tts.PROVIDERS)
    tts.PROVIDERS.update(elevenlabs=eleven, cartesia=cart, edge=edge)
    try:
        audio, name = asyncio.run(tts.speak("Namaste", "sunday"))
        check("do fail hone par edge bola", name, "edge")
        check("edge ka audio mila", audio, b"EDGE")

        only = Good(b"ELEVEN")
        cart.calls.clear()
        tts.PROVIDERS["elevenlabs"] = only
        _, name = asyncio.run(tts.speak("hi", "sunday"))
        check("pehla provider chala", name, "elevenlabs")
        check("baaki provider nahi chala", cart.calls, [])

        tts.PROVIDERS.update(elevenlabs=Boom(), cartesia=Good(b"CART"))
        _, name = asyncio.run(tts.speak("hi", "prabh"))
        check("eleven fail par cartesia", name, "cartesia")

        # Allowlist ke bahar ki id skip ho jaati hai (male awaaz nahi).
        tts_female.ALLOW["elevenlabs"] = {"SirfYe"}
        os.environ["ELEVENLABS_VOICE_PRABH"] = "Ye-Nahi-Hai"
        _, name = asyncio.run(tts.speak("hi", "prabh"))
        check("allowlist bahar id skip", name, "cartesia")
    finally:
        tts.PROVIDERS.update(saved)

    tts.PROVIDERS.update(elevenlabs=Boom(), cartesia=Boom(), edge=Boom())
    try:
        asyncio.run(tts.speak("hi", "sunday"))
        check("sab fail par saaf error", "error nahi mila", "error mila")
    except tts.TtsError as exc:
        check("sab fail par saaf error", "Awaaz nahi ban paayi" in str(exc), True)
    finally:
        tts.PROVIDERS.update(saved)


def test_text_cleaning():
    print("TEXT CLEANING (awaz se pehle)")
    check("markdown hat gaya", tts.clean("*bold* #tag `code` _x_ >y"), "bold tag code x y")
    check("URL hat gaya", tts.clean("Ye dekho https://x.com/a?b=1 aur phir"), "Ye dekho aur phir")
    check("www hat gaya", tts.clean("Ye dekho www.example.com"), "Ye dekho")
    check("emoji hat gaya", tts.clean("accha laga \U0001F600✨"), "accha laga")
    check("tir nahi bacha", "✔" in tts.clean("sab theek -> ✔"), False)
    check("kitna bhi lamba", len(tts.clean("**a**" * 400)), len("a" * 400 + " " * 399))


def test_char_limit():
    print("500 CHARACTER LIMIT")
    check("limit 500 hai", config.TTS_MAX_CHARS, 500)
    check("chhota text pura", tts.clip("chhota jawab"), "chhota jawab")
    long = "word " * 400
    cut = tts.clip(long)
    check("500 se kam bola", len(cut) <= 500, True)
    check("500 se zyada nahi", len(cut) >= 400, True)
    check("sentence pura nahi kata", cut.endswith("word"), True)
    check("limit badal sakte ho", len(tts.clip(long, 50)) <= 50, True)


def test_no_empty_audio():
    print("KHAALI TEXT")
    try:
        asyncio.run(tts.speak("   ", "prabh"))
        check("khaali text block hua", "nahi aaya", "TtsError")
    except tts.TtsError:
        check("khaali text block hua", True, True)


for fn in (test_chain_order, test_text_cleaning, test_char_limit, test_no_empty_audio):
    fn()

print()
if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Saare TTS test pass.")