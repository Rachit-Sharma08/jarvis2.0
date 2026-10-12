"""Fixed jawab ka cache key — time jaise badalne wale jawab ke liye.

`voice/tts.py` ka cache `(text, mode)` par hai. Ye theek hai jab text **same**
ho ("Ji, boliye", "Screen par confirm kijiye"). Par "abhi 3 ghante 20 minute ho
rahe hain" har baar naya text hota hai — to cache **kabhi hit nahi** hota, aur
TTS har sawal dobara banti hai (~1.5-2 s).

Is liye: jawab me **time** ho to key me **minute ka bucket** daal dete hain.
Usi minute me dobara poochha to audio reuse (0 ms). agli minute me naya — sahi
bhi hai, kyunki time to badal chuka hota.

**Ye sirf key badalta hai, cache nahi** — cache wahi bounded LRU hai
(`voice/tts.py` ka `_CACHE` + `CACHE_MAX`). Isi liye memory tez nahi bharati.

SABOOT: `core/directreply.py` ke DIRECT_TOOLS me `get_time_date` hai, yaani
time wala jawab LLM se nahi, seedha tool-result se aata hai — wahi sabse
zyada repeat hota hai aur isi ka sabse zyada faida hai.
"""

import re
import time

# "3:20", "03:20", "3 ghante 20 minute", "7 baje" — time ke nishaan.
_TIME_RE = re.compile(
    r"\b\d{1,2}\s*[:.]\s*\d{2}\b"                       # 3:20
    r"|\b\d{1,2}\s*(ghante|minute|second|baje|second)\b"  # 3 ghante
    r"|\b\d{1,2}\s*(am|pm|a\.m|p\.m)\b",                 # 7 pm
    re.IGNORECASE)

# Saal/date bhi time jaisi hi: "14 October" har din badalta hai.
_DATE_RE = re.compile(r"\b\d{1,2}\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|"
                      r"nov|dec)[a-z]*\b", re.IGNORECASE)


def is_volatile(text: str) -> bool:
    """Ye jawab time/date batata hai (ya use par depend karta hai)?"""
    body = str(text or "")
    return bool(_TIME_RE.search(body) or _DATE_RE.search(body))


def bucket(now=None) -> int:
    """Minute ka number. Cache key me judta hai."""
    moment = time.time() if now is None else float(now)
    return int(moment // 60)


def key(text: str, mode: str, now=None) -> tuple:
    """`(text, mode)` ya volatile ho to `(text, mode, minute)`.

    Static text ka key **bilkul waisa** rehta hai — is liye `tts_cache` ke
    purane test aur prewarm ka koi matlab nahi badla.

    ⚠️ `text` ko `str()` **nahi** karte. Purana cache `key = (text, mode)`
    tha, aur `config.ACK_ON_WAKE` jaise text asal me **tuple** hain — `str()`
    karne se key badal jaata tha aur `tests/test_tts_prewarm.py` ka
    `_CACHE.pop((config.ACK_ON_WAKE, "sunday"))` chup-chaap fail ho jaata.
    Sirf volatile check ke liye text ko padha jaata hai."""
    if is_volatile(text):
        return (text, mode, bucket(now))
    return (text, mode)
