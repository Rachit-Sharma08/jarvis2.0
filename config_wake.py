"""Wake word + voice command ke constants. `import config` hi sab jagah chalta hai.

Ye Step 1 ka hissa hai. Do alag STT jaan-boojh kar:

1. **Wake word ("Sunday")** — local Vosk, `models/vosk-model-small-en-us-0.15`.
   English model hi sahi hai kyunki "Sunday" ek English shabd hai. Awaaz kabhi
   bahar nahi jaati, 100% offline.

2. **Command ("whatsapp kholo", "Ramesh ko phone karo")** — `voice/stt.py` ka
   Groq Whisper (`whisper-large-v3-turbo`). Ye Hinglish ka asli expert hai.
   `language` jaan-boojh kar NAHI bhejte (wahi galti Round 2 me hui thi).

Is liye Hinglish ke liye koi 470 MB model download karne ki zarurat nahi —
dono cheezein pehle se maujood hain. `wake/commands.py` ke liye bhi
`WAKE_COMMAND_HINTS` me wahi shabd jo user bolta hai.

Rule: is file me koi API key nahi. Wake ka model path `BASE_DIR/models` me hai.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"

# ---- kholna / band karna ----
# Default ON. Mic band karne ka ek hi raasta hai `desktop/micperm.py` +
# tray ka MUTE — `.env` se alag koi davaa nahi.
WAKE_ENABLED = os.getenv("PRABH_WAKE", "1").strip() not in ("0", "false", "no")

# ---- model ----
WAKE_MODEL_DIR = str(MODEL_DIR / "vosk-model-small-en-us-0.15")
WAKE_MODEL_ALT_DIR = str(MODEL_DIR / "vosk-model-small-hi-0.22")

# Vosk ke saath grammar: sirf ye shabd hi pehchanega. Isse do fayde —
# galat trigger kam, aur CPU halka (68 MB model me se sirf 4 shabd).
WAKE_WORDS = ("sunday",)
WAKE_GRAMMAR = (
    '["hello sunday", "hey sunday", "hi sunday", "okay sunday", "sunday", "[unk]"]'
)

# ---- audio ----
SAMPLE_RATE = 16000          # Vosk isko hi maangta hai (16 kHz mono)
BLOCK_MS = 30                # 30 ms ka chunk — Vosk ke liye ideal
CHANNELS = 1
INPUT_DEVICE = os.getenv("PRABH_WAKE_MIC", "").strip() or None

# Energy VAD. Mic ki khamoshi ka level ~0.002-0.01 hota hai, insaan ki awaaz
# 0.02 se upar. Beech ka number: thodi door se awaaz bhi uth jaaye, par
# fan/hawa ka shor na pakde.
VAD_THRESHOLD = float(os.getenv("PRABH_VAD", "0.012"))
VAD_SILENCE_BLOCKS = 12      # ~0.36 s khamoshi = VAD ke baad band
VAD_HANGOVER_BLOCKS = 30     # ~0.9 s — VAD ke dauraan awaaz mat kaato

# Ek hi "sunday" me do trigger na ho. Wake hit ke baad itni der queue khaali
# karte hue aawaaz fenk-te hain (recognition nahi) — taaki TTS/bijli ka shor
# ya apna hi naam dobara na pakde.
WAKE_COOLDOWN_SECONDS = 1.5

# ---- command window ----
COMMAND_MAX_SECONDS = 8      # wake ke baad itni der suno
COMMAND_MIN_SECONDS = 0.6    # itni ASLI awaaz chahiye, khamoshi ginti nahi
COMMAND_END_SILENCE_SECONDS = 0.9   # user chup ho gaya -> command khatam
COMMAND_HANGOVER_SECONDS = 0.4     # beech ka chhota ruk na kaato (wake se chhota)
COMMAND_PRE_ROLL_SECONDS = 0.4     # "Sunday" ke aakhri shabd bhi pakad lo
COMMAND_WAIT_SECONDS = 5.0         # pehla shabd aaya hi nahi -> "sun nahi aaya"
COMMAND_WARMUP_SECONDS = 1.0       # mic settle hone do, warna pehla shabd kat-ta hai

# Bolne ke waqt sunna band rakhna. Apni hi awaaz wapas na aaye — is liye
# "Sunday, WhatsApp kholo" sunne se pehle "Ji, boliye" bolna zaroori hai.
PLAYBACK_MUTE_MIC = True

# ---- wake ke jawab ----
ACK_ON_WAKE = "Ji, boliye."
NOT_HEARD = "Kuch sun nahi aaya. Dobara boliye."
STOP_WORD = ("ruk jao", "band karo", "shukriya", "thanks", "stop")

# ---- WhatsApp call (Step 2, Option A) ----
WHATSAPP_WEB = "https://web.whatsapp.com"
# CDP port. Edge/Chrome is par remote debug mode me chalta hai. Pehli baar
# WhatsApp Web QR scan karna padega (browser me khud khulta hai).
CDP_PORT = 9222
CDP_HOST = "127.0.0.1"
CALL_ASK_FIRST = True         # call se pehle confirm card (gatekeeper ka ASK)


def model_path() -> str:
    """Pehla model jo disk par maujood hai -> uska folder. Ya `''`."""
    for folder in (WAKE_MODEL_DIR, WAKE_MODEL_ALT_DIR):
        if Path(folder).is_dir():
            return folder
    return ""


def model_missing() -> str:
    """Model na ho to user ko dikhane layak ek line (ya `''` = sab theek)."""
    if model_path():
        return ""
    return ("Vosk model nahi mila: %s me folder nahi hai. "
            "README VOICE.md me command hai." % MODEL_DIR)


def wake_available() -> bool:
    """Worker chal sakta hai? -> (bool, reason)."""
    if not WAKE_ENABLED:
        return False, "PRABH_WAKE=0 se band hai"
    if not model_path():
        return False, model_missing()
    return True, ""


def describe() -> str:
    """Log + `--wake-info` ke liye ek line."""
    folder = model_path()
    return "wake=%s word=%s model=%s stt=%s" % (
        "ON" if WAKE_ENABLED else "OFF",
        "/".join(WAKE_WORDS),
        Path(folder).name if folder else "MISSING",
        config_stt_name(),
    )


def config_stt_name() -> str:
    """Command ke liye kaunsa STT — yahan `config_brain` se utha rahe hain taaki
    cycle na bane (`config.py` yahan se import karta hai, wahan se nahi)."""
    return os.getenv("PRABH_STT_MODEL", "groq-whisper")