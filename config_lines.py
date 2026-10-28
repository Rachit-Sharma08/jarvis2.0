"""Jarvis kya **bolta** hai — spoken lines, ack beep, aur ack ka peek.

Ye file 14-Oct raat me bani (`config_wake.py` 228 line par 200 cross kar gaya).
Pehle usi file ka ek precedent tha — `config_describe.py` bhi isi wajah se bana
tha — to ye usi tarike se nikala gaya hai.

**Is file me kya hai:** sirf woh cheezein jo user **sunta** hai.
- Wake ke jawab: `ACK_ON_WAKE`, `NOT_HEARD`, `NOT_UNDERSTOOD`, `BRAIN_FAILED`,
  `CONFIRM_VOICE`
- "So jao": `SLEEP_WORDS`, `SLEEP_ACK`, `SLEEP_FROM_TRAY`
- Ack beep + ack peek (`COMMAND_ACK_PEEK_SECONDS`)

**Is file me kya NAHI hai (jaan-boojh kar):**
- Wake ke **constants** (VAD, gain, command window, hot window) — `config_wake.py`
  me. `test_hot_window.py`/`test_hot_window_helpers.py` wahan ke
  `os.getenv("JARVIS_HOT_WINDOW"...)` aur `test_hearing_audit.py` ka
  `PLAYBACK_MUTE_MIC = True` **source-text** se dhoondte hain — hatate to wo
  chup-chaap fail ho jaate.
- Wake ki **functions** (`model_path`, `model_missing`, `wake_available`) —
  `config_wake.py` me hi. `test_wake.py` inhe **mutate** karta hai
  (`config_wake.WAKE_MODEL_DIR = ...`) aur phir `model_path()` se **usi**
  module ka global padha jaata hai. Kahin aur shift karte to test ka mutation
  chup-chaap bekaar ho jaata aur "model na ho to path khaali" jaisa check
  GALAT pass hota. Ye wahi galti hai jo test-fake shift na karne par hoti hai.

Ye sirf constants hai — koi logic nahi, koi API key nahi.
"""

import config_env  # noqa: F401  (purane env naam pehle alias hote hain)
import os

# ---- ack beep (12-Oct) ------------------------------------------------------
# "Ji, boliye" ~5 s leti thi (ElevenLabs 401 + edge + speaker), aur uske baad
# ka 1 s warmup command phenk deta tha. Ab beep + turant capture; `=0` par
# purana.
ACK_BEEP = os.getenv("JARVIS_WAKE_ACK_BEEP", "1").strip().lower() not in ("0", "false", "no", "off")
ACK_BEEP_HZ, ACK_BEEP_MS, ACK_BEEP_DROP_SECONDS = 880, 120, 0.2

# ---- wake ke jawab ---------------------------------------------------------
# Ye chaaron line sirf `wake/command.py` bolti hai. UI me text nahi — awaaz.
ACK_ON_WAKE = ("Ji Sir, boliye.", "At your service, Sir.", "Haan Sir.",
               "Right away, Sir.", "Sun raha hoon, Sir.")
NOT_HEARD = "Kuch sun nahi aaya. Dobara boliye."
# Awaaz saaf nahi aayi: kuch bola hi nahi, bahut chhota bola, ya STT guard ne
# ("Thank you." jaisa) reject kar diya. TEENO ka jawab ek hi line.
NOT_UNDERSTOOD = "Samajh nahi aaya, dobara boliye."
# Brain ya net fail. Chhota rakha hai — asli wajah log me hai.
BRAIN_FAILED = "Abhi jawab nahi mil pa raha."
# ASK wala tool: card screen par aayega. **Awaaz se Allow kabhi nahi** — sirf
# screen ka button. Ye line sirf itni batati hai ki screen dekh lo.
CONFIRM_VOICE = "Screen par confirm kijiye."

# ---- "so jao" (battery) ---------------------------------------------------
# Mic sunna **kabhi band nahi** hota (warna "Jarvis" sunai hi nahi dega). Is
# liye battery ka asal nuksan hataane ke liye bhaari sab (HUD, stats pump,
# browser) band karna padta hai — sirf mic + gate chalta reheta hai. Puri
# tarah band karna tray ke Quit se (CPU 0, phir "Jarvis" kaam nahi karega).
SLEEP_WORDS = ("so jao", "so jaiye", "sone jao", "soye raho", "soye rahiye",
               "so jaa", "band ho jao", "soye jao")
SLEEP_ACK = "So gaya. Jarvis boliye."      # chhota — TTS + playback = waqt
SLEEP_FROM_TRAY = "SO JAAO"                # tray ka item

# "Ji, boliye" bolne se **pehle** itni der suno (4-Oct). Agar user is dauraan
# bol hi raha hai to ack chhod do — warna hamari awaaz uske upar chadh jaati
# hai, command ka pehla shabd kat-ta hai aur use lagta hai "sun nahi pa raha".
# Isi 0.18 s ka kaam hai: mic settle + bolne ki pehli awaaz pakadna. Nahi mila
# to normal raasta (ack + 1 s warm-up). `.env` ke `JARVIS_ACK_PEEK` se.
COMMAND_ACK_PEEK_SECONDS = float(os.getenv("JARVIS_ACK_PEEK", "0.18"))