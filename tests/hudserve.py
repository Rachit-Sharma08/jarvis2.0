"""Playwright ke liye nakli HUD server (KAAM A/B dono share karte hain).

SAF rules jo ye file Follow karti hai:
- Sirf `ui/` static files + do nakli JSON endpoint. **Koi brain, koi tool,
  koi asli data nahi.**
- Port **8731** (8700+ ke beech, 8000 KABHI nahi — asli Jarvis ka port hai).
- `import config` **NAHI** karte — is liye test me logsafe ka ordering koi
  sawaal hi nahi banta aur `.env` padha hi nahi jaata.
- `PRABH_*` placeholder bhari jaati hain, `.env` ki koi key yahan nahi.

Browser sirf is server se baat karta hai; koi asli service nahi.
"""

import http.server
import json
import socket
import threading
from pathlib import Path

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

PLACEHOLDERS = (
    ("__PRABH_TOKEN__", "nakli-token"),
    ("__PRABH_TOOLS_ON__", "1"),
    ("__PRABH_ASSISTANT_NAME__", "Jarvis"),
    ("__PRABH_DISPLAY_NAME__", "Jarvis"),
    ("__PRABH_BRAIN_WARN__", ""),
)

CSS = "text/css"
JS = "application/javascript"


def filled_html() -> str:
    """index.html + placeholder bhari. `__PRABH_HUD_THEME__` bhi (KAAM B)."""
    html = (UI / "index.html").read_text(encoding="utf-8")
    for name, value in PLACEHOLDERS:
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
        path = self.path.split("?")[0]
        if path == "/":
            return self._send(self._index(), "text/html; charset=utf-8")
        if path == "/hud/stats":
            return self._send(json.dumps(FAKE_STATS), "application/json")
        if path == "/hud/weather":
            return self._send(json.dumps(FAKE_WEATHER), "application/json")
        if path.startswith("/ui/"):
            f = UI / path[4:]
            if f.is_file():
                return self._send(f.read_bytes(), _ctype(f.suffix))
        self.send_error(404)

    def _index(self) -> bytes:
        return filled_html().encode("utf-8")


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
    """`with FakeHud() as hud:` — background me chalta hai, baad me band."""

    def __init__(self, port=None):
        self.port = port or free_port()
        self.url = f"http://127.0.0.1:{self.port}/"
        self._httpd = None

    def __enter__(self):
        Server.allow_reuse_address = True
        self._httpd = Server(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
        return False