"""Error text se category — sirf yahi file word/pattern decide karti hai.

Categories (health.py in par cooldown lagati hai):
  gone    -> 404, model hata diya gaya. Session me permanent.
  quota   -> daily/monthly limit. Agle 00:00 tak.
  billing -> cloud credits khatam / payment required. Nayi key tak.
  busy    -> 429/503/timeout. Retry-After, warna 10 min.
  empty   -> khaali jawab. 45s.
  other   -> baaki sab. 10 min.

'quota' aur 'billing' alag rakhna zaroori: quota apne aap theek ho jaata hai
agle din, credits nahi — nayi key chahiye.
"""

import re

# Word-boundary se. Bina boundary "4299" (voice id me) bhi 429 ban jata.
CODE_RE = re.compile(r"\b(402|429|503|500|502)\b")
GONE_MARKERS = ("model_not_found", "does not exist", "no longer available",
                "not found for api version", "model not found")
BUSY_WORDS = ("payment_required", "rate limit", "rate_limit", "resource_exhausted",
              "unavailable", "overloaded")
BILLING_RE = re.compile(r"insufficient_?funds|paid_plan|upgrade your plan|billing", re.IGNORECASE)
# Cloud credits khatam = nayi key chahiye. Daily quota nahi — isliye alag.
CREDIT_RE = re.compile(
    r"insufficient_?credit|credits?\s*expired|cloud\s*credits?|add\s*credits?"
    r"|credit\s*balance|payment\s*required|out\s*of\s*credits", re.IGNORECASE)
# Din/maah ki limit. 429 ke saath bhi yahi rule chalta hai.
QUOTA_RE = re.compile(r"daily\s*quota|quota\s*exceeded|exceeded your\s*current quota"
                      r"|monthly\s*quota|quota_exceeded", re.IGNORECASE)


def classify(exc) -> str:
    """Groq/Gemini SDK, TTS ya koi bhi exception -> category."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(m in text for m in GONE_MARKERS):
        return "gone"
    if QUOTA_RE.search(text):
        return "quota"
    if CREDIT_RE.search(text) or BILLING_RE.search(text):
        return "billing"
    if CODE_RE.search(text) or any(w in text for w in BUSY_WORDS):
        return "busy"
    if "khaali" in text or "empty" in text:
        return "empty"
    return "other"


def is_503(exc) -> bool:
    """Sirf 503 (overloaded) par retry — 429/402 par retry bekaar hai."""
    return bool(CODE_RE.search(f"{type(exc).__name__}: {exc}")) and "503" in str(exc)