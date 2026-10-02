"""Desktop shell (Phase 5 Step 3a) ke constants. Ek file, ek kaam.

Sirf values aur chhote helpers — koi logic nahi. `config.py` inhe re-export
karta hai, isliye baaki code `config.HUD_WIDTH` jaisa hi likhta hai.

Teen hisse:
- HUD window: Edge/Chrome `--app=` mode, apna user-data-dir, ek hi window
- Tray icon: state ke rang (mic ka nishaan hamesha icon me)
- Supervisor: crash par restart + single instance + Windows login autostart

Rule: is file me koi API key nahi, koi registry likhwat nahi (wo `desktop/`
me hai, taaki test me aasaani se na mile).
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Runtime data. `.gitignore` me hai — face data, lock file, browser profile
# yahin bante hain. Kabhi bhi repo me commit nahi hote.
DATA_DIR = BASE_DIR / "data"
LOCK_FILE = DATA_DIR / "prabh.lock"

# ---- HUD window: Edge/Chrome --app mode ----
# pywebview nahi: uske liye 4 extra package (pythonnet, clr_loader, bottle,
# proxy_tools) chahiye aur pythonnet CLR baaki packages se takra sakta hai.
# --app mode me koi naya package nahi, security model bilkul waisa hi rehta
# hai (wahi URL, wahi token, wahi CSP). Choice ka poora record CHANGELOG.md me.
HUD_PATH = "/"
HUD_WIDTH = 1200
HUD_HEIGHT = 720
# Apna alag profile — isse Sunday ka browser instance tumhare normal browsing
# se alag rehta hai. Doosri baar `--app` bulao to browser isi profile me
# naya window nahi banata, purane ko focus karke khud exit ho jaata hai.
HUD_PROFILE_DIR = DATA_DIR / "hud-profile"
# HUD apne aap sirf wake word par khulta hai. Chalu hote hi khulna ho to
# `.env` me PRABH_HUD_AT_START=1, ya `python -m desktop.app --hud`.
HUD_OPEN_AT_START = os.getenv("PRABH_HUD_AT_START", "0") == "1"

# ---- HUD ke do aur raasta (tray par nirbhar na rahein) ----
# Tray icon Windows ke overflow `^` me chhup jaata hai (ye Windows ka normal
# behaviour hai, pystray ki galti nahi), is liye ek teesra raasta zaroori hai:
#   1. Desktop ka shortcut "Sunday HUD"  -> `desktop/shortcut.py`
#   2. Global hotkey (default Ctrl+Alt+S) -> `desktop/hotkey.py`
# Dono ka **ek hi kaam** `desktop/open_hud.py` karta hai: server zinda hai to
# HUD window khol do, warna saaf message. Doosra koi raasta kabhi mat banao.
HUD_SHORTCUT_NAME = "Sunday HUD"
# `.env` me PRABH_HUD_HOTKEY=<ctrl+alt+shift+s> se badal do. Galat ya khali
# value par hotkey chalti hi nahi — app bilkul safe rehta hai.
HUD_HOTKEY = os.getenv("PRABH_HUD_HOTKEY", "ctrl+alt+s")

# Pehle Edge, phir Chrome. Dono Windows 10/11 ke saath aate hain — inhe
# install karne ki zarurat nahi.
BROWSER_CANDIDATES = (
    (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "Edge"),
    (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", "Edge"),
    (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "Chrome"),
    (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "Chrome"),
)
BROWSER_ON_PATH = (("msedge", "Edge"), ("chrome", "Chrome"))

# ---- Tray icon: state ka rang ----
# Mic ka nishaan hamesha icon me rehta hai. Rang = halaat:
#   DIM   — mic band (app chalu hi nahi / quit)
#   CYAN  — sun raha hai (wake kaam kar raha hai)
#   AMBER — mute (user ne band kiya)
#   RED   — mic error (device nahi khul raha / permission nahi)
TRAY_IDLE = "idle"
TRAY_LISTENING = "listening"
TRAY_MUTED = "muted"
TRAY_ERROR = "error"
TRAY_OFF = "off"
TRAY_COLORS = {
    TRAY_OFF: "#4a5a6a",
    TRAY_IDLE: "#2ea8ff",
    TRAY_LISTENING: "#4cc3ff",
    TRAY_MUTED: "#f5a623",
    TRAY_ERROR: "#e0483c",
}
TRAY_TITLE = {
    TRAY_OFF: "Sunday — band",
    TRAY_IDLE: "Sunday — suna nahi raha",
    TRAY_LISTENING: "Sunday — sun raha hai",
    TRAY_MUTED: "Sunday — mic mute",
    TRAY_ERROR: "Sunday — mic error",
}
TRAY_NAME = "Sunday"

# ---- Supervisor: crash par restart ----
# Child (desktop.app) crash ho to supervisor use dobara chala deta hai.
# Zyada crash ho to ruk jaata hai — Warna koi crash-loop chalu ho jaata aur
# RAM/CPU khaali karega. Upar se chalao (`start_prabh.bat`).
RESTART_MAX = 5
RESTART_WINDOW_SECONDS = 10 * 60
RESTART_BACKOFF = (2, 5, 10, 20, 30)

# Exit code — supervisor isi se samajhta hai ki crash hua ya user ne band
# kiya. Crash par dobara chalao; 0 (saaf band) par kuch nahi.
EXIT_QUIT = 0
EXIT_RESTART = 20
EXIT_ALREADY_RUNNING = 3
# Tray icon nahi bana to app band. Bina tray ke app chalta rahe to usse band
# karne ka koi raasta hi nahi hota - is liye ye alag exit code hai.
EXIT_NO_TRAY = 4
# Tray icon banane ki kitni koshish (pystray kabhi kabhi pehli baar chhoot deta hai).
TRAY_START_ATTEMPTS = 3

# ---- Startup ke 4 standard line ----
# Ye chaar line hamesha isi shabd me aati hain — console par bhi aur
# `logs/prabh.log` me bhi — taaki crash ke waqt pata chale app kahan tak
# pahunchi thi. Sirf `desktop/app.py` inhe bolta hai (ek hi jagah).
STARTUP_SERVER = "server up"
STARTUP_TRAY = "tray started"
STARTUP_HUD = "HUD ready"
STARTUP_WAKE = "wake"
# Kitni der tak startup ka intezaar — phir "HUD ready: FAILED" bol kar aage badho.
STARTUP_HTTP_TIMEOUT = 20.0

# ---- Speaker (Step 2: "Ji, boliye" aur jawab ki awaaz) ----
# TTS ke mp3/wav bytes `desktop/playback.py` me `miniaudio` se 16-bit PCM me
# badal kar `sounddevice` se bajte hain. Mic ki taraf ka rule yahi hai — ek hi
# jagah (`wake/audio.py`), koi doosra `OutputStream` nahi.
# Device khali chhodne par Windows ka default speaker chalta hai. Device badalna
# ho to `.env` me PRABH_SPEAKER=<device name>; list ke liye
# `python -m desktop.playback --list`.
OUTPUT_DEVICE = os.getenv("PRABH_SPEAKER", "").strip() or None
# 32 kHz mono. TTS 22-24 kHz deta hai, is se upar jaane se koi fayda nahi aur
# resample ka kaam bhi kam hota hai.
OUTPUT_RATE = int(os.getenv("PRABH_SPEAKER_RATE", "32000"))
# TTS + decode + play ka total intezaar. Is se zyada lage to chup kar do —
# wake thread ko rok na sakte.
PLAYBACK_TIMEOUT_SECONDS = 45.0

# ---- Suraksha ----
# TOOLS ON karne ke 30 minute baad apne aap OFF. Wake se bhi gatekeeper
# bilkul waisa hi hai — awaaz se Allow kabhi nahi hota.
TOOLS_AUTO_OFF_MINUTES = 30
# Windows lock (Win+L) ka pata. Tools lock par OFF ho jaate hain — sirf
# baat-cheet chalti hai. Detect na ho to sirf report hota hai, block nahi.
LOCK_POLL_SECONDS = 2.0

# ---- Windows login par auto-start ----
# HKCU = sirf is user ka, admin ya UAC nahi chahiye. Value tabhi likhi jaati
# hai jab user "haan" bole (desktop/autostart.py).
AUTOSTART_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_NAME = "Prabh"

# "Let desktop apps access your microphone" ka master switch. Value = Deny
# hua to sounddevice device khol hi nahi paayega.
MIC_CONSENT_KEY = (
    r"Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager"
    r"\ConsentStore\microphone"
)


def browser_path() -> tuple:
    """-> (exe_path, browser_name) ya ('', ''). Edge pehle, phir Chrome."""
    for path, name in BROWSER_CANDIDATES:
        if os.path.isfile(path):
            return path, name
    for exe, name in BROWSER_ON_PATH:
        found = shutil.which(exe)
        if found:
            return found, name
    return "", ""


def tray_color(state: str) -> str:
    return TRAY_COLORS.get(state, TRAY_COLORS[TRAY_OFF])


def tray_title(state: str) -> str:
    return TRAY_TITLE.get(state, TRAY_TITLE[TRAY_OFF])


def backoff_for(attempt: int) -> int:
    """Crash #1 ke liye pehla backoff. List khatam to aakhri wala."""
    if not RESTART_BACKOFF:
        return 0
    index = min(max(attempt, 1), len(RESTART_BACKOFF)) - 1
    return RESTART_BACKOFF[index]
