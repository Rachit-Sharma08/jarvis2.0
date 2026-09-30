"""Brain doctor: kaunsa model/provider abhi use karna safe hai.

- 404 model_not_found = model hata diya gaya. Poore session me dobara try nahi.
- 402/429/503 = abhi quota/load issue. 10 min skip karke baad me try.
- Dono ka ek hi source: brain/health.py — router, startup check aur UI yahi padhte hain.
"""

import re
import time

import config
from log_setup import get_logger

log = get_logger("health")

GONE = {}      # model -> reason ("hata diya gaya")
UNTIL = {}     # provider -> monotonic deadline
LAST = {}      # provider -> last error (UI message ke liye)

# Status codes word-boundary se. Bina boundary "4299" (voice id me) bhi 429 ban jata.
CODE_RE = re.compile(r"\b(402|429|503)\b")
GONE_MARKERS = ("model_not_found", "does not exist", "no longer available", "not found for api version")
BUSY_WORDS = ("payment_required", "rate limit", "rate_limit", "resource_exhausted",
              "unavailable", "overloaded", "quota")


def classify(exc: Exception) -> str:
    """Error ka category: 'gone' (permanent), 'busy' (10 min rest) ya 'other'."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(marker in text for marker in GONE_MARKERS):
        return "gone"
    if CODE_RE.search(text) or any(word in text for word in BUSY_WORDS):
        return "busy"
    return "other"


def is_503(exc: Exception) -> bool:
    """Sirf 503 (overloaded) par retry — 429/402 par retry bekaar hai."""
    return bool(re.search(r"\b503\b", f"{type(exc).__name__}: {exc}"))


def model_gone(provider: str, model: str, reason: str) -> None:
    GONE[model] = f"{reason}"
    log.warning("model %s hata diya gaya (%s) — is session me dobara try nahi hoga", model, provider)


def skip(provider: str, reason: str, seconds: int = None) -> None:
    rest = seconds or config.PROVIDER_SKIP_SECONDS
    UNTIL[provider] = time.monotonic() + rest
    LAST[provider] = reason
    log.warning("%s ko %ds ka rest diya — %s", provider, rest, reason)


def blocked_reason(provider: str) -> str:
    """Khali = abhi chal sakta hai. Nahi to chhodne ka karan (log + UI dono ke liye)."""
    until = UNTIL.get(provider)
    if not until:
        return ""
    if time.monotonic() < until:
        return f"{provider} {int(until - time.monotonic())}s ke liye rest par"
    UNTIL.pop(provider, None)
    return ""


def classify_and_skip(provider: str, reason: str) -> str:
    """TTS fail me bhi wahi rule: 402/429/503 par 10 min rest, warna chhod do."""
    kind = classify(reason)
    if kind == "busy":
        skip(provider, reason)
    return kind


def warnings() -> list:
    """Startup log aur UI banner ke liye ek line per problem."""
    out = [f"model {model} hata diya gaya" for model in GONE]
    for provider, until in UNTIL.items():
        left = int(max(0, until - time.monotonic()))
        if left:
            out.append(f"{provider} {left}s rest par")
    return out
