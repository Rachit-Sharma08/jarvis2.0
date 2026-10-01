"""Engine ka brain raasta. Asli kaam brain/pool.py me hai.

Ye file sirf compatibility layer hai — engine `router.ask()` call karta hai.
Naya provider yahan nahi, brain/pool_config.py me add hoga.
"""

from brain import pool
from log_setup import get_logger

log = get_logger("router")


def ask(history: list, persona: str) -> tuple:
    """(answer, provider_name). Sab fail par ek saaf message reasons ke saath."""
    return pool.ask(history, persona)


def status() -> dict:
    return pool.status()