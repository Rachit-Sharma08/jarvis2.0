"""Brain/TTS doctor: kaunsa provider abhi use karna safe hai.

Categories:
  - gone    -> 404. Model hata diya gaya. Poore session me dobara try nahi.
  - busy    -> 429/402/503/timeout. Cooldown: Retry-After header, warna 10 min.
  - billing -> payment/credit word ya 402. DIN BHAR BAND (agle 00:00 tak).
  - auth    -> 401. Key galat/missing. Session me band.
  - empty   -> khaali jawab. Chhota rest (45s) — agli request me phir chance.
  - other   -> baaki sab. 10 min rest.

Ek hi source — brain/pool.py, brain/checkup.py, voice/tts.py aur /brain/status
sab yahi padhte hain. Do jagah cooldown mat likho.
"""

import datetime
import re
import time

import config
from log_setup import get_logger

log = get_logger("health")

GONE = {}       # model -> reason (permanent, is session me)
UNTIL = {}      # provider -> monotonic deadline
LAST = {}       # provider -> last fail ka chhota reason
NEXT_DAY = {}   # provider -> (deadline, reason) — agle 00:00 tak
HUMAN = {}      # provider -> "12 min baad" jaisa text

DEFAULT_COOLDOWN = 600     # 10 min
EMPTY_COOLDOWN = 45        # khaali jawab — jaldi phir try

# Word-boundary se. Bina boundary "4299" (voice id me) bhi 429 ban jata.
CODE_RE = re.compile(r"\b(402|429|503|500|502)\b")
GONE_MARKERS = ("model_not_found", "does not exist", "no longer available",
                "not found for api version", "model not found")
BUSY_WORDS = ("payment_required", "rate limit", "rate_limit", "resource_exhausted",
              "unavailable", "overloaded", "quota")
BILLING_WORDS = ("insufficient_credit", "insufficient credit", "insufficient credits",
                 "insufficient funds", "credits expired", "cloud credits",
                 "payment required", "add credits", "credit balance is too low",
                 "billing", "paid_plan", "upgrade your plan")


def classify(exc) -> str:
    """Groq/Gemini SDK ya TTS exception -> category."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(m in text for m in GONE_MARKERS):
        return "gone"
    if any(w in text for w in BILLING_WORDS):
        return "billing"
    if CODE_RE.search(text) or any(w in text for w in BUSY_WORDS):
        return "busy"
    if "khaali" in text or "empty" in text:
        return "empty"
    return "other"


def is_503(exc) -> bool:
    """Sirf 503 (overloaded) par retry — 429/402 par retry bekaar hai."""
    return bool(re.search(r"\b503\b", f"{type(exc).__name__}: {exc}"))


def _human(seconds: float) -> str:
    if seconds >= 3600:
        return f"{round(seconds / 3600, 1)} ghante baad"
    if seconds >= 60:
        return f"{round(seconds / 60)} min baad"
    return f"{int(seconds)}s baad"


def _midnight() -> float:
    """Agle local 00:00 ka monotonic deadline."""
    now = datetime.datetime.now()
    tomorrow = (now + datetime.timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return time.monotonic() + max(1.0, (tomorrow - now).total_seconds())


def model_gone(provider: str, model: str, reason: str) -> None:
    GONE[model] = f"{reason}"
    log.warning("model %s hata diya gaya (%s) — is session me dobara try nahi", model, provider)


def skip(provider: str, reason: str, seconds: int = None) -> None:
    rest = seconds if seconds else DEFAULT_COOLDOWN
    UNTIL[provider] = time.monotonic() + rest
    LAST[provider] = " ".join(str(reason).split())[:200]
    HUMAN[provider] = _human(rest)
    log.warning("%s ko %ds ka rest — %s", provider, rest, reason)


def till_next_day(provider: str, reason: str) -> None:
    """Din ki limit (billing/credit khatam). Agle 00:00 tak band."""
    NEXT_DAY[provider] = (_midnight(), " ".join(str(reason).split())[:200])
    LAST[provider] = NEXT_DAY[provider][1]
    HUMAN[provider] = "agle din tak (credits/payment)"
    log.error("%s BAND — %s (agle 00:00 tak nahi chalega)", provider, reason)


def lock_auth(provider: str, reason: str) -> None:
    """401 — key galat/missing. Is session me band."""
    UNTIL[provider] = float("inf")
    LAST[provider] = " ".join(str(reason).split())[:200]
    HUMAN[provider] = "key galat — nayi key chahiye"
    log.error("%s BAND — %s", provider, reason)


def fail(provider: str, kind: str, reason: str, retry_after: int = 0) -> str:
    """Ek fail register karo, sahi category ka cooldown. Wapas: kind."""
    if kind == "gone":
        return kind
    if kind == "billing":
        till_next_day(provider, reason)
    elif kind == "auth":
        lock_auth(provider, reason)
    elif kind == "empty":
        skip(provider, reason, EMPTY_COOLDOWN)
    else:
        skip(provider, reason, retry_after or None)
    return kind


def classify_and_skip(provider: str, reason) -> str:
    """TTS fail me wahi rule: bad category par cooldown, warna chhod do."""
    kind = classify(reason)
    if kind in ("busy", "billing", "auth", "empty"):
        fail(provider, kind, str(reason))
    return kind


def blocked_reason(provider: str) -> str:
    """Khali = abhi chal sakta hai. Nahi to chhodne ka karan (log + UI)."""
    if provider in NEXT_DAY:
        deadline, reason = NEXT_DAY[provider]
        if time.monotonic() < deadline:
            return f"{provider} BAND — {reason} (agle din tak)"
        NEXT_DAY.pop(provider, None)   # naya din — dubara try ho sakta hai
    until = UNTIL.get(provider)
    if until is None:
        return ""
    if time.monotonic() < until:
        return f"{provider} {_human(until - time.monotonic())} rest par ({LAST.get(provider, '')})"
    UNTIL.pop(provider, None)
    HUMAN.pop(provider, None)
    return ""


def last_fail(provider: str) -> str:
    return LAST.get(provider, "")


def cooldowns() -> dict:
    out = dict(HUMAN)
    for name in NEXT_DAY:
        out[name] = "agle din tak (credits/payment)"
    return out


def reset_provider(provider: str) -> None:
    """Nayi key daalne par band provider kholo."""
    NEXT_DAY.pop(provider, None)
    UNTIL.pop(provider, None)
    HUMAN.pop(provider, None)
    LAST.pop(provider, None)


def reset_all() -> None:
    GONE.clear(); UNTIL.clear(); LAST.clear(); NEXT_DAY.clear(); HUMAN.clear()


def warnings() -> list:
    """Startup log aur UI banner ke liye ek line per problem."""
    out = [f"model {model} hata diya gaya" for model in GONE]
    for name, (_d, reason) in NEXT_DAY.items():
        out.append(f"{name} BAND — {reason}")
    for name, until in list(UNTIL.items()):
        if until == float("inf"):
            out.append(f"{name} BAND — {LAST.get(name, 'auth')}")
        elif time.monotonic() < until:
            out.append(f"{name} {_human(until - time.monotonic())} rest par")
    return out