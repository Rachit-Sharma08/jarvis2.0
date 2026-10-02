"""Saare settings ek jagah se. `import config` hi sab jagah chalta hai.

Bade hisse alag file me hain (ek file, ek kaam):
  - config_brain.py  → brain provider keys, models, tokens, timeouts
  - config_voice.py  → TTS/STT constants + voice id ka faisla
  - config_hud.py    → HUD ka rang, weather, stats interval, quick buttons
  - config_desktop.py → desktop shell: HUD window, tray, supervisor, autostart
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
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "prabh.log"

load_dotenv(BASE_DIR / ".env")

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
    FEMALE_ONLY_MODES, RECORD_MAX_SECONDS, STT_MIN_DURATION_MS, TTS_CHAIN,
    TTS_MAX_CHARS, VOICE_ENV, has_cartesia, has_elevenlabs, voice_for,
)
from config_hud import (  # noqa: E402
    AMBER, CYAN, CYAN_BRIGHT, CYAN_DIM, FONT_BODY, FONT_HEAD, FONT_MONO,
    MUSIC_URL, NET_MB, QUICK_BUTTONS, STATS_CACHE_SECONDS,
    STATS_INTERVAL_SECONDS, TEMP_MAX, TEMP_MIN, WEATHER_CACHE_SECONDS,
    WEATHER_CITY, WEATHER_LAT, WEATHER_LON, WEATHER_TIMEOUT_SECONDS, WEATHER_URL,
    quick_by_id, quick_ids, temp_percent, weather_text,
)
from config_desktop import (  # noqa: E402
    AUTOSTART_NAME, AUTOSTART_RUN_KEY, BROWSER_CANDIDATES, DATA_DIR,
    EXIT_ALREADY_RUNNING, EXIT_QUIT, EXIT_RESTART, HUD_HEIGHT,
    HUD_OPEN_AT_START, HUD_PATH, HUD_PROFILE_DIR, HUD_WIDTH, LOCK_FILE,
    LOCK_POLL_SECONDS, MIC_CONSENT_KEY, RESTART_BACKOFF, RESTART_MAX,
    RESTART_WINDOW_SECONDS, STARTUP_HUD, STARTUP_HTTP_TIMEOUT, STARTUP_SERVER,
    STARTUP_TRAY, STARTUP_WAKE, TRAY_COLORS, TRAY_ERROR, TRAY_IDLE,
    TRAY_LISTENING, TRAY_MUTED, TRAY_NAME, TRAY_OFF, TRAY_TITLE,
    TOOLS_AUTO_OFF_MINUTES, backoff_for, browser_path, tray_color, tray_title,
)

DEFAULT_MODE = "sunday"

# Phase 5: sirf Sunday. PRABH mode ka code **hataya nahi gaya** — bas band
# kar diya gaya hai. Band karna ek flag se hai taaki baad me wapas on kar
# sakein bina kuch badle. `core/modes.py` yahi flag dekhta hai: "Prabh..." bol
# par bhi mode sunday hi rahega, aur wo text ek normal message ki tarah brain
# ko jayegi.
SUNDAY_ONLY = os.getenv("PRABH_SUNDAY_ONLY", "1") == "1"

# Ye app sirf is PC par chalti hai. 0.0.0.0 kabhi allowed nahi.
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000
# Apna hi origin. Tab use hota hai jab browser same-origin GET par Origin
# header nahi bhejta (see server/security.py same_origin_proof).
SERVER_ORIGIN = f"http://{SERVER_HOST}:{SERVER_PORT}"
LOCAL_NAMES = ("localhost", "127.0.0.1")
TOKEN_BYTES = 32

MODE_ALIASES = {
    "sunday": ("Sunday", "संडे"),
    "prabh": ("Prabh", "Prabhu", "प्रभ", "प्रभु"),
}

# ---- Phase 3: PC ke tools + gatekeeper ----

SAFE, ASK, BLOCKED = "SAFE", "ASK", "BLOCKED"

HOME = Path(os.path.expanduser("~"))
WORKSPACE = Path(os.getenv("PRABH_WORKSPACE", r"D:\prabh_workspace"))
READ_FOLDERS = (HOME / "Desktop", HOME / "Downloads", HOME / "Documents", WORKSPACE)

# Har tool ka base risk. Gatekeeper args dekh ke ise aage badha sakta hai.
TOOL_BASE_RISK = {
    "get_time_date": SAFE,
    "system_info": SAFE,
    "list_dir": SAFE,
    "read_file": SAFE,
    "write_file": ASK,
    "run_command": ASK,
    "open_app": SAFE,
    "open_website": SAFE,
    "close_app": ASK,
    "delete_to_trash": ASK,
}

# open_app sirf inhi me SAFE hai. Baaki sab poochhega.
ALLOWED_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "vscode": "code",
    "vs code": "code",
    "wordpad": "write.exe",
}

# Yahan user aur patterns add kar sakta hai. Code me hard-coded nahi.
EXTRA_BLOCKED_PATTERNS = (
    "vssadmin delete shadows",
    "bcdedit /set",
    "cipher /w",
    "wmic shadowcopy delete",
)


def _blocked_roots() -> tuple:
    """Jahan delete/badlav kabhi nahi hoga."""
    roots = []
    for name in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        value = os.environ.get(name, "")
        if value:
            roots.append(Path(value))
    roots += [Path(p) for p in (r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)",
                                r"C:\$Recycle.Bin", r"C:\Recovery", r"C:\System Volume Information")]
    return tuple(dict.fromkeys(roots))


BLOCKED_ROOTS = _blocked_roots()
# Naam se bhi pakadna hai (D: drive par bhi), raw aur resolved dono me.
PROTECTED_FOLDER_NAMES = (
    "windows", "system32", "syswow64", "winsxs", "program files",
    "program files (x86)", "programdata", "recovery", "boot", "driver",
    "$recycle.bin", "system volume information",
)
SECRET_FILE_NAMES = (".env", ".env.local", "credentials", "secrets.json", "id_rsa", "id_ed25519")

# Kill switch. Default OFF — user UI ka toggle daba kar ON kare.
TOOLS_ENABLED_DEFAULT = os.getenv("PRABH_TOOLS_ON", "0") == "1"
TOOL_MAX_STEPS = 5
TOOL_MAX_CALLS_PER_MINUTE = 20
TOOL_CONFIRM_TIMEOUT = 60
TOOL_OUTPUT_LIMIT = 2000
TOOL_ARG_LIMIT = 2000
COMMAND_TIMEOUT_SECONDS = 30
READ_FILE_MAX_BYTES = 20 * 1024
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