"""Computer vision ke settings. `config.py` me wapas re-export hote hain.

Rules: is file me **koi API key nahi**, aur camera ka koi model file yahan nahi
(wo `data/` me hota hai, jo gitignored hai).

**DEFAULT OFF** (`JARVIS_VISION=0`). Ye project ka pakka niyam hai — naya
mic/camera feature tab tak band rahega jab tak owner khud na on kare. wajah:
camera on = battery + privacy. Aur jab tak `insightface` install nahi hota,
feature chalta hua dikhna hi galat hoga (usme se har command DENY hoti hai).

Toggle aur uske asar:

| `JARVIS_VISION` | Asar |
|---|---|
| `0` (default) | `allowed()` bilkul pehle jaisa — koi camera nahi khulta |
| `1` | Har command se pehle camera se ek frame, phir owner match |

`0` par bhi `allowed()` **tezi se** wapas jaata hai (ek dict lookup) — camera
kabhi initialize hi nahi hota.
"""

import config_env  # noqa: F401  (purane env naam pehle alias hote hain)
import os

# **Yahan `log_setup` import NAHI kar sakte.** Wajah (15-Oct raat ko 3 test
# is wajah se toote — `test_pool`, `test_probe`, `test_stt_guard`):
#   `log_setup.py` khud `from config import LOG_DIR, LOG_FILE` karta hai.
#   Aur `config.py` me hum yahan se aate hain.
#   Is liye `config -> config_vision -> log_setup -> config` = **circular**, aur
#   `get_logger` "partially initialized module" error dekar app ka config hi
#   tod deta hai.
#
# Is project ka pakka niyam: **`config_*.py` kabhi `log_setup` import nahi karta**
# (ye ek hi file tha jo karti thi). Sab kuch constants hai, logging nahi.

# ---- kholna / band karna ----
# Default **0** — OFF. Mic/camera ka naya feature is project me default OFF
# hota hai (AGENTS.md: DEFAULT OFF).
VISION_ENABLED = os.getenv("JARVIS_VISION", "0").strip().lower() in (
    "1", "true", "yes", "on")

# ---- match ka cut-off ----
# `identity.DEFAULT_THRESHOLD` ka override. **Guess mat karna** — apni webcam
# se enroll karke tune karo (enroll.py docstring dekho).
_threshold = os.getenv("JARVIS_VISION_THRESHOLD", "").strip()
try:
    VISION_THRESHOLD = float(_threshold) if _threshold else None
except ValueError:
    # Galat value par chup-chaap default (fail-safe: default bhi kaam karta hai).
    # `log_setup` yahan nahi import kar sakte (circular — upar dekho), is liye
    # galat value ka pata `state()` se lagega, log se nahi.
    VISION_THRESHOLD = None

# ---- camera ----
# Default 0 = Windows ka default camera. Diya ho to wo index.
CAMERA_INDEX = int(os.getenv("JARVIS_VISION_CAM", "0") or 0)
# Frame width. Chhota = tez + battery; 640 bade chehre ke liye kaafi hai.
CAMERA_WIDTH = int(os.getenv("JARVIS_VISION_WIDTH", "640") or 640)
CAMERA_HEIGHT = int(os.getenv("JARVIS_VISION_HEIGHT", "480") or 480)

# Enrollment me kitne frames lene hain. 15 asli bana dete hain (bina dikhne
# wali explanation se utna hi fayda, aur battery zyada).
ENROLL_SAMPLES = int(os.getenv("JARVIS_VISION_SAMPLES", "15") or 15)

# ---- guard ki wajah ----
# Ye line HUD par aur log me dikhti hai. Chhoti rakhi hai (clip_answer ke saath).
# Awaaz se ALLOW kabhi nahi — bilkul gatekeeper card jaisa.
NEEDS_ENROLL = "Pehle apna chehra register karo."
NEEDS_CAMERA = "Camera nahi khul raha."
NOT_OWNER = "Ye aap nahi hain."
TOO_FAST = "Camera check, thoda intezaar kijiye."


def state() -> dict:
    """HUD/debug ke liye ek line — koi raw data nahi."""
    from vision import backend, store
    if not VISION_ENABLED:
        return {"on": False, "label": "OFF"}
    return {"on": True, "label": "ON", "enrolled": store.enrolled(),
            "backend": backend.status().get("backend", "none")}