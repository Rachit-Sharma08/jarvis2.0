"""Groq pehle, phir Gemini. Dono fail = ek hi message, dono errors ke saath."""

import time

from brain import gemini_client, groq_client, health
from log_setup import get_logger

log = get_logger("router")

ORDER = [("groq", groq_client), ("gemini", gemini_client)]
MAX_ERROR_CHARS = 160


def _short(problem: str) -> str:
    problem = " ".join(str(problem).split())
    return problem if len(problem) <= MAX_ERROR_CHARS else problem[:MAX_ERROR_CHARS] + "..."


def ask(history: list, persona: str) -> tuple:
    start = time.perf_counter()
    problems = []

    for name, client in ORDER:
        rest = health.blocked_reason(name)
        if rest:
            log.info("%s skip: %s", name, rest)
            problems.append(f"{name} rest par hai")
            continue
        try:
            answer = client.ask(history, persona)
            log.info("TIME brain: %s total %dms", name, int((time.perf_counter() - start) * 1000))
            return answer, name
        except Exception as exc:
            problems.append(_short(f"{name}: {exc}"))
            log.warning("%s fail, agla try kar rahe -> %s", name, exc, exc_info=True)

    problems += [_short(w) for w in health.warnings()]
    log.error("All brains failed -> %s", " | ".join(problems), exc_info=True)
    log.info("TIME brain: fail total %dms", int((time.perf_counter() - start) * 1000))
    return (
        "Abhi koi brain jawab nahi de paya. Ye reasons mila:\n"
        + "\n".join(f"- {p}" for p in problems),
        "none",
    )
