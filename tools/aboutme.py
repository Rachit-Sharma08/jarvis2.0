"""User ke baare me yaad rakhna — `core/profile.py` (local `data/profile.json`).

Sirf do kaam: `remember` (naya fact / purana update) aur `forget` (privacy).
Padhna tool se nahi hota — profile har prompt me khud chali jaati hai.
"""

from core import profile


def remember(key: str, value: str) -> str:
    return profile.remember(key, value)


def forget(key: str) -> str:
    return profile.forget(key)
