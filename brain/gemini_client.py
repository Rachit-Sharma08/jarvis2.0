from google import genai
from google.genai import types

import config
from log_setup import get_logger

log = get_logger("gemini")


class BrainError(Exception):
    pass


def ask(history: list, persona: str) -> str:
    if not config.has_gemini():
        log.warning("Gemini key missing in .env")
        raise BrainError("GEMINI_API_KEY missing")

    prompt = persona + "\n\n" + "\n".join(
        ("User: " if m["role"] == "user" else "Assistant: ") + m["content"]
        for m in history
    )
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        reply = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=persona,
                max_output_tokens=800,
            ),
        )
        text = (reply.text or "").strip()
    except Exception as exc:
        log.error("Gemini failed: %s: %s", type(exc).__name__, exc)
        raise BrainError(f"Gemini error: {exc}") from exc

    if not text:
        log.error("Gemini returned empty answer")
        raise BrainError("Gemini returned empty answer")

    log.info("Gemini answered (%d chars)", len(text))
    return text