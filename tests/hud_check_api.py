"""Phase 4 HUD — server side ke checks (mock + endpoint security).

Yahan asli app chalti hai (`TestClient`), lekin:
- weather ka network call mock hota hai
- stats ka data `psutil` se aata hai (koi network nahi)
- koi brain call nahi, koi asli tool nahi

Do naye checks is file me:
- `/hud/quick` ka model sirf `id` maane (extra field 422)
- ek hi shared Engine — /chat, /ws, /hud/quick teono ka mode/state

Same-origin GET ka rule alag file `hud_check_get.py` me hai (wo lamba hai).
"""

from pathlib import Path

import config
from hud_common import GOOD_HOST, GOOD_ORIGIN, check, headers, read
from core import sysstats
from gatekeeper import keeper
from server import security, weather


# ---------------------------------------------------------------- WEATHER
def test_weather_mock():
    print("WEATHER (mock)")
    payload = {
        "current": {"temperature_2m": 31.4, "relative_humidity_2m": 55,
                    "weather_code": 2, "wind_speed_10m": 8.1},
        "daily": {"temperature_2m_max": [36.0], "temperature_2m_min": [24.5]},
    }
    parsed = weather._parse(payload)
    check("temp parse", parsed["temp"], 31.4)
    check("condition label", parsed["condition"], "Partly Cloudy")
    check("high", parsed["high"], 36.0)
    check("low", parsed["low"], 24.5)
    check("ok True", parsed["ok"], True)
    check("temp_percent", parsed["temp_percent"], config.temp_percent(31.4))

    # khaali/galat payload par crash nahi
    for bad in ({}, {"current": {}}, {"current": None, "daily": None},
                {"current": {"temperature_2m": "abc"}},
                {"current": {"temperature_2m": None}}):
        out = weather._parse(bad)
        check(f"khaali payload safe {bad}", out["ok"] is False, True)
    check("shape EMPTY se match", set(parsed) == set(weather.EMPTY), True)

    # weather fetch fail par EMPTY (cache route par)
    weather.reset()
    real = weather._fetch
    weather._fetch = lambda: dict(weather.EMPTY)
    try:
        got = weather.for_ui(force=True)
    finally:
        weather._fetch = real
        weather.reset()
    check("fetch fail par ok False", got["ok"], False)
    check("no data label", got["condition"], "No data")

    # UI: browser bahar call na kare
    wjs = read("hud_weather.js")
    check("browser sirf /hud/weather", '"/hud/weather"' in wjs, True)
    check("UI me open-meteo URL nahi", "open-meteo" in wjs, False)
    check("no data hint", "No data" in wjs, True)


# ---------------------------------------------------------------- STATS
def test_stats_mock():
    print("STATS (mock)")
    sysstats.reset()
    first = sysstats.stats(force=True)
    for key in ("cpu", "ram", "disk", "battery", "net", "cores"):
        check(f"stats me {key}", key in first, True)
    check("cpu 0..100", 0 <= first["cpu"] <= 100, True)
    check("ram 0..100", 0 <= first["ram"] <= 100, True)
    check("disk 0..100", 0 <= first["disk"] <= 100, True)
    check("net keys", sorted(first["net"]), ["down", "up"])
    check("battery keys", sorted(first["battery"]), ["percent", "plugged"])

    # cache: do call me wahi object
    check("cache wapas deta hai", sysstats.stats() is sysstats.stats(), True)
    sysstats.reset()
    check("reset ke baad naya", sysstats._cache["data"] is None, True)
    check("battery dict", isinstance(sysstats._battery(), dict), True)

    # prime() ke baad cpu 0 nahi aata
    sysstats.prime()
    sysstats.reset()
    sysstats.stats(force=True)
    sysstats.reset()


