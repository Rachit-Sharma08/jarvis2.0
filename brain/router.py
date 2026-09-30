from brain import gemini_client, groq_client
from log_setup import get_logger

log = get_logger("router")

ORDER = [("groq", groq_client), ("gemini", gemini_client)]


def ask(history: list, persona: str) -> tuple:
    """Try Groq first, fall back to Gemini. Returns (answer, brain_name)."""
    problems = []
    for name, client in ORDER:
        try:
            return client.ask(history, persona), name
        except Exception as exc:
            problems.append(f"{name}: {exc}")
            log.warning("%s failed, trying next -> %s", name, exc)

    log.error("All brains failed -> %s", " | ".join(problems))
    return (
        "Abhi koi brain jawab nahi de paya. Thodi der baad try karo.\n"
        "Details logs/prabh.log me hain.",
        "none",
    )