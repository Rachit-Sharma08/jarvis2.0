"""Fix round 1 — voice side: female-only chain, Cartesia payload."""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import os
from unittest.mock import patch

import config
from voice import tts

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


class Fake:
    def __init__(self, label, fail=False):
        self.label, self.fail = label, fail

    async def speak(self, text, mode):
        if self.fail:
            raise RuntimeError("forced fail")
        return b"AUDIO" + self.label.encode()


def run_with(failing, mode="prabh"):
    saved = dict(tts.PROVIDERS)
    tts.PROVIDERS.update({n: Fake(n, n in failing) for n in config.TTS_CHAIN})
    try:
        return asyncio.run(tts.speak("test", mode))
    finally:
        tts.PROVIDERS.clear()
        tts.PROVIDERS.update(saved)


def test_voice_config():
    print("VOICE CONFIG")
    check("prabh edge female", config.voice_for("edge", "prabh"), "hi-IN-SwaraNeural")
    check("sunday edge", config.voice_for("edge", "sunday"), "hi-IN-MadhurNeural")
    check("prabh female-only mode", "prabh" in config.FEMALE_ONLY_MODES, True)
    check("dono edge voice alag", config.EDGE_VOICES["prabh"] != config.EDGE_VOICES["sunday"], True)
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ELEVENLABS_VOICE_PRABH", None)
        check("id na ho to male default nahi", config.voice_for("elevenlabs", "prabh"), "")
        os.environ.pop("ELEVENLABS_VOICE_SUNDAY", None)
        check("sunday ko default mila", config.voice_for("elevenlabs", "sunday"),
              config.ELEVENLABS_DEFAULT_VOICE)
        check("prabh default se bacha", config.voice_for("elevenlabs", "prabh") !=
              config.ELEVENLABS_DEFAULT_VOICE, True)


def test_cartesia_payload():
    print("CARTESIA PAYLOAD")
    source = (config.BASE_DIR / "voice" / "tts_cartesia.py").read_text(encoding="utf-8")
    check("language voice.control me", '"control": {"language": "hi"}' in source, True)
    check("top-level language nahi", '"language": "hi",\n        "output_format"' not in source, True)
    check("output_format object hai", '"output_format": {"container": "mp3"' in source, True)
    check("voice id mode se", 'config.voice_for("cartesia", mode)' in source, True)


def test_female_chain_order():
    """Prabh: ElevenLabs female -> Cartesia female -> Edge Swara. Male kabhi nahi."""
    print("FEMALE CHAIN ORDER")
    check("chain order", config.TTS_CHAIN, ("elevenlabs", "cartesia", "edge"))
    audio, provider = run_with({"elevenlabs"})
    check("elevenlabs fail par cartesia", provider, "cartesia")
    audio, provider = run_with({"elevenlabs", "cartesia"})
    check("dono fail par edge", provider, "edge")
    check("edge ka audio mila", audio, b"AUDIOedge")
    check("edge voice female (Swara)", config.voice_for("edge", "prabh"), "hi-IN-SwaraNeural")

    called = []

    class Watcher(Fake):
        async def speak(self, text, mode):
            called.append(self.label)
            return await Fake.speak(self, text, mode)

    with patch.dict(os.environ, {"CARTESIA_VOICE_PRABH": "cartesia-female-test-id"}, clear=False):
        os.environ.pop("ELEVENLABS_VOICE_PRABH", None)
        saved = dict(tts.PROVIDERS)
        tts.PROVIDERS.update({n: Watcher(n) for n in config.TTS_CHAIN})
        try:
            audio, provider = asyncio.run(tts.speak("test", "prabh"))
        finally:
            tts.PROVIDERS.clear()
            tts.PROVIDERS.update(saved)
    check("id na ho par elevenlabs chala hi nahi", "elevenlabs" in called, False)
    check("cartesia par chala gaya", provider, "cartesia")


def test_sunday_can_use_default():
    print("SUNDAY CHAIN")
    audio, provider = run_with({"elevenlabs"}, mode="sunday")
    check("sunday: cartesia id nahi hai to edge", provider, "edge")
    check("sunday edge voice Madhur", config.voice_for("edge", "sunday"), "hi-IN-MadhurNeural")
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ELEVENLABS_VOICE_SUNDAY", None)
        check("sunday default male allowed hai", config.voice_for("elevenlabs", "sunday"),
              config.ELEVENLABS_DEFAULT_VOICE)
        os.environ.pop("CARTESIA_VOICE_SUNDAY", None)
        check("sunday cartesia id na ho to skip", config.voice_for("cartesia", "sunday"), "")


def test_no_empty_audio_accepted():
    print("KHAALI TEXT")
    from voice.tts import TtsError, speak
    try:
        asyncio.run(speak("   ", "prabh"))
        check("khaali text block hua", "nahi aaya", "TtsError")
    except TtsError:
        check("khaali text block hua", True, True)


for fn in (test_voice_config, test_cartesia_payload, test_female_chain_order,
           test_sunday_can_use_default, test_no_empty_audio_accepted):
    fn()

print("FAIL:", FAILED if FAILED else "koi nahi")
sys.exit(1 if FAILED else 0)
