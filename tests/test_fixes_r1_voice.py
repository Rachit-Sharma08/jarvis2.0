"""Fix round 1 — voice side: female-only chain, Cartesia payload."""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
import os
from unittest.mock import patch

import config
from voice import tts, tts_female

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
    # Round 2: dono mode Swara (female). Sunday bhi Swara.
    check("sunday edge bhi Swara", config.voice_for("edge", "sunday"), "hi-IN-SwaraNeural")
    check("prabh female-only mode", "prabh" in config.FEMALE_ONLY_MODES, True)
    check("dono mode female-only", set(config.FEMALE_ONLY_MODES) == {"prabh", "sunday"}, True)
    check("dono edge voice same", config.EDGE_VOICES["prabh"] == config.EDGE_VOICES["sunday"], True)
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ELEVENLABS_VOICE_PRABH", None)
        check("id na ho to male default nahi", config.voice_for("elevenlabs", "prabh"), "")
        # Round 2: Sunday bhi female-only — default (male) fallback nahi milta.
        os.environ.pop("ELEVENLABS_VOICE_SUNDAY", None)
        check("sunday ko bhi default nahi", config.voice_for("elevenlabs", "sunday"), "")


def test_cartesia_payload():
    print("CARTESIA PAYLOAD")
    source = (config.BASE_DIR / "voice" / "tts_cartesia.py").read_text(encoding="utf-8")
    check("language voice.control me", '"control": {"language": "hi"}' in source, True)
    check("top-level language nahi", '"language": "hi",\n        "output_format"' not in source, True)
    check("output_format object hai", '"output_format": {"container": "mp3"' in source, True)
    check("voice id mode se", 'config.voice_for("cartesia", mode)' in source, True)


def test_female_chain_order():
    """Dono mode: ElevenLabs female -> Cartesia female -> Edge Swara. Male kabhi nahi."""
    print("FEMALE CHAIN ORDER")
    check("chain order", config.TTS_CHAIN, ("elevenlabs", "cartesia", "edge"))
    # Test allowlist ko pata id se replace karta hai — asli voice ids par depend
    # na kare, warna env badalne par test toot jayega.
    fake_allow = {
        "elevenlabs": {"FAKE-EL-1"},
        "cartesia": {"fake-cartesia-id"},
        "edge": {"hi-IN-SwaraNeural"},
    }
    saved_allow = dict(tts_female.ALLOW)
    tts_female.ALLOW.clear()
    tts_female.ALLOW.update(fake_allow)
    saved_env = {k: os.environ.get(k) for k in
                 ("ELEVENLABS_VOICE_PRABH", "CARTESIA_VOICE_PRABH")}
    os.environ["ELEVENLABS_VOICE_PRABH"] = "FAKE-EL-1"
    os.environ["CARTESIA_VOICE_PRABH"] = "fake-cartesia-id"
    called = []

    class Watcher(Fake):
        async def speak(self, text, mode):
            called.append(self.label)
            return await Fake.speak(self, text, mode)

    def run_watched(failing):
        saved = dict(tts.PROVIDERS)
        tts.PROVIDERS.update({n: Watcher(n, n in failing) for n in config.TTS_CHAIN})
        try:
            return asyncio.run(tts.speak("test", "prabh"))
        finally:
            tts.PROVIDERS.clear()
            tts.PROVIDERS.update(saved)

    try:
        audio, provider = run_with({"elevenlabs"})
        check("elevenlabs fail par cartesia", provider, "cartesia")
        audio, provider = run_with({"elevenlabs", "cartesia"})
        check("dono fail par edge", provider, "edge")
        check("edge ka audio mila", audio, b"AUDIOedge")
        check("edge voice female (Swara)", config.voice_for("edge", "prabh"), "hi-IN-SwaraNeural")

        # Sab id valid hain to pehla provider (elevenlabs) hi chalta hai.
        audio, provider = run_watched(set())
        check("sab chalta hai", provider, "elevenlabs")

        # ElevenLabs id missing -> seedha Cartesia.
        called.clear()
        os.environ["ELEVENLABS_VOICE_PRABH"] = ""
        audio, provider = run_watched(set())
        check("elevenlabs id na ho par chala nahi", "elevenlabs" in called, False)
        check("cartesia par chala gaya", provider, "cartesia")

        # Dono premium id missing -> Edge (Swara).
        os.environ["CARTESIA_VOICE_PRABH"] = ""
        called.clear()
        audio, provider = run_watched(set())
        check("dono id na ho par edge", provider, "edge")

        # Female allowlist me nahi id -> skip (male awaaz nahi bolega).
        os.environ["ELEVENLABS_VOICE_PRABH"] = "MALE-VOICE-NOT-ALLOWED"
        os.environ["CARTESIA_VOICE_PRABH"] = "fake-cartesia-id"
        called.clear()
        audio, provider = run_watched(set())
        check("allowlist ke bahar id skip", "elevenlabs" in called, False)
        check("allowlist ke bahar id par cartesia", provider, "cartesia")
    finally:
        tts_female.ALLOW.clear()
        tts_female.ALLOW.update(saved_allow)
        for key, val in saved_env.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val


def test_sunday_can_use_default():
    print("SUNDAY CHAIN")
    audio, provider = run_with({"elevenlabs"}, mode="sunday")
    check("sunday: cartesia id nahi hai to edge", provider, "edge")
    # Round 2: Sunday ki awaaz bhi Swara (dono mode same).
    check("sunday edge voice Swara", config.voice_for("edge", "sunday"), "hi-IN-SwaraNeural")
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("ELEVENLABS_VOICE_SUNDAY", None)
        # Sunday ab female-only — male default fallback nahi milta.
        check("sunday default male nahi milta", config.voice_for("elevenlabs", "sunday"), "")
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
