from groq import Groq

import config
from log_setup import get_logger

log = get_logger("groq")


class BrainError(Exception):
    pass


def ask(history: list, persona: str) -> str:
    if not config.has_groq():
        log.warning("Groq key missing in .env")
        raise BrainError("GROQ_API_KEY missing")

    messages = [{"role": "system", "content": persona}] + history
    try:
        client = Groq(api_key=config.GROQ_API_KEY)
        reply = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
        )
        text = (reply.choices[0].message.content or "").strip()
    except Exception as exc:
        log.error("Groq failed: %s: %s", type(exc).__name__, exc)
        raise BrainError(f"Groq error: {exc}") from exc

    if not text:
        log.error("Groq returned empty answer")
        raise BrainError("Groq returned empty answer")

    log.info("Groq answered (%d chars)", len(text))
    return text