"""Ek message me kai kaam? Code se todo, ek-ek karke chalao.

Voice/Telegram par user aksar ek saans me 4-5 kaam bolta hai ("vs code khol,
terminal khol, mummy ko call, gaana chala"). Model ek jawab me ek hi action
deta hai aur phir "sab ho gaya" bol deta hai (live 30-Oct: 6 kaam, 1 chala) —
planning LLM par chhodna kaam nahi karta. Is liye message ko yahan todte hain
aur har kaam apna alag engine turn ban jaata hai.

Sirf voice (`wake/ask.py`) aur Telegram (`server/telegram_bot.py`) isse
guzarte hain; `/chat` aur `/ws` ka streaming raasta waisa hi hai.
"""

import re

from core import events

MAX_TASKS = 6
_SPLIT = re.compile(r"\s+(?:aur|or|phir|fir|then)\s+|,|;", re.IGNORECASE)


def split(text: str) -> list:
    """Message ko chhote kaamon me todo. Ek hi kaam ho to wahi wapas."""
    parts = [part.strip(" .\t") for part in _SPLIT.split(str(text or ""))]
    parts = [part for part in parts if len(part) > 2]
    return parts[:MAX_TASKS] if len(parts) > 1 else [str(text or "")]


def run(engine, text: str, rid: str):
    """Generator: har kaam ke events, aakhir me ek joda hua jawab (agar >1)."""
    answers = []
    for index, part in enumerate(split(text)):
        for event in engine.handle(part, "%s-%d" % (rid, index + 1)):
            if event.get("type") == "message" and event.get("role") == "assistant":
                answers.append(event.get("text") or "")
            yield event
    if len(answers) > 1:
        yield events.message("assistant", " | ".join(a for a in answers if a))
