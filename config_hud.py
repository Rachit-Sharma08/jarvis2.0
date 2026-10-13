"""HUD (Phase 4) ke settings. Ek file, ek kaam — sirf constants aur helpers.

Ye `config.py` me re-export hote hain, isliye baaki code ko `config.WEATHER_CITY`
jaisa hi likhna hai. Is file me koi logic nahi, sirf values aur chhote helpers.

Rules: yahan koi API key nahi. Weather ke liye key chahiye hi nahi (Open-Meteo).

KAAM B (14-Oct): naya "arc" theme yahin se aata hai (`PRABH_HUD_THEME`).
Default `"neon"` — yaani Phase 4 wala neela HUD bilkul waisa hi rehta hai.
"""

import os

# ---- Colors: reference photo + spec dono se ----
# Photo washed-out thi, isliye saturation thodi barh kar diya. Exact value
# design/reference.png ke grid analysis se aayi hai.
CYAN = "#2ea8ff"
CYAN_BRIGHT = "#4cc3ff"
CYAN_DIM = "#1c5f9e"
AMBER = "#f5a623"

# ---- Theme: purana neela (default) ya naya "arc" (KAAM B, 14-Oct) ----
# `PRABH_HUD_THEME` se. Default `"neon"` = Phase 4 wala neela HUD, bilkul
# waisa hi. `?theme=arc` URL par bhi on/off ho sakta hai (test/record ke liye).
#
# Sirf LOOK ka reference <https://jarvis.mukh1.com> se liya gaya hai — unka
# code/CSS/SVG/asset copy nahi kiya gaya. Chhota credit footer me hai.
HUD_THEME_DEFAULT = "neon"
HUD_THEMES = ("neon", "arc")
# Arc theme ka credit (footer me chhota). Reference ka naam — design bana
# apna hai, sirf look ka.
ARC_CREDIT = "Interface style inspired by Mukh.1"

# ---- Arc theme: performance + a11y (i5 laptop ke liye) ----
# Sirf CSS transform/SVG animation — WebGL ya bhaara canvas NAHI.
ARC_FPS = 30                 # isse tez raf nahi (i5 par battery)
ARC_FRAME_MS = int(1000 / ARC_FPS)
ARC_PAUSE_WHEN_HIDDEN = True # window background me — rAF band
# Animation CSS hi chalati hai; `prefers-reduced-motion` ko maanta hai.
# Ye sirf JS raf (typewriter/orbit number) ke liye hai.
ARC_TYPE_MS = 28             # typewriter: ek character
ARC_ACTIVITY_MAX = 6         # right panel me kitni purani lines
ARC_TICK_COUNT = 72          # reactor ke bahar tick-marks
ARC_HEX_NODES = 6            # hexagon nodes
ARC_ORBIT_DOTS = 3           # ghoomte dots

# ---- Fonts: Arc theme ----
# Devanagari **laptop ke maujood font** se. Internet se koi font nahi —
# CSP `default-src 'self'` hai aur offline bhi chalna hai. Windows 10/11
# par Nirmala UI hota hi hai; Noto Sans Devanagari tab jab installed ho.
ARC_FONT_MONO = ('"Share Tech Mono", "Nirmala UI", "Noto Sans Devanagari", '
                 'Consolas, monospace')
ARC_FONT_BODY = ('"Rajdhani", "Nirmala UI", "Noto Sans Devanagari", '
                 '"Segoe UI", sans-serif')
ARC_FONT_HEAD = ('"Orbitron", "Nirmala UI", "Noto Sans Devanagari", '
                 '"Segoe UI", sans-serif')

# ---- Arc theme: colours (CSS variables ke andar jayengi) ----
# Gehra baingani-kaala + patli orange.
ARC_BG = "#08050e"
ARC_PANEL = "rgba(19, 12, 28, 0.72)"
ARC_LINE = "rgba(255, 138, 46, 0.22)"
ARC_ACCENT = "#ff8a2e"       # patli orange
ARC_ACCENT_2 = "#ff5e3a"     # garm lali/orange (core ke andar)
ARC_ACCENT_DIM = "#8a4a16"
ARC_INK = "#f2e6da"
ARC_INK_DIM = "#a08a78"
ARC_GOOD = "#5cffb0"
ARC_BAD = "#ff6b6b"

# ---- Arc: routing chip (WAKE -> STT -> BRAIN -> TTS) ----
ARC_ROUTING = ("WAKE", "STT", "BRAIN", "TTS")
ARC_ROUTING_CHANNEL = "LOCAL"

