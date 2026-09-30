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

# Live list endpoint par verify hua (Sept 2026). Purane naam 404 de rahe the.
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_MODELS = (GROQ_MODEL, "openai/gpt-oss-20b")
GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_MODELS = (GEMINI_MODEL, "gemini-flash-latest")
# Kitni der wait: Groq 10s, Gemini 15s. 402/429/503 par 10 min araam.
BRAIN_TIMEOUT_GROQ = 10.0
BRAIN_TIMEOUT_GEMINI = 15.0
GEMINI_RETRY_WAIT = 2.5
PROVIDER_SKIP_SECONDS = 600

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

# Prabh ki awaaz hamesha female. Is mode me default (male) voice kabhi use
# nahi hoga — id na ho to seedha Cartesia/Edge par chala jayega.
FEMALE_ONLY_MODES = ("prabh",)

VOICE_ENV = {
    ("elevenlabs", "sunday"): "ELEVENLABS_VOICE_SUNDAY",
    ("elevenlabs", "prabh"): "ELEVENLABS_VOICE_PRABH",
    ("cartesia", "sunday"): "CARTESIA_VOICE_SUNDAY",
    ("cartesia", "prabh"): "CARTESIA_VOICE_PRABH",
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


def voice_for(provider: str, mode: str) -> str:
    """Is provider+mode ki voice id. Female-only mode me male default kabhi nahi.

    Edge hamesha apni built-in voice deta hai. Baaki me id na ho to '' — matlab
    us provider ko chhod do (Prabh male awaaz par nahi ja sakta).
    """
    if provider == "edge":
        return EDGE_VOICES.get(mode, EDGE_VOICES[DEFAULT_MODE])
    vid = os.getenv(VOICE_ENV.get((provider, mode), ""), "").strip()
    if not vid and provider == "elevenlabs" and mode not in FEMALE_ONLY_MODES:
        return ELEVENLABS_DEFAULT_VOICE
    return vid


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