# ---------------------------------------------------------------- SECURITY
def test_endpoints_security(client):
    print("HUD ENDPOINT SECURITY")
    token = security.token()
    ok = headers(token)

    check("/hud/stats bina token", client.get("/hud/stats", headers={"host": GOOD_HOST, "origin": GOOD_ORIGIN}).status_code, 401)
    check("/hud/weather bina token", client.get("/hud/weather", headers={"host": GOOD_HOST, "origin": GOOD_ORIGIN}).status_code, 401)
    check("/hud/stats fake host", client.get("/hud/stats", headers={**ok, "host": "evil.com"}).status_code, 400)
    check("/hud/weather bad origin", client.get("/hud/weather", headers={**ok, "origin": "https://evil.com"}).status_code, 403)
    check("/hud/quick bina token", client.post("/hud/quick", json={"id": "scan"}, headers={"host": GOOD_HOST, "origin": GOOD_ORIGIN}).status_code, 401)
    check("/hud/quick bad origin", client.post("/hud/quick", json={"id": "scan"}, headers={**ok, "origin": "https://evil.com"}).status_code, 403)
    check("/hud/quick fake host", client.post("/hud/quick", json={"id": "scan"}, headers={**ok, "host": "evil.com"}).status_code, 400)
    check("/hud/quick galat id", client.post("/hud/quick", json={"id": "rm_rf"}, headers=ok).status_code, 404)

    # khali/extra arg reject (UI se sirf id aata hai)
    check("extra field reject", client.post("/hud/quick", json={"id": "scan", "tool": "run_command"}, headers=ok).status_code, 422)
    check("args field reject", client.post("/hud/quick", json={"id": "scan", "args": {"command": "del"}}, headers=ok).status_code, 422)

    # sab par CSP + nosniff
    for path in ("/hud/stats", "/hud/weather"):
        resp = client.get(path, headers=ok)
        check(f"{path} CSP", "default-src 'self'" in resp.headers.get("content-security-policy", ""), True)
        check(f"{path} nosniff", resp.headers.get("x-content-type-options"), "nosniff")

    # /hud/quick mask: response me koi key nahi
    body = client.post("/hud/quick", json={"id": "scan"}, headers=ok).text.lower()
    for bad in ("apikey", "api_key", "secret", "password", "gsk_", "nvapi"):
        check(f"quick response me {bad} nahi", bad in body, False)


# ---------------------------------------------------------------- QUICK + GATEKEEPER
def test_quick_goes_through_gatekeeper(client):
    print("QUICK BUTTON → GATEKEEPER (no bypass)")
    token = security.token()
    ok = headers(token)

    # config ka quick list: sirf 6, sab allowed tool
    check("6 quick button", len(config.QUICK_BUTTONS), 6)
    for button in config.QUICK_BUTTONS:
        check(f"{button['id']} allowed tool", button["tool"] in __import__("tools").TOOLS, True)
        check(f"{button['id']} risk chhota (SAFE/ASK)",
              config.TOOL_BASE_RISK[button["tool"]] in (config.SAFE, config.ASK), True)

    # server args UI se nahi leta
    src = (Path(config.BASE_DIR) / "server" / "hud_routes.py").read_text(encoding="utf-8")
    check("args config se", 'args = dict(button["args"])' in src, True)
    check("engine.run_tool use hua", "run_tool" in src, True)
    check("direct execute() nahi", "tools.execute" in src, False)
    check("keeper.review direct nahi", "keeper.review" in src, False)

    # quick click par UI sirf id bhejti hai
    qjs = read("hud_quick.js")
    check("UI sirf id bhejti hai", 'JSON.stringify({ id: id })' in qjs, True)
    check("UI koi tool args nahi bhejti", "run_command" not in qjs, True)
    check("isTrusted check", "isTrusted" in qjs, True)

    # TOOLS OFF: server par DENY, UI par disabled
    keeper.set_tools(False)
    try:
        used_before = keeper.LIMITER.used()
        client.post("/hud/quick", json={"id": "scan"}, headers=ok)
        check("TOOLS OFF par call count nahi badha", keeper.LIMITER.used(), used_before)
        check("tools abhi bhi OFF", keeper.tools_on(), False)
        check("UI button disable logic", "setTools" in qjs and "btn.disabled" in qjs, True)
        check("TOOLS OFF text", "TOOLS OFF" in read("tools.js"), True)
    finally:
        keeper.set_tools(False)

    # tools toggle UI ke kill switch se (purana rasta)
    reply = client.post("/tools/toggle", json={"on": True}, headers=ok)
    check("toggle ON", reply.json()["tools_on"], True)
    client.post("/tools/toggle", json={"on": False}, headers=ok)
    check("toggle OFF", keeper.tools_on(), False)


# ---------------------------------------------------------------- SHARED ENGINE
def test_one_shared_engine():
    """/chat, /ws aur /hud/quick ka Engine ek hi hona chahiye.

    Alag-alag Engine ho to mode switch ek jagah lagta hai aur quick button
    doosri jagah se chalta hai (user ko lagta hai bug hai).
    """
    print("SHARED ENGINE (ek hi instance)")
    from server.state import engine as shared
    import server.app as app_mod
    import server.hud_routes as hud_mod
    import server.ws_routes as ws_mod

    check("app aur state same", app_mod.engine is shared(), True)
    check("hud_routes shared use karta hai",
          "shared_engine()" in (Path(config.BASE_DIR) / "server" / "hud_routes.py").read_text(encoding="utf-8"), True)
    check("ws_routes shared use karta hai",
          "shared_engine()" in (Path(config.BASE_DIR) / "server" / "ws_routes.py").read_text(encoding="utf-8"), True)
    check("koi stray Engine() nahi bana", ws_mod.__dict__.get("engine") is None, True)
    check("hud me bhi stray Engine() nahi", hud_mod.__dict__.get("engine") is None, True)


def run(client):
    test_weather_mock()
    test_stats_mock()
    test_endpoints_security(client)
    test_quick_goes_through_gatekeeper(client)
    test_one_shared_engine()