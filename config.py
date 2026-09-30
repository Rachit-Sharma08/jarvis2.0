import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PERSONAS_DIR = BASE_DIR / "personas"
UI_DIR = BASE_DIR / "ui"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "prabh.log"

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "").strip()

GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_MODEL = "gemini-2.5-flash"

DEFAULT_MODE = "sunday"

# Ye app sirf is PC par chalti hai. 0.0.0.0 kabhi allowed nahi.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
LOCAL_NAMES = ("localhost", "127.0.0.1")
TOKEN_BYTES = 32

MODE_ALIASES = {
    "sunday": ("Sunday", "संडे"),
    "prabh": ("Prabh", "Prabhu", "प्रभ", "प्रभु"),
}

TTS_CHAIN = ("elevenlabs", "cartesia", "edge")
TTS_MAX_CHARS = 500
AUDIO_MAX_BYTES = 10 * 1024 * 1024
RECORD_MAX_SECONDS = 30

EDGE_VOICES = {"sunday": "hi-IN-MadhurNeural", "prabh": "hi-IN-SwaraNeural"}
ELEVENLABS_MODEL = "eleven_multilingual_v2"
ELEVENLABS_DEFAULT_VOICE = "JBFqnCBsd6RMkjVDRZzb"
CARTESIA_MODEL = "sonic-2"
CARTESIA_VERSION = "2025-04-16"

VOICE_ENV = {
    ("elevenlabs", "sunday"): "ELEVENLABS_VOICE_SUNDAY",
    ("elevenlabs", "prabh"): "ELEVENLABS_VOICE_PRABH",
    ("cartesia", "sunday"): "CARTESIA_VOICE_SUNDAY",
    ("cartesia", "prabh"): "CARTESIA_VOICE_PRABH",
}


def mode_aliases() -> list:
    return [a for names in MODE_ALIASES.values() for a in names]


def voice_id(provider: str, mode: str) -> str:
    return os.getenv(VOICE_ENV.get((provider, mode), VOICE_ENV[(provider, DEFAULT_MODE)]), "").strip()


def is_local_only() -> bool:
    return SERVER_HOST in LOCAL_NAMES


def allowed_hosts() -> set:
    return {f"{name}:{SERVER_PORT}" for name in LOCAL_NAMES}


def allowed_origins() -> set:
    return {f"http://{name}:{SERVER_PORT}" for name in LOCAL_NAMES}


def has_groq() -> bool:
    return bool(GROQ_API_KEY)


def has_gemini() -> bool:
    return bool(GEMINI_API_KEY)


def has_elevenlabs() -> bool:
    return bool(ELEVENLABS_API_KEY)


def has_cartesia() -> bool:
    return bool(CARTESIA_API_KEY)