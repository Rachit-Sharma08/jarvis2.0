"""Wake ka **audio** hissa — sample rate, device, VAD, aur digital gain.

Ye file 14-Oct raat me bani (`config_wake.py` 228 line par 200 cross kar gaya).
Isi file ka doosra hissa `config_lines.py` (Jo Jarvis bolta hai).

Ye sirf **mic se aane wali signal** ki settings hai. Wake word ka grammar
`config_wake.py` me hai, command window bhi wahin hai.

Ye teenon ka ek ghar is liye hai kyunki inka ek hi asli kaam hai — **kitna
awaaz "bol raha hai" maana jaye** (VAD threshold) aur **kitna tez sunen**
(hostapi + gain). Ye teen alag-alag rakhne par ek hi bug ki tafseer teen
file me fail ho jaati.

Koi API key nahi. Sirf `os.getenv`.
"""

import os

# ---- audio basics ----
SAMPLE_RATE = 16000          # Vosk isko hi maangta hai (16 kHz mono)
BLOCK_MS = 30                # 30 ms ka chunk — Vosk ke liye ideal
CHANNELS = 1
INPUT_DEVICE = os.getenv("PRABH_WAKE_MIC", "").strip() or None
# 5-Oct ka sabse bada bug: **MME** ka mic kachra deta tha (peak -19..-52 dB, Vosk
# `"hey"`/`"huh"` sunta tha, 0 jarvis-hit). **WASAPI** par peak -7.6 dB aur wahi
# grammar `"hello jarvis"` pakad leti thi. Is liye mic WASAPI se khulta hai.
# Device number `PRABH_WAKE_MIC` se diya ho to wo pehle (user ka faisla).
INPUT_HOSTAPI = os.getenv("PRABH_WAKE_MIC_HOSTAPI", "WASAPI").strip().upper()

# Energy VAD. **5-Oct ka doosra asli bug yahin tha**: mic WASAPI se theek khul
# raha tha, lekin door/dheere bolne par chunk ka RMS sirf **0.0055** hota tha,
# jabki threshold 0.010 tha — 90 s me 3003 chunk me se sirf **31** chunk Vosk
# tak pahuncha aur `finals=0` raha. Mic ki khamoshi 0.0000-0.0026 hai (fan/hawa),
# aur paas bolne par RMS 0.023 (peak 0.81) — wahi audio Vosk ne "hello jarvis"
# pehchan liya. Is liye threshold beech me.
# Fan ka shor 0.0026 se upar nahi jaata, to VAD band nahi hota.
# 4-Oct: 0.012 -> 0.010 -> 5-Oct: 0.004 -> ab **0.0075**. `.env` ke `PRABH_VAD`.
VAD_THRESHOLD = float(os.getenv("PRABH_VAD", "0.0075"))
VAD_SILENCE_BLOCKS = 12      # ~0.36 s khamoshi = VAD ke baad band
VAD_HANGOVER_BLOCKS = 30     # ~0.9 s — VAD ke dauraan awaaz mat kaato

# ---- digital gain (5-Oct ka teesra bug) -------------------------------------
# Level par 100x ka farak tha: door/dheere bolne par RMS **0.0014**, paas-zor
# bolne par **0.16** (peak 0.99). Wahi audio gain se theek hua — 8x par `hello`
# + `jarvis` dono finals me aa gaye. Ye `wake/pcm.py` ka `AutoGain` hai jo
# sirf **awaaz** par lagta hai, khamoshi par nahi (warna VAD hamesha "bol raha
# hai" bolta aur battery jaati).
# `.env`: `PRABH_WAKE_GAIN=auto` (default) | koi number (fixed gain) | `0`/`off`
INPUT_GAIN = os.getenv("PRABH_WAKE_GAIN", "auto").strip().lower()
INPUT_GAIN_TARGET = float(os.getenv("PRABH_WAKE_GAIN_TARGET", "0.12"))
INPUT_GAIN_MAX = float(os.getenv("PRABH_WAKE_GAIN_MAX", "12"))