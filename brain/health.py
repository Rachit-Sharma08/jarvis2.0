"""Brain/TTS doctor: kaunsa provider abhi safe hai.

gone=404 (permanent) · busy=429/503/timeout (Retry-After, warna 10 min) ·
quota=limit khatam (agle 00:00) · billing=credits khatam (nayi key tak) ·
auth=401 · empty=khaali jawab (45s) · other=10 min.

Category ke word/pattern `health_words.py` me hain; yahan sirf state + cooldown.
Ek hi source — pool.py, checkup.py, tts.py aur /brain/status sab yahi padhte hain.
"""

import datetime
import time

from brain import health_words
from log_setup import get_logger

log = get_logger("health")

# Word/pattern yahan se bhi nikaal sakte hain (purana import na toote).
CODE_RE, GONE_MARKERS, BUSY_WORDS = health_words.CODE_RE, health_words.GONE_MARKERS, health_words.BUSY_WORDS
BILLING_RE, CREDIT_RE, QUOTA_RE = health_words.BILLING_RE, health_words.CREDIT_RE, health_words.QUOTA_RE

GONE = {}       # model -> reason (permanent, is session me)
UNTIL = {}      # provider -> monotonic deadline
LAST = {}       # provider -> last fail ka chhota reason
NEXT_DAY = {}   # provider -> (deadline, reason) — agle 00:00 tak
HUMAN = {}      # provider -> "12 min baad" jaisa text

DEFAULT_COOLDOWN = 600     # 10 min
EMPTY_COOLDOWN = 45        # khaali jawab — jaldi phir try


def classify(exc) -> str:
    """Exception -> category (pattern health_words me)."""
    return health_words.classify(exc)


def is_503(exc) -> bool:
    return health_words.is_503(exc)


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


def is_gone(model: str) -> bool:
    """Ye model 404 ho chuka hai? (key me model naam, provider se alag)"""
    return model in GONE


def _lock(provider: str, reason: str, human: str) -> None:
    """Seedha BAND — koi deadline nahi. Sirf reset_provider (nayi key) khol sakta hai."""
    UNTIL[provider] = float("inf")
    LAST[provider] = " ".join(str(reason).split())[:200]
    HUMAN[provider] = human
    log.error("%s BAND — %s (nayi key/session tak nahi chalega)", provider, reason)


def lock_credits(provider: str, reason: str) -> None:
    """Cloud credits khatam / payment required — nayi key tak, agle din tak NAHI."""
    _lock(provider, reason, "credits khatam — nayi key chahiye")


def skip(provider: str, reason: str, seconds: int = None) -> None:
    rest = seconds if seconds else DEFAULT_COOLDOWN
    UNTIL[provider] = time.monotonic() + rest
    LAST[provider] = " ".join(str(reason).split())[:200]
    HUMAN[provider] = _human(rest)
    log.warning("%s ko %ds ka rest — %s", provider, rest, reason)


def till_next_day(provider: str, reason: str) -> None:
    """Din/maah ki limit. Agle 00:00 tak band."""
    NEXT_DAY[provider] = (_midnight(), " ".join(str(reason).split())[:200])
    LAST[provider] = NEXT_DAY[provider][1]
    HUMAN[provider] = "agle din tak (quota)"
    log.error("%s BAND — %s (agle 00:00 tak nahi chalega)", provider, reason)


def lock_auth(provider: str, reason: str) -> None:
    """401 — key galat/missing. Is session me band."""
    _lock(provider, reason, "key galat — nayi key chahiye")


def fail(provider: str, kind: str, reason: str, retry_after: int = 0) -> str:
    """Ek fail register karo, sahi category ka cooldown. Wapas: kind."""
    if kind == "gone":
        return kind
    text = str(reason)
    # 4 alag rules: credits = nayi key tak, quota = agle din, auth = session,
    # khaali = 45s, baaki = Retry-After ya 10 min.
    if CREDIT_RE.search(text) or kind == "credits":
        lock_credits(provider, text)
    elif kind in ("quota", "billing") or QUOTA_RE.search(text):
        till_next_day(provider, text)
    elif kind == "auth":
        lock_auth(provider, text)
    elif kind == "empty":
        skip(provider, text, EMPTY_COOLDOWN)
    else:
        skip(provider, text, retry_after or None)
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
        # Naya din — purana record saaf, warna UI me stale cooldown dikhega.
        NEXT_DAY.pop(provider, None)
        HUMAN.pop(provider, None)
    until = UNTIL.get(provider)
    if until is None:
        return ""
    if until == float("inf"):
        # credits khatam ya key galat — inf tak band.
        return f"{provider} BAND — {LAST.get(provider, 'credits/auth')} ({HUMAN.get(provider, 'nayi key chahiye')})"
    if time.monotonic() < until:
        return f"{provider} {_human(until - time.monotonic())} rest par ({LAST.get(provider, '')})"
    UNTIL.pop(provider, None)
    HUMAN.pop(provider, None)
    return ""


def last_fail(provider: str) -> str:
    return LAST.get(provider, "")


def cooldowns() -> dict:
    """Sirf ABHI band providers. Expired hua entry yahin se saaf hota hai."""
    for name in list(UNTIL) + list(NEXT_DAY):
        blocked_reason(name)
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
    for name in list(UNTIL) + list(NEXT_DAY):
        reason = blocked_reason(name)
        if reason:
            out.append(reason)
    return out