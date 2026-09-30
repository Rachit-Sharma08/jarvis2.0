import re
import time

import config
from brain import health
from core.timing import Stopwatch
from log_setup import get_logger
from voice import tts_cartesia, tts_edge, tts_elevenlabs

log = get_logger("tts")

PROVIDERS = {
    "elevenlabs": tts_elevenlabs,
    "cartesia": tts_cartesia,
    "edge": tts_edge,
}

URL_RE = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U0001F1E6-\U0001F1FF\u2190-\u21FF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]"
)
MARKDOWN_RE = re.compile(r"[*#`>_]+")
SPACES_RE = re.compile(r"[ \t]+")


class TtsError(Exception):
    pass


def clean(text: str) -> str:
    """Awaaz se pehle text saaf karta hai: link, emoji aur markdown hatao."""
    text = URL_RE.sub(" ", text or "")
    text = EMOJI_RE.sub(" ", text)
    text = MARKDOWN_RE.sub(" ", text)
    text = SPACES_RE.sub(" ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def clip(text: str, limit: int = None) -> str:
    """Free quota bachaane ke liye sirf shuruaat boli jaati hai."""
    limit = limit or config.TTS_MAX_CHARS
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.strip()


async def speak(text: str, mode: str) -> tuple:
    """Elevenlabs -> Cartesia -> edge. Teeno fail ho to saaf error.

    Returns (audio_bytes, provider_name).
    """
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
        "Awaaz nahi ban paayi. Thodi der baad try karo. "
        "Details logs/prabh.log me hain."
    )