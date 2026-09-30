"""Tool ke server endpoints. Teeno par wahi Host -> Origin -> token check.

- POST /tool/confirm  -> Allow/Deny sirf UI ke button se (id + hash ke saath)
- POST /tools/toggle  -> TOOLS OFF / ON kill switch
- POST /tools/cancel  -> STOP: pending card + chalta hua command
- GET  /tools/status  -> kill switch ki halaat
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

import config
from gatekeeper import keeper
from server import security
from tools import command

router = APIRouter()


class ConfirmIn(BaseModel):
    id: str
    hash: str
    allow: bool


class ToggleIn(BaseModel):
    on: bool


def _guard(request: Request) -> None:
    denied = security.verify(
        request.headers.get("origin", ""),
        request.headers.get("host", ""),
        request.headers.get(security.TOKEN_HEADER, ""),
    )
    if denied:
        raise HTTPException(*denied)


@router.post("/tool/confirm")
async def confirm(data: ConfirmIn, request: Request):
    """Sirf UI ka button yahan aata hai. Hash galat ya replay -> 409."""
    _guard(request)
    ok, reason = keeper.APPROVALS.decide(data.id, data.hash, data.allow)
    if not ok:
        raise HTTPException(409, reason)
    return {"ok": True, "decision": "allow" if data.allow else "deny"}


@router.post("/tools/toggle")
async def toggle(data: ToggleIn, request: Request):
    _guard(request)
    return {"tools_on": keeper.set_tools(data.on)}


@router.post("/tools/cancel")
async def cancel(request: Request):
    """STOP dabane par pending card aur chalte hue command dono ruk jaate hain."""
    _guard(request)
    card, _reason = keeper.cancel_all()
    return {"card_cancelled": card, "commands_stopped": command.cancel_all()}


@router.post("/tools/status")
async def status(request: Request):
    _guard(request)
    return {
        "tools_on": keeper.tools_on(),
        "used": keeper.LIMITER.used(),
        "limit": config.TOOL_MAX_CALLS_PER_MINUTE,
    }
