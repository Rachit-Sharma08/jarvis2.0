"""STT ke saamne wala filter. Recording + text dono jaanche jaate hain.

Chaar guard:
  1. duration_ms < 600  -> chhoo (dab dab / mic chhua)
  2. khamoshi ke phrases -> Whisper YouTube hallucinations deta hai
  3. script check        -> sirf Devanagari ya Latin, baaki kuch nahi
  4. text khaali        -> error

Romanized Hinglish (English akshar) jaan-boojh kar CHALEGA — wahi asli Hinglish
hai. `language="hi"` bhejne se Whisper romanized text bigaad deta tha, isliye
wo hint jaan-boojh kar nahi bheja jaata.
"""

import re
import unicodedata

from log_setup import get_logger

log = get_logger("stt_guard")

MIN_DURATION_MS = 600

# Whisper khamoshi par ye nikal deta hai (mostly YouTube training ka asar).
SILENCE_PHRASES = (
    "thank you", "thanks for watching", "thank you for watching",
    "subtitles by", "amara.org", "subtitle by", "please subscribe",
    "thank you.", "thanks.", "bye.", "bye", "okay.", "so",
    "you", "the", "music", "applause", "silence", "blank audio",
    "inaudible", "foreign", "hmm", "uh", "um",
)

PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
SPACE_RE = re.compile(r"\s+")
DIGIT_RE = re.compile(r"\d")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
LATIN_RE = re.compile(r"[A-Za-z]")
# Devanagari ya Latin ke alaawa koi bhi letter (Cyrillic, Arabic, CJK...).
OTHER_LETTER_RE = re.compile(
    r"[^\W\d_]", re.UNICODE)


def bad_duration(duration_ms) -> str:
    """'' = theek. Nahi to chhodne ka reason."""
    if duration_ms in (None, ""):
        return ""          # browser ne nahi bheja — pichle record jaisa
    try:
        ms = int(duration_ms)
    except (TypeError, ValueError):
        return f"duration samajh nahi aaya ({duration_ms!r})"
    if ms < 0:
        return "duration negative hai"
    if ms < MIN_DURATION_MS:
        return f"recording bahut chhoti ({ms}ms)"
    return ""


def _normal(text: str) -> str:
    text = PUNCT_RE.sub(" ", text or "")
    text = SPACE_RE.sub(" ", text).strip().lower()
    return text


def is_silence_phrase(text: str) -> str:
    """Khamoshi ka nishaan? ('' nahi, matched phrase return karta hai)."""
    norm = _normal(text)
    if not norm:
        return ""
    # Poora text hi ek known phrase hai ya bahut chhota filler hai.
    if len(norm) <= 24:
        for phrase in SILENCE_PHRASES:
            if norm == phrase.rstrip(".") or norm == phrase:
                log.info("stt guard: khamoshi ka phrase reject — %r", norm)
                return norm
    if "subtitles by" in norm or "amara.org" in norm or "thanks for watching" in norm:
        return norm
    return ""


def script_ok(text: str) -> str:
    """Sirf Hindi (Devanagari) ya English (Latin)? '' = theek, warna reason."""
    norm = _normal(text)
    if not norm:
        return "khaali text"
    letters = OTHER_LETTER_RE.findall(norm)
    if not letters:
        return "sirf number/symbol"
    if len(letters) < 2:
        return "sirf ek akshar"
    if not (DEVANAGARI_RE.search(norm) or LATIN_RE.search(norm)):
        return "Hindi/English script nahi"
    # Koi bhi letter Devanagari/Latin se bahar — reject.
    for ch in letters:
        if not (DEVANAGARI_RE.match(ch) or LATIN_RE.match(ch)):
            return f"galat script: {unicodedata.name(ch, '?')[:30]}"
    # Aadha se zyada number ho to recording number gin raha hai, baat nahi.
    if len(DIGIT_RE.findall(norm)) > len(norm) / 2:
        return "zyada number"
    return ""


# Whisper ka kachra: TV/YouTube ya shor par "okay okay okay", "Tee. Tee." jaisa
# text. Ye brain tak jaata tha aur Jarvis bekaar jawab deta tha.
FILLER_WORDS = frozenset((
    "okay", "ok", "tee", "thank", "thanks", "bye", "so", "you", "the",
    "music", "hmm", "uh", "um", "ah", "oh", "yeah", "yes", "no",
))
MIN_LETTERS = 3


def is_garbage(text: str) -> str:
    """Shor ka kachra? ('' = theek, warna reason)."""
    norm = _normal(text)
    if not norm:
        return "khaali"
    if len(OTHER_LETTER_RE.findall(norm)) < MIN_LETTERS:
        return "bahut chhota text"
    tokens = norm.split()
    if len(tokens) >= 2 and len(set(tokens)) == 1:
        word = tokens[0]
        if word in FILLER_WORDS or (len(tokens) >= 3 and len(word) <= 5):
            return f"ek hi shabd repeat: {word!r}"
    return ""


def guard_text(text: str) -> str:
    """Poora text guard. '' = chalane layak, warna reason."""
    if not (text or "").strip():
        return "khaali text"
    silence = is_silence_phrase(text)
    if silence:
        return "khamoshi ka phrase"
    bad = script_ok(text)
    if bad:
        return bad
    return is_garbage(text)