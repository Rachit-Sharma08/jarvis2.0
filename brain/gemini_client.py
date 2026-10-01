import time

from google import genai
from google.genai import types

import config
from brain import health
from log_setup import get_logger

log = get_logger("gemini")


class BrainError(Exception):
    pass


def _is_timeout(exc: Exception) -> bool:
    text = f"{type(exc).__name__} {exc}".lower()
    return "timeout" in text or "deadline" in text or "504" in text


def _call(model: str, prompt: str, persona: str) -> str:
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    reply = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=persona,
            max_output_tokens=config.BRAIN_MAX_TOKENS,
            http_options=types.HttpOptions(timeout=int(config.BRAIN_TIMEOUT_GEMINI * 1000)),
        ),
    )
    return (reply.text or "").strip()


def ask(history: list, persona: str) -> str:
    if not config.has_gemini():
        log.warning("Gemini key missing in .env")
        raise BrainError("GEMINI_API_KEY missing")

    rest = health.blocked_reason("gemini")
    if rest:
        raise BrainError(f"Gemini rest par hai: {rest}")

    prompt = persona + "\n\n" + "\n".join(
        ("User: " if m["role"] == "user" else "Assistant: ") + m["content"]
        for m in history
    )

    problems, tried = [], 0
    for model in config.GEMINI_MODELS:
        if model in health.GONE:
            continue
        if health.blocked_reason("gemini"):
            # Pichla model 402/429/503/timeout par fail hua — provider 10 min rest par
            # hai, to iska dusra model bhi mat chalao.
            break
        tried += 1
        for attempt in (1, 2):  # 503 par ek retry
            start = time.perf_counter()
            try:
                text = _call(model, prompt, persona)
            except Exception as exc:
                took = int((time.perf_counter() - start) * 1000)
                kind = health.classify(exc)
                log.error("Gemini %s fail (%dms, %s, try %d): %s: %s",
                          model, took, kind, attempt, type(exc).__name__, exc)
                problems.append(f"{model} ({type(exc).__name__})")
                if kind == "gone":
                    health.model_gone("gemini", model, f"{type(exc).__name__}: {exc}")
                    break
                if kind == "busy":
                    if health.is_503(exc) and attempt == 1:
                        log.warning("Gemini %s par 503 — %.1fs baad ek retry",
                                    model, config.GEMINI_RETRY_WAIT)
                        time.sleep(config.GEMINI_RETRY_WAIT)
                        continue
                    health.skip("gemini", f"{model} par {type(exc).__name__}: {exc}")
                    break
                if _is_timeout(exc):
                    # 15s me nahi aaya. Har request pe 15s rukna bura hai —
                    # 10 min rest de do, tab try karenge.
                    health.skip("gemini", f"{model} par {config.BRAIN_TIMEOUT_GEMINI}s timeout")
                    break
                raise BrainError(f"Gemini error: {exc}") from exc

            took = int((time.perf_counter() - start) * 1000)
            if not text:
                raise BrainError("Gemini ne khaali jawab diya")
            log.info("TIME gemini: %s %dms | %d chars", model, took, len(text))
            return text

    detail = " | ".join(problems) or "saare models pehle se hata chuke hain"
    raise BrainError(f"Gemini fail ({tried} try): {detail}")