# ---- Fonts (ui/fonts.css me load, fallback yahan) ----
FONT_HEAD = '"Orbitron", "Rajdhani", "Segoe UI", sans-serif'
FONT_BODY = '"Rajdhani", "Segoe UI", sans-serif'
FONT_MONO = '"Share Tech Mono", "Consolas", monospace'

# ---- Left column: CHRONOMETER ----
CLOCK_DATE_FORMAT = "%A, %d %B %Y"   # Wednesday, 30 September 2026
CLOCK_TICK_MS = 1000                 # seconds ka chhota ring 1 second me

# ---- Left column: SYSTEM ----
STATS_INTERVAL_SECONDS = 2.0   # WebSocket par stats bhejne ka gap
STATS_CACHE_SECONDS = 1.5      # ek hi sample itni der me dobara nahi padhna
NET_MB = 1024 ** 2             # bytes -> MB me convert

# ---- Right column: WEATHER ----
WEATHER_CITY = "Delhi"
WEATHER_LAT = 28.6139
WEATHER_LON = 77.2090
WEATHER_CACHE_SECONDS = 15 * 60   # 15 minute — bahar zyada call nahi
WEATHER_TIMEOUT_SECONDS = 6.0
WEATHER_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
    "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
    "&daily=temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=1"
)
# WMO weather code -> chhota label. Poora table nahi, sirf jo dikhta hai.
WEATHER_CODES = {
    0: "Clear Sky", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime Fog", 51: "Light Drizzle", 53: "Drizzle",
    55: "Heavy Drizzle", 61: "Light Rain", 63: "Rain", 65: "Heavy Rain",
    71: "Light Snow", 73: "Snow", 75: "Heavy Snow", 80: "Rain Showers",
    81: "Rain Showers", 82: "Violent Showers", 95: "Thunderstorm",
    96: "Thunderstorm", 99: "Thunderstorm",
}
# Gauge -20°C .. 50°C
TEMP_MIN = -20
TEMP_MAX = 50

# ---- Bottom bar: quick buttons ----
# Har button ka kaam `engine.run_tool()` se jaata hai — gatekeeper ke bagal se
# nahi. Isliye yahan sirf (id, label, tool, args) hai; args user se nahi aate.
DEFAULT_BROWSER_URL = "https://www.google.com"
MUSIC_URL = "https://www.youtube.com/results?search_query=lofi+hindi"

# id, label, tool, args
QUICK_BUTTONS = (
    {"id": "browser", "label": "BROWSER", "tool": "open_website",
     "args": {"url": DEFAULT_BROWSER_URL}},
    {"id": "youtube", "label": "YOUTUBE", "tool": "open_website",
     "args": {"url": "https://www.youtube.com"}},
    {"id": "whatsapp", "label": "WHATSAPP", "tool": "open_website",
     "args": {"url": "https://web.whatsapp.com"}},
    {"id": "music", "label": "MUSIC", "tool": "open_website",
     "args": {"url": MUSIC_URL}},
    {"id": "files", "label": "FILES", "tool": "list_dir",
     "args": {"path": ""}},          # "" → server apne workspace me bharta hai
    {"id": "scan", "label": "SCAN", "tool": "system_info", "args": {}},
)


def quick_by_id(button_id: str) -> dict:
    """Quick button dhoondho. List ke bahar ka id = None (server par deny)."""
    for row in QUICK_BUTTONS:
        if row["id"] == button_id:
            return row
    return None


def quick_ids() -> tuple:
    return tuple(row["id"] for row in QUICK_BUTTONS)


def hud_theme() -> str:
    """HUD ka theme — `PRABH_HUD_THEME` env se, default `"neon"` (purana).

    Kaam jaan-boojh kar nahi maana jaata: koi bhi adhoora ya adhoori value
    seedhi default par gir jaati hai, warna ek typo se poora HUD ka look badal
    jaata aur user ko samajh hi nahi aata kyun.
    """
    want = os.getenv("PRABH_HUD_THEME", HUD_THEME_DEFAULT).strip().lower()
    return want if want in HUD_THEMES else HUD_THEME_DEFAULT


def weather_text(code) -> str:
    """WMO code ka label. Code na mile to 'Unknown'."""
    try:
        return WEATHER_CODES.get(int(code), "Unknown")
    except (TypeError, ValueError):
        return "Unknown"


def temp_percent(celsius) -> int:
    """-20..50°C ko 0..100% me badlo, gauge ke liye. range se bahar = clamp."""
    try:
        value = float(celsius)
    except (TypeError, ValueError):
        return 0
    span = TEMP_MAX - TEMP_MIN
    pct = (value - TEMP_MIN) * 100.0 / span
    return max(0, min(100, int(round(pct))))
