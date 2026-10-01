"""PC ke live stats — HUD ke SYSTEM panel ke liye. Sirf padhna hai, kuch badalta nahi.

psutil se CPU / RAM / battery / disk / network. Har call par naya sample nahi —
`STATS_CACHE_SECONDS` ke andar purana wapas de dete hain, warna 2 second me
sirf 1 hit par poori CPU peegi padhni padti.

Not: network MB/s ke liye do sample ka farak chahiye, isliye last reading
alag se yaad rakhte hain. Battery nahi ho (desktop) to `None` — UI "PLUGGED"
dikhayega.
"""

import threading
import time

import psutil

import config

_lock = threading.Lock()
_cache = {"at": 0.0, "data": None}
_prev_net = None      # (time, bytes_sent, bytes_recv)


def _cpu_percent() -> float:
    """interval=None → pichle call ke baad ka CPU %. Pehle call 0 deta hai,
    isliye `prime()` startup par chala lo."""
    return round(psutil.cpu_percent(interval=None), 1)


def _battery() -> dict:
    """{'percent': int, 'plugged': bool}. Battery na ho to plugged=True."""
    try:
        raw = psutil.sensors_battery()
    except Exception:
        return {"percent": None, "plugged": True}
    if raw is None:
        return {"percent": None, "plugged": True}
    return {
        "percent": max(0, min(100, int(raw.percent))),
        "plugged": bool(raw.power_plugged),
    }


def _disk_percent() -> int:
    try:
        return int(psutil.disk_usage(str(config.BASE_DIR)).percent)
    except Exception:
        return 0


def _net_mb() -> dict:
    """Is sample ka (sent+recv) MB/s. Pehli baar 0 — do sample chahiye hote hain."""
    global _prev_net
    now = time.monotonic()
    io = psutil.net_io_counters()
    sent, recv = io.bytes_sent, io.bytes_recv
    result = {"down": 0.0, "up": 0.0}
    if _prev_net is not None:
        gap = now - _prev_net[0]
        if gap > 0.2:      # 0.2s se chhota gap = network jump dekhne layak nahi
            result["down"] = round(max(0, recv - _prev_net[2]) / config.NET_MB / gap, 2)
            result["up"] = round(max(0, sent - _prev_net[1]) / config.NET_MB / gap, 2)
    _prev_net = (now, sent, recv)
    return result


def _sample() -> dict:
    mem = psutil.virtual_memory()
    net = _net_mb()
    return {
        "cpu": _cpu_percent(),
        "ram": int(mem.percent),
        "ram_used_gb": round(mem.used / config.NET_MB / 1024, 1),
        "ram_total_gb": round(mem.total / config.NET_MB / 1024, 1),
        "battery": _battery(),
        "disk": _disk_percent(),
        "net": net,
        "cores": psutil.cpu_count() or 1,
    }


def prime() -> None:
    """Startup par chalao — CPU ka pehla interval=None sample 0 deta hai.
    Isse pehla asli number 2 second baad sahi aata hai."""
    psutil.cpu_percent(interval=None)
    _net_mb()


def stats(force: bool = False) -> dict:
    """Latest stats, cache ke saath. UI ko sirf yahi chahiye.
    force=True → cache chhod kar naya sample (test ke liye)."""
    now = time.monotonic()
    with _lock:
        fresh = _cache["data"] is not None and (now - _cache["at"]) < config.STATS_CACHE_SECONDS
        if fresh and not force:
            return _cache["data"]
        data = _sample()
        _cache["at"] = now
        _cache["data"] = data
        return data


def reset() -> None:
    """Test ke liye. Server restart par bhi naya hota hai."""
    global _prev_net
    with _lock:
        _cache["at"] = 0.0
        _cache["data"] = None
        _prev_net = None
