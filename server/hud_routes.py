"""Phase 4 HUD ke endpoints. Teeno par wahi Host -> Origin -> token check.

- GET  /hud/stats    → psutil ka ek sample (WebSocket se bhi aata rehta hai;
                       ye ek baar load par bhi chalta hai taaki panel khali na rahe)
- GET  /hud/weather  → Open-Meteo, sirf server se (browser bahar nahi jaata)
- POST /hud/quick    → bottom bar ke 6 button. YAHAAN KOI BYPASS NAHI —
                       `engine.run_tool()` hi call hota hai, jo gatekeeper
                       (kill switch + rate limit + confirm card) se guzta hai.

Quick ka saf flow: button id config me hona chahiye, args UI se nahi aate
(UI sirf id bhejta hai), aur kaam background me chalta hai taaki confirm card
ka 60 second ka wait HTTP request ko rok na de.
"""

import asyncio

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

import config
from core import sysstats
from log_setup import get_logger
from server import security, weather
from server.drain import drain
from server.hub import HUB
from server.state import engine as shared_engine

log = get_logger("hud_routes")
router = APIRouter()


class QuickIn(BaseModel):
    # `extra="forbid"` zaroori hai: UI sirf `id` bhejta hai. Iske bina koi
    # browser `{"id": "scan", "tool": "run_command"}` bhej de to pydantic
    # extra field chupa deta aur request chal jaati. Args hamesha config se
    # aate hain, par extra ko mana karna saaf aur saarega hai.
    model_config = ConfigDict(extra="forbid")

    id: str


def _guard(request: Request) -> None:
    denied = security.verify_request(request, request.headers.get(security.TOKEN_HEADER, ""))
    if denied:
        raise HTTPException(*denied)


@router.get("/hud/stats")
async def hud_stats(request: Request):
    _guard(request)
    return sysstats.stats()


@router.get("/hud/weather")
async def hud_weather(request: Request):
    _guard(request)
    data = weather.for_ui()
    data["hint"] = "" if data.get("ok") else f"{config.WEATHER_CITY} ka weather poochiye"
    return data


async def _run_quick(tool: str, args: dict) -> None:
    """`engine.run_tool` ka generator chala kar har event hub par bhejo.

    Gatekeeper ke andar hi rehta hai — kill switch OFF ho to confirm/deny
    activity hi aayegi, aur rate limit 20/min yahin ginti hai.
    """
    try:
        # Shared engine (server/state.py) — isse user ke current mode aur
        # gatekeeper state ke saath hi chalega, alag instance nahi.
        async for event in drain(shared_engine().run_tool(tool, args)):
            HUB.publish(event)
    except Exception as exc:
        log.error("quick tool %s: %s: %s", tool, type(exc).__name__, exc)
        HUB.publish({"type": "activity", "tool": tool, "decision": "deny",
                     "text": f"quick button fail: {type(exc).__name__}"})


@router.post("/hud/quick")
async def hud_quick(data: QuickIn, request: Request):
    _guard(request)
    button = config.quick_by_id(data.id)
    if button is None:
        log.warning("quick id reject: %r", data.id)
        raise HTTPException(404, "ye quick button nahi hai.")

    # Args config se — UI se kuch bhi nahi aata.
    args = dict(button["args"])
    if args.get("path") == "":
        args["path"] = str(config.ensure_workspace())
    tool = button["tool"]
    log.info("quick: %s -> %s", button["id"], tool)

    asyncio.create_task(_run_quick(tool, args))
    return {"queued": True, "id": button["id"], "tool": tool}
