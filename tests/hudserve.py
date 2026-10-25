"""Playwright ke liye nakli HUD server (KAAM A/B dono share karte hain).

SAF rules jo ye file Follow karti hai:
- Sirf `ui/` static files + do nakli JSON endpoint. **Koi brain, koi tool,
  koi asli data nahi.**
- Port **8731** (8700+ ke beech, 8000 KABHI nahi — asli Jarvis ka port hai).
- `import config` **NAHI** karte — is liye test me logsafe ka ordering koi
  sawaal hi nahi banta aur `.env` padha hi nahi jaata.
- `JARVIS_*` placeholder bhari jaati hain, `.env` ki koi key yahan nahi.

Browser sirf is server se baat karta hai; koi asli service nahi.
"""

import http.server
import json
import socket
import threading
from pathlib import Path
from urllib.parse import unquote

UI = Path(__file__).resolve().parent.parent / "ui"

# Nakli system numbers — test sirf shape dekhta hai, asli psutil nahi.
FAKE_STATS = {
    "cpu": 23.4, "ram": 61.2, "disk": 48.0, "cores": 4,
    "net": {"down": 132456.0, "up": 54321.0},
    "battery": {"percent": 88, "plugged": True},
}
FAKE_WEATHER = {
    "ok": True, "temp": 31.4, "condition": "Partly Cloudy",
    "high": 36.0, "low": 24.5, "temp_percent": 73, "hint": "",
}

# `__JARVIS_HUD_THEME__` ka default — **test runner ise bharta hai**
# (`config.hud_theme()` se), taaki nakli server bhi asli default serve kare.
# Yahan hard-code rakhne ka koi fayda nahi: default flip hote hi test asal
# config ke bajaye khayali value check karta, aur asli bug chhoot jaata.
# Neeche `filled_html()` isko PLACEHOLDERS me dhal deta hai.
DEFAULT_THEME = "neon"

PLACEHOLDERS = (
    ("__JARVIS_TOKEN__", "nakli-token"),
    ("__JARVIS_TOOLS_ON__", "1"),
    ("__JARVIS_ASSISTANT_NAME__", "Jarvis"),
    ("__JARVIS_DISPLAY_NAME__", "Jarvis"),
    ("__JARVIS_BRAIN_WARN__", ""),
    # --- KAAM B: arc theme. Rang/number `config_hud.py` ke hain (nakli
    # constants nahi — asli values, taaki test bhi asli config check kar
    # sake). Theme `DEFAULT_THEME` se aata hai, upar dekho. ---
    ("__JARVIS_HUD_THEME__", DEFAULT_THEME),
    ("__ARC_ACCENT__", "#ff8a2e"),
    ("__ARC_ACCENT_2__", "#ff5e3a"),
    ("__ARC_ROUTING__", '["WAKE", "STT", "BRAIN", "TTS"]'),
    ("__ARC_CHANNEL__", '"LOCAL"'),
    ("__ARC_CREDIT__", '"Interface style inspired by Mukh.1"'),
    ("__ARC_TICKS__", "72"),
    ("__ARC_HEX__", "6"),
    ("__ARC_ACT_MAX__", "6"),
    ("__ARC_TYPE_MS__", "28"),
    ("__ARC_FRAME_MS__", "33"),
)

CSS = "text/css"
JS = "application/javascript"

# Sirf ye do theme — `server/app.py` ke `resolve_theme()` ka wahi whitelist.
THEMES = ("neon", "arc")


def filled_html(theme: str = "") -> str:
    """index.html + placeholder bhari. `theme` dene par `?theme=` set hota hai.

    `DEFAULT_THEME` **call time** par padha jaata hai, import par nahi — test
    runner usse yahin set karta hai (`config.hud_theme()`).
    """
    html = (UI / "index.html").read_text(encoding="utf-8")
    for name, value in PLACEHOLDERS:
        if name == "__JARVIS_HUD_THEME__":
            value = theme or DEFAULT_THEME
        html = html.replace(name, value)
    return html


def _ctype(suffix: str) -> str:
    return {".css": CSS, ".js": JS, ".html": "text/html; charset=utf-8",
            ".woff2": "font/woff2"}.get(suffix, "application/octet-stream")


class Handler(http.server.SimpleHTTPRequestHandler):
    """Sirf GET. WebSocket `/ws` jaan-boojh kar 404 — test us par depend nahi."""

    # HTTP/1.1 + Content-Length (har response me hai) taaki browser ek hi
    # connection par saare 20+ scripts/woff2 le sake. `ThreadingHTTPServer` ke
    # saath ye zaroori hai — warna Chromium ke parallel connections beech me
    # kat jaate hain aur app.js ko `tools.js`/`hud_status.js` chhoot jaata
    # hai ("ToolsPanel is not defined" — alag alag baar bhi alag error).
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):        # noqa: D102 - console spam band
        pass

    def _send(self, body, ctype: str) -> None:
        raw = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):                    # noqa: N802 - stdlib ka naam
        path, _, query = self.path.partition("?")
        if path == "/":
            # `?theme=arc` — asli server jaisa (`server/app.py` ka
            # `resolve_theme`: lowercase + whitelist). Test yahi rule maangta
            # hai, is liye nakli server bhi WAHI kare — warna test asli
            # server se alag behave karega.
            theme = ""
            for part in query.split("&"):
                if part.startswith("theme="):
                    theme = unquote(part[6:]).strip().lower()
                    if theme not in THEMES:
                        theme = ""
            return self._send(self._index(theme), "text/html; charset=utf-8")
        if path == "/hud/stats":
            return self._send(json.dumps(FAKE_STATS), "application/json")
        if path == "/hud/weather":
            return self._send(json.dumps(FAKE_WEATHER), "application/json")
        if path.startswith("/ui/"):
            f = UI / path[4:]
            if f.is_file():
                return self._send(f.read_bytes(), _ctype(f.suffix))
        self.send_error(404)

    def _index(self, theme: str = "") -> bytes:
        return filled_html(theme).encode("utf-8")


def free_port(start: int = 8731) -> int:
    """Port khud dhundho — do test ek saath chale to bhi na toke."""
    for port in range(start, start + 40):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
        return port
    raise RuntimeError("khula port nahi mila")


class Server(http.server.ThreadingHTTPServer):
    """Har connection apne thread me — Chromium ek saath kai file maangta hai."""


class FakeHud:
    """`with FakeHud() as hud:` — background me chalta hai, baad me band.

    `theme="neon"` ya `"arc"` dene par usi theme ko **pin** kar deta hai
    (chahe asli default kuch bhi ho), aur `__exit__` par wapas asli default.
    Ye zaroori hai: ek test jo neele HUD ke selectors check karta hai, use
    saaf-saaf `neon` pin karna chahiye — warna default flip karte hi wo
    chup-chaap "sab theek" bolne lagta hai jabki uske saare selectors maujood
    hi nahi rahte. Ye wahi galti hai jo Phase 4 me 8 baar hui thi.
    """

    def __init__(self, port=None, theme: str = ""):
        self.port = port or free_port()
        self.url = f"http://127.0.0.1:{self.port}/"
        self._httpd = None
        self.theme = theme
        self._prev_theme = None

    def __enter__(self):
        if self.theme:
            self._prev_theme = DEFAULT_THEME
            globals()["DEFAULT_THEME"] = self.theme
        Server.allow_reuse_address = True
        self._httpd = Server(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self.theme and self._prev_theme is not None:
            globals()["DEFAULT_THEME"] = self._prev_theme
        return False