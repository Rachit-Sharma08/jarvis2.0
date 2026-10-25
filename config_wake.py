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


# ---- battery ka pakkaura ----
# Vosk ko **har** chunk dena = 3.9% CPU chalu, chahe koi na bol (battery jaati
# hai). Is liye chunk tabhi dena jab VAD bol raha ho — `wake/session.py` ka gate.
# Mic ka stream khula rehta hai (band nahi hota, crash ka raasta bhi nahi);
# sirf sunna band hota hai. `.env` ke `PRABH_VOSK_GATE=0` se gate band.
WAKE_VOSK_GATE = os.getenv("PRABH_VOSK_GATE", "1").strip() not in ("0", "false", "no")

# Ek hi "jarvis" me do trigger na ho. Wake hit ke baad itni der queue khaali
# karte hue aawaaz fenk-te hain (recognition nahi) - taaki TTS/bijli ka shor
# ya apna hi naam dobara na pakde.
WAKE_COOLDOWN_SECONDS = 1.5

# ---- mic kholne ki koshish (5-Oct) -----------------------------------------
# Ek koshish me app hamesha "wake: nahi chala" ho jati thi, jabki MicUnavailable
# (PortAudio `MME error 1`) ka matlab hota hai device **busy** hai - Chrome/Teams
# ka mic tab. Ab 3 koshish, beech me chhota intezaar. `.env` se badal sakte ho.
MIC_OPEN_ATTEMPTS = int(os.getenv("PRABH_MIC_ATTEMPTS", "3"))
MIC_OPEN_RETRY_SECONDS = float(os.getenv("PRABH_MIC_RETRY", "1.2"))

# ---- command window ----
# Chuppi pehle 2.0 s -> 1.2 s -> 0.9 s -> ab **0.7 s** (13-Oct). Har 0.1 s yahan
# seedha wake ke total me judta hai. 0.7 s ek normal sentence-gap se ab bhi
# lamba hai, is liye beech ka vaakya kat-ta nahi. `.env` ke `PRABH_CMD_SILENCE`
# se badalte ho — **wo raasta bilkul waisa hi hai.**
COMMAND_MAX_SECONDS = 30           # wake ke baad itni der suno (safety limit)
COMMAND_MIN_SECONDS = 0.6    # itni ASLI awaaz chahiye, khamoshi ginti nahi
COMMAND_END_SILENCE_SECONDS = float(os.getenv("PRABH_CMD_SILENCE", "0.7"))
COMMAND_HANGOVER_SECONDS = 0.4     # beech ka chhota ruk na kaato (wake se chhota)
# Pre-roll 0.4 -> **0.6** (4-Oct): "Hlo Jarvis, WhatsApp kholo" me pehle shabd
# "WhatsApp" ka 'a' kat-ta tha, kyunki wake shabd ke aakhri chunk ke saath hi
# bolna shuru ho jaata tha. Thoda purana buffer = pehla shabd poora.
COMMAND_PRE_ROLL_SECONDS = 0.6
COMMAND_WAIT_SECONDS = 5.0         # pehla shabd aaya hi nahi -> "sun nahi aaya"
COMMAND_WARMUP_SECONDS = 1.0       # mic settle hone do, warna pehla shabd kat-ta hai

# ---- hot window (13-Oct, KAAM 5) -------------------------------------------
# Jawab ke baad **"Jarvis" na bole** follow-up puchh sakte ho. Us window me
# sirf bolna sunna kaafi hai.
#
# **DEFAULT OFF** (`PRABH_HOT_WINDOW=0`). Naye mic/awaaz wale feature ka yahi
# niyam hai - jab tak Rachit on na kare, `Trigger.hot_active()` hamesha False
# rahega aur raasta purane waise hi chalega.
HOT_WINDOW_ENABLED = os.getenv("PRABH_HOT_WINDOW", "0").strip().lower() in (
    "1", "true", "yes", "on")
# Kitni der. Follow-up par window **dobara** lag jaata hai, is liye teen
# follow-up chain kar sakte ho (test me wahi hai).
HOT_WINDOW_SECONDS = float(os.getenv("PRABH_HOT_WINDOW_SECONDS", "12") or 12)

# Bolne ke waqt sunna band rakhna. Apni hi awaaz wapas na aaye — is liye
# "Jarvis, WhatsApp kholo" sunne se pehle "Ji, boliye" bolna zaroori hai.
#
# â„ `PLAYBACK_MUTE_MIC` **kahin use nahi hota** (13-Oct ka audit: sirf define
# hai, koi code nahi padhta). Asli rok ka raasta `wake/worker.py` ka
# `hold_for_command()` / `release_from_command()` hai - command poore chalte
# tak sunna band, phir chhod dena. Ye flag abhi bhi pada hai taaki purana
# `.env` me koi use na toot jaaye; naya kaam is par nahi banaya.
PLAYBACK_MUTE_MIC = True

