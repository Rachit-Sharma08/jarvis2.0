"""Poore server ke liye EK shared Engine.

Pehle `server/app.py`, `server/ws_routes.py` aur `server/hud_routes.py` — teeno
apna alag `Engine()` bana rahe the. Iska matlab:

- `/chat` se mode PRABH kar do, lekin WebSocket wala engine abhi bhi SUNDAY
  rahega (aur ulta).
- `/hud/quick` ke tools hamesha SUNDAY persona ke hisaab se chaleenge.
- Ek hi request par do engine ke gatekeeper state alag-alag honge.

Engine me mode, tool-loop state aur active tool rehta hai — is liye yeh ek
hi instance honi chahiye. Yahan se sab jagah wahi object milta hai.

Rule (AGENTS.md): brain ka ek raasta, tool ka ek raasta. Ye file un dono ko
ek jagah baandh deti hai.
"""

from core.engine import Engine

ENGINE = Engine()


def engine() -> Engine:
    """FastAPI dependency / direct call dono ke liye."""
    return ENGINE