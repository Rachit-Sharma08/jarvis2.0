"""Voice (STT + TTS) constants aur voice id ka faisla.

`config.py` inhe re-export karta hai, isliye code me `config.TTS_CHAIN` hi
likhna hai. Gender rule: DONO mode female-only — male id ya male default
fallback kabhi nahi. Female id ki allowlist `voice/tts_female.py` me hai.
"""

import os

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "").strip()

TTS_CHAIN = ("elevenlabs", "cartesia", "edge")
TTS_MAX_CHARS = 500
AUDIO_MAX_BYTES = 10 * 1024 * 1024
RECORD_MAX_SECONDS = 30
# Round 2: chhoti recording (dab dab) aur bad script reject. Browser duration
# bhejta hai, server 600ms se kam par TTS/STT dono rok deta hai.
STT_MIN_DURATION_MS = 600

# Dono mode ki awaaz female. Prabh pehle bhi female tha, ab Sunday bhi.
EDGE_VOICES = {"sunday": "hi-IN-SwaraNeural", "prabh": "hi-IN-SwaraNeural"}
ELEVENLABS_MODEL = "eleven_multilingual_v2"
CARTESIA_MODEL = "sonic-2"
CARTESIA_DEFAULT_MODEL = CARTESIA_MODEL
CARTESIA_VERSION = "2025-04-16"

FEMALE_ONLY_MODES = ("prabh", "sunday")

VOICE_ENV = {
    ("elevenlabs", "sunday"): "ELEVENLABS_VOICE_SUNDAY",
    ("elevenlabs", "prabh"): "ELEVENLABS_VOICE_PRABH",
    ("cartesia", "sunday"): "CARTESIA_VOICE_SUNDAY",
    ("cartesia", "prabh"): "CARTESIA_VOICE_PRABH",
}

DEFAULT_MODE = "sunday"


def voice_for(provider: str, mode: str) -> str:
    """Is provider+mode ki voice id. Female-only mode me male default kabhi nahi.

    Edge hamesha apni built-in female voice deta hai. Baaki me id na ho to '' —
    matlab us provider ko chhod do. Voice id female allowlist me na ho to
    tts.py use hi nahi karega (voice/tts_female.py dekho).
    """
    if provider == "edge":
        return EDGE_VOICES.get(mode, EDGE_VOICES[DEFAULT_MODE])
    return os.getenv(VOICE_ENV.get((provider, mode), ""), "").strip()


def has_elevenlabs() -> bool:
    return bool(ELEVENLABS_API_KEY)


def has_cartesia() -> bool:
    return bool(CARTESIA_API_KEY)