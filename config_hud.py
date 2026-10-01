"""HUD (Phase 4) ke settings. Ek file, ek kaam — sirf constants aur helpers.

Ye `config.py` me re-export hote hain, isliye baaki code ko `config.WEATHER_CITY`
jaisa hi likhna hai. Is file me koi logic nahi, sirf values aur chhote helpers.

Rules: yahan koi API key nahi. Weather ke liye key chahiye hi nahi (Open-Meteo).
"""

# ---- Colors: reference photo + spec dono se ----
# Photo washed-out thi, isliye saturation thodi barh kar diya. Exact value
# design/reference.png ke grid analysis se aayi hai.
CYAN = "#2ea8ff"
CYAN_BRIGHT = "#4cc3ff"
CYAN_DIM = "#1c5f9e"
AMBER = "#f5a623"

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
