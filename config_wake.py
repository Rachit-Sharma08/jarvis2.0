"""Wake word + voice command ke constants. `import config` hi sab jagah chalta hai.

Ye Step 1 ka hissa hai. Do alag STT jaan-boojh kar:

1. **Wake word ("Jarvis")** — local Vosk, `models/vosk-model-small-en-us-0.15`.
   English model hi sahi hai kyunki "Jarvis" ek English shabd hai. Awaaz kabhi
   bahar nahi jaati, 100% offline. Shabd `config_name.py` se aate hain —
   purane "sunday" shabd wahan alag list me, default band.

2. **Command ("whatsapp kholo", "Ramesh ko phone karo")** — `voice/stt.py` ka
   Groq Whisper (`whisper-large-v3-turbo`). Ye Hinglish ka asli expert hai.

Is liye Hinglish ke liye koi 470 MB model download karne ki zarurat nahi —
dono cheezein pehle se maujood hain.

Rule: is file me koi API key nahi. Wake ka model path `BASE_DIR/models` me hai.
"""

import os
from pathlib import Path

from config_name import (
    LEGACY_WAKE_PHRASES, WAKE_PHRASES, legacy_enabled, wake_grammar, wake_words,
)

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
# galat trigger kam, aur CPU halka. Asli list `config_name.py` me hai
# (Step 1: "jarvis"; purane "sunday" shabd `LEGACY_WAKE_PHRASES` me, band).
WAKE_WORDS = wake_words()
WAKE_GRAMMAR = wake_grammar()

# ---- audio ----
SAMPLE_RATE = 16000          # Vosk isko hi maangta hai (16 kHz mono)
BLOCK_MS = 30                # 30 ms ka chunk — Vosk ke liye ideal
CHANNELS = 1
INPUT_DEVICE = os.getenv("PRABH_WAKE_MIC", "").strip() or None

# Energy VAD. Mic ki khamoshi ka level ~0.002-0.01 hota hai, insaan ki awaaz
# 0.02 se upar. Beech ka number: thodi door se awaaz bhi uth jaaye, par
# fan/hawa ka shor na pakde.
# 4-Oct: 0.012 -> **0.010**. Door se ya dheere bola "Hlo Jarvis" par trigger
# nahi ho raha tha (gate VAD par hi tika hai). 0.010 par fan ka shor nahi aata,
# kyunki wo aam taur par 0.005 se neeche rehta hai.
VAD_THRESHOLD = float(os.getenv("PRABH_VAD", "0.010"))
VAD_SILENCE_BLOCKS = 12      # ~0.36 s khamoshi = VAD ke baad band
VAD_HANGOVER_BLOCKS = 30     # ~0.9 s — VAD ke dauraan awaaz mat kaato

# ---- battery ka pakkaura ----
# Vosk ko **har** chunk dena = 3.9% CPU chalu, chahe koi na bol (battery jaati
# hai). Is liye chunk tabhi dena jab VAD bol raha ho — `wake/session.py` ka gate.
# Mic ka stream khula rehta hai (band nahi hota, crash ka raasta bhi nahi);
# sirf sunna band hota hai. `.env` ke `PRABH_VOSK_GATE=0` se gate band.
WAKE_VOSK_GATE = os.getenv("PRABH_VOSK_GATE", "1").strip() not in ("0", "false", "no")

# Ek hi "jarvis" me do trigger na ho. Wake hit ke baad itni der queue khaali
# karte hue aawaaz fenk-te hain (recognition nahi) — taaki TTS/bijli ka shor
# ya apna hi naam dobara na pakde.
WAKE_COOLDOWN_SECONDS = 1.5

