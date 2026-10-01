"""OpenAI-compatible adapter — NVIDIA, OpenRouter (aur test ke fake providers).

Ek hi adapter sab OpenAI-style provider chalata hai; naye endpoint nahi.
Groq bhi OpenAI-compatible hai (base_url alag), Gemini nahi — wo apne
client se chalta hai. Yahan sirf raw HTTP + dict, taaki test me easy mock ho.

Fail reasons yahi module decide karta hai:
  - 404 -> 'gone' (session me permanent skip)
  - 429/402/503 -> 'busy' (Retry-After, warna 10 min)
  - billing/credit word -> 'billing' (free-only provider band, nayi key tak)
  - khaali ya finish_reason='length' -> 'empty' (retry, phir agla provider)
  - ghalat JSON -> 'json'
"""

import json
import time
import urllib.error
import urllib.request

from brain import limiter, pool_config
from log_setup import get_logger

log = get_logger("openai_pool")

RETRY_AFTER_HEADERS = ("retry-after", "x-ratelimit-reset", "x-ratelimit-reset-after")
# 402 alag se billing hai, isliye yahan nahi. 500/502/503/429 = busy.
BUSY_CODES = (429, 500, 502, 503)
MAX_RETRY_AFTER = 900


class CallError(Exception):
    """kind: gone | busy | billing | empty | json | auth | other"""

    def __init__(self, kind: str, message: str, retry_after: int = 0):
        super().__init__(message)
        self.kind = kind
        self.retry_after = retry_after


def _retry_after(headers) -> int:
    """Header se Retry-After (seconds). 0 = header nahi."""
    for name in RETRY_AFTER_HEADERS:
        val = headers.get(name) if headers else None
        if not val:
            continue
        try:
            secs = int(float(val))
        except (TypeError, ValueError):
            continue
        if secs > 0:
            return min(secs, MAX_RETRY_AFTER)
    return 0


def _classify_status(code: int, body: str) -> tuple:
    low = (body or "").lower()
    if code == 404:
        return "gone", f"404 model/provider nahi mila"
    if code == 401:
        return "auth", "401 key galat ya missing"
    if code == 402:
        return "billing", f"402 {body[:120]}"
    if any(w in low for w in ("insufficient_credit", "insufficient credit",
                              "credits expired", "payment required", "billing")):
        return "billing", f"billing/credit chahiye: {body[:120]}"
    if code in BUSY_CODES:
        return "busy", f"{code} {body[:120]}"
    return "other", f"{code} {body[:160]}"


def _post(url: str, key: str, payload: dict, headers: dict = None, timeout: float = 30.0,
          method: str = "POST"):
    hdrs = {"Content-Type": "application/json", "Authorization": "Bearer " + key}
    if headers:
        hdrs.update(headers)
    body = json.dumps(payload).encode() if method == "POST" else None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode()), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        kind, msg = _classify_status(exc.code, raw)
        raise CallError(kind, msg, _retry_after(exc.headers)) from exc
    except TimeoutError as exc:
        raise CallError("busy", "timeout") from exc
    except Exception as exc:
        raise CallError("other", f"{type(exc).__name__}: {exc}") from exc


def _extract(data: dict) -> tuple:
    """(content, finish_reason). content empty ho sakta hai — reason 'length'."""
    choices = data.get("choices") or [{}]
    msg = choices[0].get("message") or {}
    content = (msg.get("content") or "").strip()
    finish = choices[0].get("finish_reason") or ""
    return content, finish


def chat(provider: dict, history: list, persona: str, model: str,
         max_tokens: int, temperature: float, reasoning_effort: str = "") -> str:
    """Ek raw chat call. Raise CallError(kind=...)."""
    lim = limiter.get(provider)
    lim.acquire()

    messages = [{"role": "system", "content": persona}] + history
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if reasoning_effort:
        # NVIDIA par ye top-level chahiye — extra_body me bhejne par 400 aata hai.
        payload["reasoning_effort"] = reasoning_effort

    url = provider["base_url"].rstrip("/") + "/chat/completions"
    extra = {}
    if provider["name"] == "openrouter":
        extra = {"HTTP-Referer": "http://localhost", "X-Title": "Prabh"}
    start = time.perf_counter()
    data, _ = _post(url, provider["key"], payload, extra, provider["timeout"])
    took = int((time.perf_counter() - start) * 1000)

    content, finish = _extract(data)
    log.info("TIME %s: %s %dms | %d chars", provider["name"], model, took, len(content))

    if not content:
        if finish == "length":
            raise CallError("empty", f"{model}: token khatam (length), content khaali")
        raise CallError("empty", f"{model}: khaali jawab")

    # Kuch free providers 200 par bhi "payment required" bhej dete hain. Chhota
    # response + billing word = free-only provider ko turant band karna hai.
    if provider["name"] in pool_config.FREE_ONLY:
        word = pool_config.billing_hit(content)
        if word:
            raise CallError("billing", f"{model}: '{word}' — credit/payment chahiye")
    return content


def models_list(provider: dict) -> list:
    """Sirf /models — free, credits nahi lagte. Startup check ke liye. GET, POST nahi."""
    url = provider["base_url"].rstrip("/") + "/models"
    data, _ = _post(url, provider["key"], {}, timeout=provider["timeout"], method="GET")
    return [m.get("id") for m in data.get("data", []) if m.get("id")]