"""Model probe — strict JSON + latency naapna, 24 ghante cache.

Startup par probe NAHI chalta (credits bachane ke liye). Sirf tab jab user khud
`brain.probe.run()` chalaaye. Result JSON file me cache hota hai; 24 ghante me
dobara call nahi hota.

Rules:
- Har candidate par MAX_CALLS (2) se zyada call nahi.
- Latency limit (8s) cross kare to model Tier 2 me hi rehne layak hai.
- JSON probe pass + latency limit = hi model apnaaya jayega.
"""

import json
import time
from pathlib import Path

import config
from brain import openai_pool, pool_config
from log_setup import get_logger

log = get_logger("probe")

CACHE_FILE = config.LOG_DIR / "probe_cache.json"
CACHE_TTL = 24 * 3600          # 24 ghante
MAX_CALLS = 2                  # har model par
LATENCY_LIMIT_MS = 8000        # isse upar = sirf Tier 2 reserve

PROBE_MSG = 'Reply with ONLY this JSON, nothing around it: {"text":"namaste","n":7,"ok":true}'
EXPECT = (("text", str), ("n", int), ("ok", bool))


def strict_json(text: str) -> tuple:
    """(pass, reason). Model ka free-form answer strict JSON banega ya nahi."""
    text = (text or "").strip()
    if not text:
        return False, "khaali content"
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return False, "JSON braces nahi mile"
    try:
        data = json.loads(text[start:end + 1])
    except Exception as exc:
        return False, f"JSON parse nahi hua: {exc}"
    if not isinstance(data, dict):
        return False, "JSON object nahi hai"
    for key, typ in EXPECT:
        if key not in data:
            return False, f"{key} missing"
        if typ is bool:
            if not isinstance(data[key], bool):
                return False, f"{key} galat type"
        elif isinstance(data[key], bool) or not isinstance(data[key], typ):
            return False, f"{key} galat type"
    return True, "ok"


def probe_model(provider: dict, model: str, calls: int = MAX_CALLS) -> dict:
    """Ek model par `calls` tak try. {'ok','latency_ms','reason','calls'}"""
    best_ms, reason, used, total = None, "", 0, 0
    for _ in range(calls):
        used += 1
        start = time.monotonic()
        try:
            text = openai_pool.chat(
                provider, [{"role": "user", "content": PROBE_MSG}], "probe",
                model, max_tokens=pool_config.MAX_TOKENS, temperature=0,
                reasoning_effort=pool_config.REASONING_EFFORT)
        except openai_pool.CallError as exc:
            reason = f"{exc.kind}: {exc}"
            total += int((time.monotonic() - start) * 1000)
            continue
        total = int((time.monotonic() - start) * 1000)
        passed, why = strict_json(text)
        if passed and (best_ms is None or total < best_ms):
            best_ms = total
        if not reason:
            reason = why
    return {
        "model": model,
        "ok": best_ms is not None,
        "latency_ms": best_ms,
        "reason": reason or "ok",
        "calls": used,
    }


def run(provider_name: str = "nvidia", limit: int = 3, force: bool = False) -> dict:
    """Provider ke preferred models probe karo (top `limit`). Cache 24 ghante."""
    cache = _load()
    key = provider_name
    if not force and _fresh(cache.get(key)):
        log.info("probe: %s ka cache %s tak sahi hai, call nahi kiya", provider_name, CACHE_TTL)
        return cache[key]

    provider = pool_config.by_name().get(provider_name)
    if not provider:
        return {"error": f"provider {provider_name} pool me nahi"}
    if not provider["key"]:
        return {"error": f"{provider_name} ki key nahi hai"}

    rows = []
    for model in provider["models"][:limit]:
        row = probe_model(provider, model)
        rows.append(row)
        log.info("probe %s: ok=%s %sms %s", model, row["ok"], row["latency_ms"], row["reason"])

    winner = _pick(rows)
    result = {
        "provider": provider_name,
        "ts": time.time(),
        "rows": rows,
        "winner": winner,
        "note": "NVIDIA credits 1000 — har probe call credit kharch karta hai",
    }
    cache[key] = result
    _save(cache)
    return result


def _pick(rows: list) -> dict:
    """Sirf wahi model jo JSON pass + latency limit me ho.

    `latency_ms is not None` — 0 bhi valid hai (local test), `if row[...]`
    se 0 falsy ho jata.
    """
    for row in rows:
        if not row.get("ok"):
            continue
        ms = row.get("latency_ms")
        if ms is not None and ms < LATENCY_LIMIT_MS:
            return {"model": row["model"], "latency_ms": ms}
    return {}


def _load() -> dict:
    try:
        return json.loads(Path(CACHE_FILE).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(cache: dict) -> None:
    try:
        Path(CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(CACHE_FILE).write_text(json.dumps(cache, indent=2), encoding="utf-8")
    except Exception as exc:
        log.warning("probe cache likh nahi paya: %s", exc)


def _fresh(entry) -> bool:
    if not isinstance(entry, dict) or "ts" not in entry:
        return False
    return (time.time() - entry["ts"]) < CACHE_TTL


def main(argv: list) -> int:
    """`python -m brain.probe [provider] [--limit N] [--force]`"""
    args = [a for a in argv if not a.startswith("-")]
    flags = {a for a in argv if a.startswith("-")}
    provider = args[0] if args else "nvidia"
    limit = 3
    for i, a in enumerate(argv):
        if a == "--limit" and i + 1 < len(argv):
            limit = int(argv[i + 1])
    log.warning("PROBE chalu: %s, %d model, force=%s (credits lag sakte hain)",
                provider, limit, "--force" in flags)
    print(json.dumps(run(provider, limit=limit, force="--force" in flags),
                     indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))