# ---- tail guard (13-Oct, KAAM 2) -------------------------------------------
# **Apni hi awaaz se WAKE HIT** ka asli nuksan yahi hai. Command ke dauraan
# jab ka nahi hota; nuksan `release_from_command()` ke **turant baad** hota hai:
# mic ki queue me humari TTS ka poora shor pada hota hai, aur `drain()` sirf
# `MAX_QUEUE_BLOCKS` (400 chunk = ~12 s) tak phenkta hai. Jawab 18 s me banta
# hai (log: `speak 18530ms`), to queue me ~6 s ki apni awaaz **bachi** rehti
# hai - aur `take_fresh()` sirf **ek** chunk bachata hai. Uske baad Vosk ko
# wahi shor jaata hai.
#
# Is liye: hold chhodte hi `TAIL_GUARD_SECONDS` tak **koi bhi chunk** trigger
# nahi kar sakta. Raasta `wake/trigger.py` ka `suppressing()` hai, aur
# `Session._loop` wahi check karta hai.
PLAYBACK_TAIL_GUARD_SECONDS = float(os.getenv("PRABH_TAIL_GUARD", "0.4") or 0.4)


# ---- wake debug (4-Oct, doosra command nahi sunta tha) ----------------------
# `PRABH_WAKE_DEBUG=1` se har 3 second ek line: kitne chunk aaye, kitne Vosk
# ko gaye, kitne chhode, RMS kya tha. Isi se pata chala ki command ke baad
# chunk **aate hi nahi** (mic/pump), ya aate hain par VAD "khamoshi" bolta hai.
# Hamesha band — sirf bug pakadne ke liye.
WAKE_DEBUG = os.getenv("PRABH_WAKE_DEBUG", "0") not in ("0", "", "no", "false")
WAKE_DEBUG_SECONDS = 3.0


# ---- WhatsApp call (Step 2, Option A) ----------------------------------------
# Ye char constant ab `config_tools.py` me hain (WhatsApp Web ek tool hai) —
# `config.py` waise bhi re-export karta hai. 5-Oct: file 200 cross thi.


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


# describe()/config_stt_name() ab config_describe.py me hain (file 200 cross).
# Yahan se re-export, is liye config.describe aur config_wake.describe dono
# pehle jaise chalte hain.
from config_describe import config_stt_name, describe  # noqa: E402,F401

# ---- "Jarvis kya bolta hai" (14-Oct: file 200 cross) ----------------------
# Spoken lines, ack beep aur ack peek ab `config_lines.py` me hain. Yahan se
# **re-export** — is liye `config.X` aur `config_wake.X` dono pehle jaise
# chalte hain (isi file me `config_describe` ka bhi yahi kiya gaya hai).
#
# Model ki functions (`model_path`/`wake_available`) jaan-boojh kar yahin
# rakhe gaye hain: `test_wake.py` `config_wake.WAKE_MODEL_DIR` **mutate** karta
# hai aur phir `model_path()` se usi module ka global padha jaata hai. Kahin
# aur shift karte to wo mutation bekaar hota aur "model na ho" wala check
# chup-chaap GALAT pass hota.
from config_lines import (  # noqa: E402,F401
    ACK_BEEP, ACK_BEEP_DROP_SECONDS, ACK_BEEP_HZ, ACK_BEEP_MS,
    ACK_ON_WAKE, BRAIN_FAILED, COMMAND_ACK_PEEK_SECONDS, CONFIRM_VOICE,
    NOT_HEARD, NOT_UNDERSTOOD, SLEEP_ACK, SLEEP_FROM_TRAY, SLEEP_WORDS,
    STOP_WORD,
)

# ---- audio (14-Oct: file 200 cross) ---------------------------------------
# Sample rate, device, VAD aur digital gain ab `config_audio.py` me hain.
# Yahan se **re-export** — is liye `config.VAD_THRESHOLD` aur
# `config_wake.VAD_THRESHOLD` dono pehle jaise chalte hain.
#
# Ye hissa is liye nikala ki 200 cross ho raha tha; koi test inhe source-text
# se nahi dhoondta, is liye koi test reference shift nahi hua.
from config_audio import (  # noqa: E402,F401
    BLOCK_MS, CHANNELS, INPUT_DEVICE, INPUT_GAIN, INPUT_GAIN_MAX,
    INPUT_GAIN_TARGET, INPUT_HOSTAPI, SAMPLE_RATE, VAD_HANGOVER_BLOCKS,
    VAD_SILENCE_BLOCKS, VAD_THRESHOLD,
)
