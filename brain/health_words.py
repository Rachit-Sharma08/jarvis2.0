"""Error text se category — sirf yahi file word/pattern decide karti hai.

Categories (health.py in par cooldown lagati hai):
  gone    -> 404, model hata diya gaya. Session me permanent.
  quota   -> daily/monthly limit. Agle 00:00 tak.
  billing -> cloud credits khatam / payment required. Nayi key tak.
  busy    -> 429/503/timeout. Retry-After, warna 10 min.
  auth    -> 401/403. Key galat — **is session me BAND** (nayi key tak).
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
# 401/403 = key galat ya permission nahi. **13-Oct tak ye category hi nahi
# thi** — 401 `other` ban kar `classify_and_skip` se guzarta hi nahi tha (wo
# sirf busy/billing/auth/empty par kuch karta hai), is liye ElevenLabs ka 401
# **har jawab me dobara poora** poochha jaata tha (~0.7-1 s har message).
# Ab `auth` -> `lock_auth()` -> is session me BAND, seedha Edge par jao.
AUTH_RE = re.compile(r"\b(401|403)\b|unauthori[sz]ed|invalid[_ ]?api[_ ]?key"
                     r"|forbidden", re.IGNORECASE)


def classify(exc) -> str:
    """Groq/Gemini SDK, TTS ya koi bhi exception -> category."""
    text = f"{type(exc).__name__}: {exc}".lower()
    if any(m in text for m in GONE_MARKERS):
        return "gone"
    if QUOTA_RE.search(text):
        return "quota"
    if CREDIT_RE.search(text) or BILLING_RE.search(text):
        return "billing"
    # `busy` se pehle: 403 message me "rate limit" bhi aa sakta hai, par key
    # galat hai — retry bekaar. `\b` ki wajah se voice id me "401" nahi pakda.
    if AUTH_RE.search(text):
        return "auth"
    if CODE_RE.search(text) or any(w in text for w in BUSY_WORDS):
        return "busy"
    if "khaali" in text or "empty" in text:
        return "empty"
    return "other"


def is_503(exc) -> bool:
    """Sirf 503 (overloaded) par retry — 429/402 par retry bekaar hai."""
    return bool(CODE_RE.search(f"{type(exc).__name__}: {exc}")) and "503" in str(exc)