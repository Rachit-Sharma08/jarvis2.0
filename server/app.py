import asyncio

from html import escape

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from brain import checkup
from core import sysstats
from core.engine import Engine
from gatekeeper import keeper
from log_setup import get_logger
from server import security
from server.brain_routes import router as brain_router
from server.drain import drain
from server.hub import HUB
from server.hud_routes import router as hud_router
from server.tool_routes import router as tool_router
from server.voice_routes import router as voice_router
from server.ws_routes import router as ws_router

log = get_logger("server")

app = FastAPI(title="Prabh")
engine = Engine()
app.mount("/ui", StaticFiles(directory=str(config.UI_DIR)), name="ui")
app.include_router(voice_router)
app.include_router(tool_router)
app.include_router(brain_router)
app.include_router(hud_router)
app.include_router(ws_router)


class ChatIn(BaseModel):
    text: str
    rid: str = ""


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = config.CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/")
async def index(request: Request):
    denied = security.verify_host(request.headers.get("host", ""))
    if denied:
        raise HTTPException(*denied)

    html = (config.UI_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace(security.TOKEN_PLACEHOLDER, security.token())
    html = html.replace("__PRABH_TOOLS_ON__", "1" if keeper.tools_on() else "0")
    # Startup warning plain text hai — ise HTML me escape karke hi daalte hain.
    return HTMLResponse(html.replace("__PRABH_BRAIN_WARN__", escape(checkup.banner())))


@app.post("/chat")
async def chat(data: ChatIn, request: Request):
    denied = security.verify(
        request.headers.get("origin", ""),
        request.headers.get("host", ""),
        request.headers.get(security.TOKEN_HEADER, ""),
    )
    if denied:
        raise HTTPException(*denied)

    events = []
    async for event in drain(engine.handle(data.text, data.rid)):
        events.append(event)
    return {"events": events, "mode": engine.mode}


@app.on_event("startup")
async def _on_startup() -> None:
    """Server shuru hote hi: hub ka loop pakdo aur CPU ka pehla sample le lo.

    `sysstats.prime()` isliye zaroori hai kyunki psutil ka pehla CPU %
    `interval=None` par hamesha 0 deta hai — bina prime ke pehla panel
    2 second tak 0% dikhata.
    """
    HUB.attach(asyncio.get_running_loop())
    sysstats.prime()
    log.info("HUD ready: stats pump + %d quick buttons", len(config.QUICK_BUTTONS))
