"""Voice (STT + TTS) constants aur voice id ka faisla.

`config.py` inhe re-export karta hai, isliye code me `config.TTS_CHAIN` hi
likhna hai. Gender rule: DONO mode female-only — male id ya male default
fallback kabhi nahi. Female id ki allowlist `voice/tts_female.py` me hai.
"""

import config_env  # noqa: F401  (purane env naam pehle alias hote hain)
import os

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "").strip()

TTS_CHAIN = ("elevenlabs", "cartesia", "edge")
TTS_MAX_CHARS = 500
# Brain ka **awaaze wala** jawab isse chhota (4-Oct). HUD par poora text rehta
# hai — sirf awaaz chhoti. 500 char bolne me ~4.3 s lagta tha (sirf playback),
# is liye user ko jawab "late" lagta tha; ~220 char ≈ 2 s. Vaakya ke end par
# kat-ta hai (beech se nahi) — `voice/tts.py` ka `clip_answer()`.
VOICE_ANSWER_MAX_CHARS = int(os.getenv("JARVIS_VOICE_MAX", "220") or 220)
# Awaaz me **pehle itne poore vaakya** bolne hain (KAAM 4). 220 char par kaatne
# se beech ka tukda sunai deta tha; 1-2 vaakya poore bolne se jawab samajh aata
# hai aur turant shuru hota hai. HUD par poora jawab waise hi rehta hai.
VOICE_SENTENCES = int(os.getenv("JARVIS_VOICE_SENTENCES", "2") or 2)
AUDIO_MAX_BYTES = 10 * 1024 * 1024
RECORD_MAX_SECONDS = 30

# ---- STT ka apna timeout + retry (13-Oct, S-1 audit) ------------------------
# Pehle `voice/stt.py` **brain wala** `BRAIN_TIMEOUT_GROQ` (10 s) use karta tha
# aur Groq SDK apne aap 2 baar retry karta tha. 3.5 s ki audio par call 43 s tak
# atak sakta tha (log: `stt failed (43503ms)`), aur 5-6 Oct ko 165-295 s bhi.
# Is liye STT ka apna chhota timeout + kam retry. `.env` se badal sakte ho.
STT_TIMEOUT_SECONDS = float(os.getenv("JARVIS_STT_TIMEOUT", "6") or 6)
STT_MAX_RETRIES = int(os.getenv("JARVIS_STT_RETRIES", "1") or 1)
# SDK ke timeout/retry ke upar app ka ceiling — is se zyada matlab hamara thread
# atak gaya hai (network ya SDK ka apna bug). `voice/stt.py` yahin lagata hai.
STT_HARD_MARGIN_SECONDS = 4.0

# ---- local STT (faster-whisper) -------------------------------------------
# Groq key na ho to bhi JARVIS sun sake — free, offline, CPU par. Model
# `models/` me rehta hai (gitignored, ek baar download).
# `JARVIS_STT_LOCAL`: auto (default) | local | groq | off
STT_LOCAL = os.getenv("JARVIS_STT_LOCAL", "auto").strip().lower()
STT_LOCAL_MODEL = os.getenv("JARVIS_STT_LOCAL_MODEL", "").strip() or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "models", "faster-whisper-small")
# 4 physical cores (i5-1145G7). Zyada threads par ye model slow ho jaata hai.
STT_LOCAL_THREADS = int(os.getenv("JARVIS_STT_THREADS", "4") or 4)
# CPU par ~2x realtime: 30 s ki max recording ~60 s leti hai, is liye ceiling
# Groq wale 16 s se alag hai.
STT_LOCAL_DEADLINE_SECONDS = float(
    os.getenv("JARVIS_STT_LOCAL_TIMEOUT", "75") or 75)
# "en" = Hinglish Latin me rehti hai (Devanagari nahi) aur language detection
# ka ~5 s bachta hai. "hi" jaan-boojh kar nahi — romanized Hinglish bigaadta hai.
STT_LANGUAGE = os.getenv("JARVIS_STT_LANG", "en").strip()
# Whisper ko hint: ye Hinglish hai (English akshar, Hindi shabd). Bina hint ke
# wo Hindi ko Devanagari me likh deta hai aur naam galat sunta hai — `prompt`
# sirf style sikhata hai, `language=` nahi bhejte (wo romanized text bigaadta hai).
STT_PROMPT = os.getenv("JARVIS_STT_PROMPT", "").strip() or (
    "Haan Sir, bataiye. WhatsApp kholo, time kya hua, aaj ka mausam kaisa hai, "
    "screen par kya hai, reminder laga do.")


def stt_deadline() -> float:
    """Wake ka STT **kutte** tak wait karega (SDK ka budget + margin).

    App ka ceiling: `timeout * (retries + 1) + margin`. Saaf SttError aayega,
    thread atka nahi rahega — user ko "sun nahi paya" turant milega."""
    return STT_TIMEOUT_SECONDS * (STT_MAX_RETRIES + 1) + STT_HARD_MARGIN_SECONDS
# Round 2: chhoti recording (dab dab) aur bad script reject. Browser duration
# bhejta hai, server 600ms se kam par TTS/STT dono rok deta hai.
STT_MIN_DURATION_MS = 600

# Dono mode ki awaaz female. Prabh pehle bhi female tha, ab default mode bhi.
# Key `sunday` wo mode **id** hai (Step 1 me naam badla, id nahi) — `.env` me
# bhi `ELEVENLABS_VOICE_SUNDAY` wahi naam rehta hai.
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