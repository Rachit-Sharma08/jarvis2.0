"""Weather sirf SERVER se. Browser kabhi bahar site ko call nahi karega.

Open-Meteo: bina API key, `current` + `daily` ek hi request me. Har 15 minute
me ek hi call (cache) — warna har refresh me bahar jaakar rate limit kha jayega.

Har value UI ko bhejne se pehle `gatekeeper.audit.mask()` se guzarti hai, kyunki
browser tak jaate hue raaste me wo rule AGENTS.md me hai (koi secret field nahi,
par masked jaana hi hai). Koi key is file me nahi hai, to risk kam hai — par
niyam badalta nahi.
"""

import threading
import time

import httpx

import config
from gatekeeper import audit
from log_setup import get_logger

log = get_logger("weather")

_lock = threading.Lock()
_cache = {"at": 0.0, "data": None}

EMPTY = {
    "ok": False,
    "city": config.WEATHER_CITY,
    "temp": None,
    "humidity": None,
    "wind": None,
    "condition": "No data",
    "code": None,
    "high": None,
    "low": None,
    "temp_percent": 0,
}


def _num(value):
    """Open-Meteo ka number -> float, ya None. String/NAN ko nahi chhodte."""
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return None if out != out else out      # NaN check


def _parse(payload: dict) -> dict:
    """Open-Meteo ka JSON → UI ka shape. Field na mile to EMPTY."""
    current = payload.get("current") or {}
    daily = payload.get("daily") or {}

    def daily_at(key):
        row = daily.get(key) or []
        return _num(row[0]) if row else None

    temp = _num(current.get("temperature_2m"))
    return {
        "ok": temp is not None,
        "city": config.WEATHER_CITY,
        "temp": None if temp is None else round(temp, 1),
        "humidity": _num(current.get("relative_humidity_2m")),
        "wind": _num(current.get("wind_speed_10m")),
        "code": current.get("weather_code"),
        "condition": config.weather_text(current.get("weather_code")),
        "high": daily_at("temperature_2m_max"),
        "low": daily_at("temperature_2m_min"),
        "temp_percent": config.temp_percent(temp),
    }


def _fetch() -> dict:
    try:
        reply = httpx.get(
            config.WEATHER_URL,
            timeout=config.WEATHER_TIMEOUT_SECONDS,
            headers={"Accept": "application/json"},
        )
        reply.raise_for_status()
        data = _parse(reply.json())
    except Exception as exc:
        log.warning("weather fail: %s: %s", type(exc).__name__, exc)
        return dict(EMPTY)
    log.info("weather: %s %s°C", data["condition"], data["temp"])
    return data


def current(force: bool = False) -> dict:
    """Cache ke saath weather. force=True → nayi call (test ke liye).
    Fail par EMPTY wapas aata hai, exception kabhi nahi uthata."""
    now = time.monotonic()
    with _lock:
        fresh = _cache["data"] is not None and (now - _cache["at"]) < config.WEATHER_CACHE_SECONDS
        if fresh and not force:
            return _cache["data"]
        data = _fetch()
        _cache["at"] = now
        _cache["data"] = data
        return data


def _mask_all(data: dict) -> dict:
    """UI tak jane se pehle har text value mask. Naam wale field (city) bhi."""
    return {k: (audit.mask(v) if isinstance(v, str) else v) for k, v in data.items()}


def for_ui(force: bool = False) -> dict:
    """Browser ke liye masked copy. Route yahi call karega."""
    return _mask_all(current(force))


def reset() -> None:
    """Test ke liye."""
    with _lock:
        _cache["at"] = 0.0
        _cache["data"] = None
