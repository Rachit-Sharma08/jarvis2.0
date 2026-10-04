"""Tray icon ke constants + uska watchdog. `config.py` inhe re-export karta hai.

`config_desktop.py` 198 lines par tha, is liye tray ke naye switches yahan aaye
(ek file, ek kaam ka niyam).

**Ye kya karta hai (roadmap T-01, section 6):** Windows me naye exe ka icon aksar
taskbar ke `^` (hidden icons) me chhup jaata hai, aur pystray ko pata hi nahi
chalta (`NIM_ADD` ka return woh ignore karta hai). Is liye app roz ye dekhta hai
ki icon taskbar me dikh raha hai ya nahi — asli check `desktop/tray_watch.py`
karta hai, yahan sirf timing hai.

Rule: is file me koi logic nahi, sirf numbers.
"""

import os

# Watchdog chalu hai ya nahi. Default ON. `.env` me `PRABH_TRAY_WATCH=0` se band.
TRAY_WATCH_ENABLED = os.getenv("PRABH_TRAY_WATCH", "1") == "1"

# Pehle itne second tak tez-dekh (app shuru hote hi Explorer ko taskbar me icon
# lagane me thoda time lagta hai — is liye 60 s), phir dheere.
TRAY_WATCH_FIRST_SECONDS = 60.0
TRAY_WATCH_FAST_SECONDS = 3.0
TRAY_WATCH_SLOW_SECONDS = 30.0