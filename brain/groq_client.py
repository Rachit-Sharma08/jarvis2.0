import time

from groq import Groq

import config
from brain import health
from log_setup import get_logger

log = get_logger("groq")


class BrainError(Exception):
    pass


def ask(history: list, persona: str) -> str:
    if not config.has_groq():
        log.warning("Groq key missing in .env")
        raise BrainError("GROQ_API_KEY missing")

    rest = health.blocked_reason("groq")
    if rest:
        raise BrainError(f"Groq rest par hai: {rest}")

    messages = [{"role": "system", "content": persona}] + history
    problems, tried = [], 0
    for model in config.GROQ_MODELS:
        if model in health.GONE:
            continue
        tried += 1
        start = time.perf_counter()
        try:
            client = Groq(api_key=config.GROQ_API_KEY, timeout=config.BRAIN_TIMEOUT_GROQ)
            reply = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
            )
            text = (reply.choices[0].message.content or "").strip()
        except Exception as exc:
            took = int((time.perf_counter() - start) * 1000)
            kind = health.classify(exc)
            log.error("Groq %s fail (%dms, %s): %s: %s", model, took, kind, type(exc).__name__, exc)
            problems.append(f"{model} ({type(exc).__name__})")
            if kind == "gone":
                health.model_gone("groq", model, f"{type(exc).__name__}: {exc}")
                continue
            if kind == "busy":
                health.skip("groq", f"{model} par {type(exc).__name__}: {exc}")
                break
            raise BrainError(f"Groq error: {exc}") from exc

        took = int((time.perf_counter() - start) * 1000)
        if not text:
            raise BrainError("Groq ne khaali jawab diya")
        log.info("TIME groq: %s %dms | %d chars", model, took, len(text))
        return text

    detail = " | ".join(problems) or "saare models pehle se hata chuke hain"
    raise BrainError(f"Groq fail ({tried} try): {detail}")