# ---- command window ----
# Chuppi pehle 2.0 s -> 1.2 s -> ab **0.9 s** (4-Oct). Wake ka total 18.5 s tha,
# jisme se 2.0 s sirf is ek intezaar me jaata tha (brain to 1.1 s me jawab de
# raha tha). 0.9 s abhi bhi ek natural sentence-gap se thoda lamba hai, is liye
# beech ka vaakya kat-ta nahi. `.env` ke `PRABH_CMD_SILENCE` se badalte ho.
COMMAND_MAX_SECONDS = 30           # wake ke baad itni der suno (safety limit)
COMMAND_MIN_SECONDS = 0.6    # itni ASLI awaaz chahiye, khamoshi ginti nahi
COMMAND_END_SILENCE_SECONDS = float(os.getenv("PRABH_CMD_SILENCE", "0.9"))
COMMAND_HANGOVER_SECONDS = 0.4     # beech ka chhota ruk na kaato (wake se chhota)
# Pre-roll 0.4 -> **0.6** (4-Oct): "Hlo Jarvis, WhatsApp kholo" me pehle shabd
# "WhatsApp" ka 'a' kat-ta tha, kyunki wake shabd ke aakhri chunk ke saath hi
# bolna shuru ho jaata tha. Thoda purana buffer = pehla shabd poora.
COMMAND_PRE_ROLL_SECONDS = 0.6
COMMAND_WAIT_SECONDS = 5.0         # pehla shabd aaya hi nahi -> "sun nahi aaya"
COMMAND_WARMUP_SECONDS = 1.0       # mic settle hone do, warna pehla shabd kat-ta hai

# Bolne ke waqt sunna band rakhna. Apni hi awaaz wapas na aaye — is liye
# "Jarvis, WhatsApp kholo" sunne se pehle "Ji, boliye" bolna zaroori hai.
PLAYBACK_MUTE_MIC = True

# "Ji, boliye" bolne se **pehle** itni der suno (4-Oct). Agar user is dauraan
# bol hi raha hai to ack chhod do — warna hamari awaaz uske upar chadh jaati
# hai, command ka pehla shabd kat-ta hai aur use lagta hai "sun nahi pa raha".
# Isi 0.18 s ka kaam hai: mic settle + bolne ki pehli awaaz pakadna. Nahi mila
# to normal raasta (ack + 1 s warm-up). `.env` ke `PRABH_ACK_PEEK` se.
COMMAND_ACK_PEEK_SECONDS = float(os.getenv("PRABH_ACK_PEEK", "0.18"))

# ---- wake ke jawab ----
# Ye chaaron line sirf `wake/command.py` bolti hai. UI me text nahi — awaaz.
ACK_ON_WAKE = "Ji, boliye."
NOT_HEARD = "Kuch sun nahi aaya. Dobara boliye."
# Awaaz saaf nahi aayi: kuch bola hi nahi, bahut chhota bola, ya STT guard ne
# ("Thank you." jaisa) reject kar diya. TEENO ka jawab ek hi line.
NOT_UNDERSTOOD = "Samajh nahi aaya, dobara boliye."
# Brain ya net fail. Chhota rakha hai — asli wajah log me hai.
BRAIN_FAILED = "Abhi jawab nahi mil pa raha."
# ASK wala tool: card screen par aayega. **Awaaz se Allow kabhi nahi** — sirf
# screen ka button. Ye line sirf itni batati hai ki screen dekh lo.
CONFIRM_VOICE = "Screen par confirm kijiye."
STOP_WORD = ("ruk jao", "band karo", "shukriya", "thanks", "stop")

# ---- "so jao" (battery) ----
# Mic sunna **kabhi band nahi** hota (warna "Jarvis" sunai hi nahi dega). Is liye
# battery ka asal nuksan hataane ke liye bhaari sab (HUD, stats pump, browser)
# band karna padta hai — sirf mic + gate chalta reheta hai. Puri tarah band karna
# tray ke Quit se (CPU 0, phir "Jarvis" kaam nahi karega).
SLEEP_WORDS = ("so jao", "so jaiye", "sone jao", "soye raho", "soye rahiye",
               "so jaa", "band ho jao", "soye jao")
SLEEP_ACK = "So gaya. Jarvis boliye."      # chhota — TTS + playback = waqt
SLEEP_FROM_TRAY = "SO JAAO"                # tray ka item

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
    return "wake=%s word=%s%s model=%s stt=%s gate=%s" % (
        "ON" if WAKE_ENABLED else "OFF",
        "/".join(WAKE_WORDS),
        "+legacy" if legacy_enabled() else "",
        Path(folder).name if folder else "MISSING",
        config_stt_name(),
        "on" if WAKE_VOSK_GATE else "off",
    )


def config_stt_name() -> str:
    """Command ke liye kaunsa STT — yahan `config_brain` se utha rahe hain taaki
    cycle na bane (`config.py` yahan se import karta hai, wahan se nahi)."""
    return os.getenv("PRABH_STT_MODEL", "groq-whisper")