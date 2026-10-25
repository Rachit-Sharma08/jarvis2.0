"""Saare settings ek jagah se. `import config` hi sab jagah chalta hai.

Bade hisse alag file me hain (ek file, ek kaam):
  - config_brain.py  → brain provider keys, models, tokens, timeouts
  - config_voice.py  → TTS/STT constants + voice id ka faisla
  - config_hud.py    → HUD ka rang, weather, stats interval, quick buttons
  - config_desktop.py → desktop shell: HUD window, tray, supervisor, autostart
  - config_tray.py   → tray watchdog ki timing (Explorer ne icon liya ya nahi)
  - config_wake.py   → wake word, VAD, command window, WhatsApp call ke constants
  - config_name.py   → assistant ka naam + usko bulane ke shabd (Step 1: Jarvis)
Yahan woh sab re-export hote hain, isliye `config.GROQ_API_KEY` aur
`config.TTS_CHAIN` dono pehle jaise hi kaam karte hain.

Rules: key sirf `.env` se, kabhi code me nahi. Ye app sirf 127.0.0.1 par.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PERSONAS_DIR = BASE_DIR / "personas"
UI_DIR = BASE_DIR / "ui"

# `.env` pehle load hota hai — neeche har `os.getenv` isi par depend karta hai.
# Pehle ye LOG_DIR ke *baad* tha, is liye `.env` me rakha `JARVIS_LOG_DIR`
# chalta hi nahi tha (sirf asli environment variable chalta tha).
load_dotenv(BASE_DIR / ".env")

# Purane env naam yahan se naye naam me badal jaate hain — LOG_DIR usi par
# depend karta hai, is liye ye import neeche ke kisi bhi getenv se pehle.
import config_env  # noqa: E402,F401

# Log ka folder. `JARVIS_LOG_DIR` se badal sakte ho — **test isi ka istemaal
# karte hain** (`tests/logsafe.py`): test bhi yehi `logs/jarvis.log` me likhte
# the, jisse asli app ka log nakli entry se bhar jaata tha (S-1 me RMS 0.129
# wahi galti thi). Test ka apna temp folder = analysis saaf.
LOG_DIR = Path(os.getenv("JARVIS_LOG_DIR") or (BASE_DIR / "logs"))
LOG_FILE = LOG_DIR / "jarvis.log"

# ---- Brain + voice constants yahan se aate hain ----

from config_brain import (  # noqa: E402
    BRAIN_MAX_TOKENS, BRAIN_MAX_TOKENS_RETRY, BRAIN_REASONING_EFFORT,
    BRAIN_TIMEOUT_GEMINI, BRAIN_TIMEOUT_GROQ, GEMINI_API_KEY, GEMINI_MODELS,
    GEMINI_MODEL, GEMINI_RETRY_WAIT, GROQ_API_KEY, GROQ_MODELS, GROQ_MODEL,
    GROQ_STT_MODEL, NVIDIA_API_KEY, NVIDIA_BASE_URL,
    NVIDIA_MAX_CALLS_PER_MINUTE, NVIDIA_MODELS, NVIDIA_MODEL,
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODELS,
    PROVIDER_SKIP_SECONDS, has_gemini, has_groq, has_nvidia, has_openrouter,
)
from config_voice import (  # noqa: E402
    AUDIO_MAX_BYTES, CARTESIA_API_KEY, CARTESIA_DEFAULT_MODEL, CARTESIA_MODEL,
    CARTESIA_VERSION, ELEVENLABS_API_KEY, ELEVENLABS_MODEL, EDGE_VOICES,
    FEMALE_ONLY_MODES, RECORD_MAX_SECONDS, STT_HARD_MARGIN_SECONDS,
    STT_MAX_RETRIES, STT_MIN_DURATION_MS, STT_TIMEOUT_SECONDS, TTS_CHAIN,
    TTS_MAX_CHARS, VOICE_ANSWER_MAX_CHARS, VOICE_ENV, VOICE_SENTENCES,
    has_cartesia, has_elevenlabs,
    stt_deadline, voice_for,
)
from config_hud import (  # noqa: E402
    AMBER, ARC_ACCENT, ARC_ACCENT_2, ARC_ACCENT_DIM, ARC_ACTIVITY_MAX,
    ARC_BAD, ARC_BG, ARC_CREDIT, ARC_FONT_BODY, ARC_FONT_HEAD, ARC_FONT_MONO,
    ARC_FRAME_MS, ARC_FPS, ARC_GOOD, ARC_HEX_NODES, ARC_INK, ARC_INK_DIM,
    ARC_LINE, ARC_ORBIT_DOTS, ARC_PANEL, ARC_PAUSE_WHEN_HIDDEN, ARC_ROUTING,
    ARC_ROUTING_CHANNEL, ARC_TICK_COUNT, ARC_TYPE_MS, CYAN, CYAN_BRIGHT,
    CYAN_DIM, FONT_BODY, FONT_HEAD, FONT_MONO, HUD_THEMES, HUD_THEME_DEFAULT,
    MUSIC_URL, NET_MB,
    QUICK_BUTTONS, STATS_CACHE_SECONDS, STATS_INTERVAL_SECONDS, TEMP_MAX,
    TEMP_MIN, WEATHER_CACHE_SECONDS, WEATHER_CITY, WEATHER_LAT, WEATHER_LON,
    WEATHER_TIMEOUT_SECONDS, WEATHER_URL, hud_theme, quick_by_id, quick_ids,
    temp_percent, weather_text,
)
# ---- Computer vision (15-Oct) — owner pehchan, DEFAULT OFF ----
from config_vision import (  # noqa: E402
    CAMERA_HEIGHT, CAMERA_INDEX, CAMERA_WIDTH, ENROLL_SAMPLES, NEEDS_CAMERA,
    NEEDS_ENROLL, NOT_OWNER, TOO_FAST, VISION_ENABLED, VISION_THRESHOLD,
    state as vision_state,
)
from config_desktop import (  # noqa: E402
    AUTOSTART_NAME, AUTOSTART_RUN_KEY, AUTOSTART_SCRIPT, BASE_DIR,
    BROWSER_CANDIDATES, DATA_DIR, EXIT_ALREADY_RUNNING, EXIT_NO_TRAY, EXIT_QUIT,
    EXIT_RESTART, HUD_HEIGHT, HUD_HOTKEY, HUD_OPEN_AT_START, HUD_PATH,
    HUD_PROFILE_DIR, HUD_SHORTCUT_NAME, HUD_WIDTH, LOCK_FILE, LOCK_POLL_SECONDS,
    MIC_CONSENT_KEY, OUTPUT_DEVICE, OUTPUT_RATE, PLAYBACK_TIMEOUT_SECONDS,
    RESTART_BACKOFF, RESTART_MAX, RESTART_WINDOW_SECONDS, STARTUP_HUD,
    STARTUP_HTTP_TIMEOUT, STARTUP_SERVER, STARTUP_TRAY, STARTUP_WAKE, TRAY_COLORS,
    TRAY_ERROR, TRAY_IDLE, TRAY_LISTENING, TRAY_MUTED, TRAY_NAME, TRAY_OFF,
    TRAY_START_ATTEMPTS, TRAY_TITLE, backoff_for,
    browser_path, tray_color, tray_title,
)
from config_tray import (  # noqa: E402
    TRAY_WATCH_ENABLED, TRAY_WATCH_FAST_SECONDS, TRAY_WATCH_FIRST_SECONDS,
    TRAY_WATCH_SLOW_SECONDS,
)
from config_wake import (  # noqa: E402
    ACK_BEEP, ACK_BEEP_DROP_SECONDS, ACK_BEEP_HZ, ACK_BEEP_MS, ACK_ON_WAKE,
    BLOCK_MS, BRAIN_FAILED,
    CHANNELS, COMMAND_ACK_PEEK_SECONDS, COMMAND_END_SILENCE_SECONDS,
    COMMAND_HANGOVER_SECONDS, COMMAND_MAX_SECONDS, COMMAND_MIN_SECONDS,
    COMMAND_PRE_ROLL_SECONDS, COMMAND_WAIT_SECONDS, COMMAND_WARMUP_SECONDS,
    CONFIRM_VOICE, HOT_WINDOW_ENABLED, HOT_WINDOW_SECONDS,
    INPUT_DEVICE, INPUT_GAIN, INPUT_GAIN_MAX, INPUT_GAIN_TARGET,
    INPUT_HOSTAPI, MIC_OPEN_ATTEMPTS, MIC_OPEN_RETRY_SECONDS,
    NOT_HEARD, NOT_UNDERSTOOD, PLAYBACK_MUTE_MIC, PLAYBACK_TAIL_GUARD_SECONDS,
    SAMPLE_RATE, SLEEP_ACK,
    SLEEP_FROM_TRAY, SLEEP_WORDS, STOP_WORD,
    VAD_HANGOVER_BLOCKS, VAD_SILENCE_BLOCKS, VAD_THRESHOLD, WAKE_COOLDOWN_SECONDS,
    WAKE_DEBUG, WAKE_DEBUG_SECONDS,
    WAKE_ENABLED, WAKE_GRAMMAR, WAKE_MODEL_DIR, WAKE_VOSK_GATE, WAKE_WORDS,
    describe, model_missing, model_path, wake_available,
)
from config_name import (  # noqa: E402
    ASSISTANT_NAME, DISPLAY_NAME, LEGACY_WAKE_PHRASES, WAKE_PHRASES,
    legacy_enabled, wake_grammar, wake_words,
)

DEFAULT_MODE = "sunday"   # Andar ka id — dikhne wala naam `ASSISTANT_NAME` hai

# Phase 5: sirf ek hi mode (Sunday-only flag). PRABH mode ka code **hataya nahi
# gaya** — bas band kar diya gaya hai, taaki baad me bina kuch badle wapas on
# kar sakein. `core/modes.py` yahi flag dekhta hai.
SUNDAY_ONLY = os.getenv("JARVIS_SUNDAY_ONLY", "1") == "1"

# Ye app sirf is PC par chalti hai. 0.0.0.0 kabhi allowed nahi.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
# Apna hi origin. Tab use hota hai jab browser same-origin GET par Origin
# header nahi bhejta (see server/security.py same_origin_proof).
SERVER_ORIGIN = f"http://{SERVER_HOST}:{SERVER_PORT}"
LOCAL_NAMES = ("localhost", "127.0.0.1")
TOKEN_BYTES = 32

# Mode switch ke shabd. "Jarvis" bhi `sunday` mode ka alias hai (andar ka id
# wahi rehta hai) — is liye "Jarvis, kya haal hai" se sirf naam prefix hatta
# hai, mode badalta nahi.
MODE_ALIASES = {
    "sunday": ("Sunday", "Jarvis", "जार्विस", "संडे"),
    "prabh": ("Prabh", "Prabhu", "प्रभ", "प्रभु"),
}

# Mode id → persona file. File ka naam alag hai (Step 1: `jarvis.txt`), mode id
# wahi `sunday` — ye mapping hi dono ko baand rakhti hai.
PERSONA_FILES = {"sunday": "jarvis.txt", "prabh": "prabh.txt"}

# ---- Phase 3: PC ke tools + gatekeeper ----

from config_tools import (  # noqa: E402
    ALARM_TOOL_ENABLED, ALLOWED_APPS, ALWAYS_ASK, ASK, BLOCKED, BLOCKED_ROOTS,
    CALL_ASK_FIRST, CDP_HOST,
    CDP_PORT, COMMAND_TIMEOUT_SECONDS, DIRECT_REPLY,
    EXTRA_BLOCKED_PATTERNS, HOME, NEVER_ALLOW, NO_CARDS, PROTECTED_FOLDER_NAMES,
    READ_FILE_MAX_BYTES,
    READ_FOLDERS, SAFE, SECRET_FILE_NAMES, TOOL_ARG_LIMIT, TOOL_BASE_RISK,
    TOOL_CONFIRM_TIMEOUT, TOOL_MAX_CALLS_PER_MINUTE, TOOL_MAX_STEPS,
    TOOL_OUTPUT_LIMIT, TOOLS_AUTO_OFF_MINUTES, TOOLS_ENABLED_DEFAULT,
    WHATSAPP_WEB, WORKSPACE,
)

# Gatekeeper har tool ka likhna yahan — LOG_DIR config.py ka apna hai.
ACTION_LOG = LOG_DIR / "actions.log"
CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "media-src 'self' blob:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
    "connect-src 'self' ws://localhost:8000 ws://127.0.0.1:8000"
)


def ensure_workspace() -> Path:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    return WORKSPACE


def mode_aliases() -> list:
    return [a for names in MODE_ALIASES.values() for a in names]


def is_local_only() -> bool:
    return SERVER_HOST in LOCAL_NAMES


def allowed_hosts() -> set:
    return {f"{name}:{SERVER_PORT}" for name in LOCAL_NAMES}


def allowed_origins() -> set:
    return {f"http://{name}:{SERVER_PORT}" for name in LOCAL_NAMES}