"""KAAM 6: HUD ka SYSTEM panel kabhi khali na rahe ("--").

**Asli wajah (code padh kar verified):** `ui/hud_stats.js` ka `render()` sirf
WebSocket ke `stats` event par chalti hai (`ui/app.js`). Par:

1. `server/ws_routes.py:35` pump **pehle** `asyncio.sleep(2)` karta hai — yaani
   pehla `stats` event **2 s baad** aata hai. Har load par panel 2+ second
   `"--"` dikhata tha.
2. WS kabhi na chala (token mismatch — `localhost` vs `127.0.0.1` wala purana
   bug) to `"--"` **hamesha** rahta tha.

`server/hud_routes.py:4` ka docstring kehta hai ye endpoint "ek baar load par
bhi chalta hai taaki panel khali na rahe" — par JS usse **kabhi call hi nahi**
karta tha. Ab `ui/app.js` ka `primePanels()` `/hud/stats` ek baar maarta hai.

**Weather alag hai:** `hud_weather.js:76` apne aap `load()` chala raha hai
(15 min interval) — usme koi kami nahi thi, is liye yahan dobara call nahi
kiya gaya.

Ye test **server side** pakadta hai: endpoint 200 deta hai aur cpu/ram
**kabhi `None` nahi** hote (yaani `"--"` data ki kami nahi, call na hone ki
 kami thi). UI ka hissa source-check hai (browser nahi chalaya — Playwright
 is machine par nahi hai, naya package lagana mana tha).

Koi browser nahi, koi asli window nahi, port 8000 par kuch nahi.
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.wakehelp import check, finish

APP_JS = ROOT / "ui" / "app.js"
PRIME_JS = ROOT / "ui" / "hud_prime.js"
STATS_JS = ROOT / "ui" / "hud_stats.js"
WEATHER_JS = ROOT / "ui" / "hud_weather.js"
WS_ROUTES = ROOT / "server" / "ws_routes.py"


class TestStatsEndpoint(unittest.TestCase):
    """`/hud/stats` sach me bhar deta hai? (server side, browser ke bina)"""

    def setUp(self):
        from fastapi.testclient import TestClient

        from server import security
        from server.app import app

        self.client = TestClient(app)
        self.headers = {
            "host": f"localhost:{config.SERVER_PORT}",
            "origin": f"http://localhost:{config.SERVER_PORT}",
            "x-prabh-token": security.token(),
        }

    def test_returns_200_with_fields(self):
        reply = self.client.get("/hud/stats", headers=self.headers)
        check("200", reply.status_code, 200)
        data = reply.json()
        for field in ("cpu", "ram", "battery", "disk", "net"):
            check(f"{field} hai", field in data, True)

    def test_cpu_ram_never_none(self):
        """`--` ka matlab data ki kami nahi — sirf render na hona."""
        from core import sysstats

        data = sysstats.stats(force=True)
        check("cpu number hai", isinstance(data["cpu"], (int, float)), True)
        check("ram number hai", isinstance(data["ram"], int), True)
        check("cpu None nahi", data["cpu"] is None, False)
        check("ram None nahi", data["ram"] is None, False)

    def test_battery_has_plug_fallback(self):
        """Battery na ho to `percent=None` par UI "PLUG" dikhata hai — `--`
        nahi. Yaani batt ka `--` bhi data ki kami nahi hai."""
        from core import sysstats

        bat = sysstats.stats(force=True)["battery"]
        check("battery dict", isinstance(bat, dict), True)
        check("plugged key", "plugged" in bat, True)
        check("percent ya None", bat.get("percent") is None or
              isinstance(bat.get("percent"), int), True)

    def test_needs_token(self):
        """Bina token 401 — is liye JS ko token bhejna zaroori hai."""
        bad = {"host": f"localhost:{config.SERVER_PORT}",
               "origin": f"http://localhost:{config.SERVER_PORT}"}
        check("bina token 401", self.client.get("/hud/stats", headers=bad).status_code,
              401)


class TestLoadPriming(unittest.TestCase):
    """UI ka hissa: load par ek fetch, WS sirf aage ke liye."""

    def test_app_js_calls_stats_on_load(self):
        src = PRIME_JS.read_text(encoding="utf-8")
        check("primePanels hai", "function primePanels()" in src, True)
        check("/hud/stats maarta hai", 'loadOnce("/hud/stats"' in src, True)
        check("token bhejta hai", '"x-prabh-token"' in src, True)
        check("load par chalta hai", "DOMContentLoaded" in src, True)
        check("index.html me script tag",
              "hud_prime.js" in (ROOT / "ui" / "index.html").read_text(
                  encoding="utf-8"), True)

    def test_weather_not_double_fetched(self):
        """Weather apne aap load karta hai — dobara call = bekaar request."""
        weather_src = WEATHER_JS.read_text(encoding="utf-8")
        check("weather khud load karta hai", "load(true);" in weather_src, True)
        both = (APP_JS.read_text(encoding="utf-8") +
                PRIME_JS.read_text(encoding="utf-8"))
        check("kisi me /hud/weather nahi", "/hud/weather" in both, False)

    def test_render_still_driven_by_ws(self):
        """Purana WS raasta bhi chahiye — `primePanels` sirf shuruaat bharta hai."""
        src = APP_JS.read_text(encoding="utf-8")
        check("WS stats render ab bhi hai",
              "if (window.PRABH_STATS) window.PRABH_STATS.render(ev.data);" in src,
              True)

    def test_uses_textcontent_not_innerhtml(self):
        """Suraksha ka pakkaura: dynamic text sirf textContent se."""
        stats = STATS_JS.read_text(encoding="utf-8")
        check("stats me innerHTML nahi", "innerHTML" in stats, False)
        check("stats me textContent hai", "textContent" in stats, True)

    def test_initial_text_is_dash(self):
        """`--` wahi hai jo shuru me likha hai — yani render na hui to dikhta hai."""
        stats = STATS_JS.read_text(encoding="utf-8")
        check('"--" shuru me hai', 'textContent = "--"' in stats, True)
        check("render guard karta hai", "if (!data) return;" in stats, True)

    def test_stats_pump_first_event_is_delayed(self):
        """SABOOT:** pump pehle sota hai, is liye pehla event 2 s baad — yahi
        `--` ki asli galti thi."""
        src = WS_ROUTES.read_text(encoding="utf-8")
        sleep_at = src.index("asyncio.sleep(config.STATS_INTERVAL_SECONDS)")
        publish_at = src.index('HUB.publish({"type": "stats"')
        check("pehle sleep, phir publish", sleep_at < publish_at, True)
        check("interval 2 s", config.STATS_INTERVAL_SECONDS, 2.0)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("HUD stats load par bharta hai" if result.wasSuccessful() else "FAIL")
