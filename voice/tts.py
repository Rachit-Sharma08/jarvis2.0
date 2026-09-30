import re

import config
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

    problems = []
    for name in config.TTS_CHAIN:
        try:
            audio = await PROVIDERS[name].speak(spoken, mode)
            log.info("tts provider: %s", name)
            return audio, name
        except Exception as exc:
            problems.append(f"{name}: {exc}")
            log.warning("%s fail, agla try kar rahe -> %s", name, exc)

    log.error("sab TTS providers fail -> %s", " | ".join(problems))
    raise TtsError(
        "Awaaz nahi ban paayi. Thodi der baad try karo. "
        "Details logs/prabh.log me hain."
    )