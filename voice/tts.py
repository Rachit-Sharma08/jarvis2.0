import time

import config
from brain import health
from core.timing import Stopwatch
from log_setup import get_logger
from voice import answer_cache
from voice import tts_cartesia, tts_edge, tts_elevenlabs, tts_female
from voice.tts_text import (clip, clip_answer, clean,  # noqa: F401 (re-export)
                            voice_answer)

log = get_logger("tts")

PROVIDERS = {
    "elevenlabs": tts_elevenlabs,
    "cartesia": tts_cartesia,
    "edge": tts_edge,
}


def missing_key(name: str) -> str:
    """Is provider ki key lagi hai? `''` = haan. Nahi to chhodne ka karan.

    Voice id check (`config.voice_for`) **alag** hai — id ho sakta hai par key
    na ho. Pehle yahi check nahi tha, is liye key khaali hone par bhi har jawab
    me network call jaata tha (aur phir fail hota tha). Pure function."""
    if name == "elevenlabs" and not config.has_elevenlabs():
        return "elevenlabs: key nahi hai"
    if name == "cartesia" and not config.has_cartesia():
        return "cartesia: key nahi hai"
    return ""


class TtsError(Exception):
    pass


# ---- Fixed UI phrases ka audio cache ----------------------------------------
#
# "Ji, boliye", "confirm kijiye", "Abhi jawab nahi mil pa raha" — ye **constant**
# (ya dobara aane wale) hain. Inka TTS har baar dobara banane me ~1.5 s lagta
# tha, jo wake ke total 18 s me sabse bada chunk tha. Ab pehli baar ban-te
# hain, phir memory se.
#
# Brain ka **naya** jawab bhi isse guzarta hai (sab awaaz ka ek hi raasta hai),
# par wo dobara aayega hi nahi — bas 8 entry ki limit me memory par koi asar
# nahi padta (har audio ~50 KB). Isi liye cache **bounded** hai: `CACHE_MAX`
# se upar ki purani entry nikal jaati hai, warna har message par memory badhti
# rahegi.
_CACHE = {}
CACHE_MAX = 8


async def speak_cached(text: str, mode: str) -> tuple:
    """`(audio, provider)` — same text+mode pe dobara provider mat pucho.

    Sirf wahi text cache hota hai jo **constant** hai (`config.ACK_ON_WAKE` jaise).
    Naya/unique text (brain ka jawab) bhi yahin se jaata hai, par dobara hit
    nahi hoga — bas limit me rehke memory par koi asar nahi padega.

    Cache hit par bhi ek line log hota hai, is liye speed ka proof log me
    dikhta hai (`tts cache hit: N chars`).
    """
    key = answer_cache.key(text, mode)
    hit = _CACHE.get(key)
    if hit is not None:
        log.info("tts cache hit: %d chars", len(text or ""))
        return hit
    # `speak()` ko hi call karo (na `_speak_uncached` directly) — is liye test
    # me `tts.speak` badalne wala fake bhi yahin se aata hai, aur asli raasta
    # sirf ek hi rehta hai.
    audio, provider = await speak(text, mode)
    if len(_CACHE) >= CACHE_MAX:
        _CACHE.pop(next(iter(_CACHE)))
    _CACHE[key] = (audio, provider)
    return audio, provider


def cache_clear() -> None:
    """Cache khaali (app band karte waqt, ya test me)."""
    _CACHE.clear()


async def speak(text: str, mode: str) -> tuple:
    """Elevenlabs -> Cartesia -> edge. Teeno fail ho to saaf error.

    Ye **cache nahi** karta. Awaaz ka ek hi raasta `speak_cached()` hai (jo isko
    call karta hai) — is liye kahin se bhi `speak()` seedha bulao tab bhi kaam
    karega, bas cache hit nahi hoga.

    Returns (audio_bytes, provider_name).
    """
    return await _speak_uncached(text, mode)


async def _speak_uncached(text: str, mode: str) -> tuple:
    """Asli kaam — pehle wala `speak()` ka badla hua naam (cache bahar hai)."""
    spoken = clip(clean(text))
    if not spoken:
        raise TtsError("Bolne layak text nahi bacha.")

    watch = Stopwatch("tts")
    problems = []
    for name in config.TTS_CHAIN:
        rest = health.blocked_reason(name)
        if rest:
            log.info("tts %s skip: %s", name, rest)
            problems.append(f"{name}: rest par")
            continue
        voice = config.voice_for(name, mode)
        if name in ("elevenlabs", "cartesia") and not voice:
            log.info("tts %s skip: %s ke liye voice id nahi hai", name, mode)
            problems.append(f"{name}: voice id nahi")
            continue
        # Key khaali hai to **bilkul try na ho** — network call aur fail dono
        # bekaar. Voice id wala check upar hai; ye usse alag.
        nokey = missing_key(name)
        if nokey:
            log.info("tts %s skip: %s", name, nokey.split(": ", 1)[-1])
            problems.append(nokey)
            continue
        # Female allowlist. List me nahi to skip — male awaaz kabhi nahi bolega.
        male_guard = tts_female.check(name, voice)
        if male_guard:
            log.info("tts %s skip: %s", name, male_guard)
            problems.append(male_guard)
            continue
        start = time.perf_counter()
        try:
            audio = await PROVIDERS[name].speak(spoken, mode)
        except Exception as exc:
            took = watch.stage(f"{name}-fail", start)
            problems.append(f"{name}: {exc}")
            log.warning("tts %s fail (%dms) -> %s", name, took, exc)
            # Sirf exception text classify karo — voice id me "429" jaisa
            # hissa aayega to 10 min ka galat rest na lage.
            health.classify_and_skip(name, str(exc))
            continue
        took = watch.stage(name, start)
        last4 = (voice or config.EDGE_VOICES.get(mode, ""))[-4:]
        log.info("TIME tts: provider=%s mode=%s voice=..%s chars=%d bytes=%d %dms",
                 name, mode, last4, len(spoken), len(audio), took)
        watch.total()
        return audio, name

    log.error("sab TTS providers fail -> %s", " | ".join(problems))
    watch.total()
    raise TtsError(
        "Awaaz nahi ban paayi. "
        + " | ".join(problems)[:200]
        + " — thodi der baad try karo."
    )