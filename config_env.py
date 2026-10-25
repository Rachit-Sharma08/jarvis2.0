"""Env var ke naam: naya `JARVIS_*`, purana `PRABH_*` bhi chalta rahe.

App ka naam pehle Sunday, phir Prabh, ab Jarvis hai. `.env` me kisi ke paas
purane naam (`PRABH_WAKE=1`) likhe ho sakte hain, is liye ye module import hote
hi har `PRABH_*` ko `JARVIS_*` me copy kar deta hai (naya naam pehle se set ho
to use chhedta nahi). Code sirf `JARVIS_*` padhta hai — ek hi naam.

Ye module **sabse pehle** import hona chahiye, is liye har `config_*.py` ise
`import os` se pehle import karta hai. Isme sirf `os` aata hai — koi circular
import nahi.
"""

import os

NEW = "JARVIS_"
OLD = "PRABH_"


def alias_legacy() -> int:
    """Purane `PRABH_*` ko `JARVIS_*` me copy karo. -> kitne copy hue."""
    moved = 0
    for name, value in list(os.environ.items()):
        if not name.startswith(OLD):
            continue
        new = NEW + name[len(OLD):]
        if new not in os.environ:
            os.environ[new] = value
            moved += 1
    return moved


alias_legacy()
