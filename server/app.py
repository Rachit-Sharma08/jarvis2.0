import asyncio

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from core.engine import Engine
from gatekeeper import keeper
from log_setup import get_logger
from server import security
from server.tool_routes import router as tool_router
from server.voice_routes import router as voice_router

log = get_logger("server")

app = FastAPI(title="Prabh")
engine = Engine()
app.mount("/ui", StaticFiles(directory=str(config.UI_DIR)), name="ui")
app.include_router(voice_router)
app.include_router(tool_router)

_DONE = object()


def _next_or_done(iterator):
    return next(iterator, _DONE)


async def drain(generator):
    """Engine ko thread me chalao taaki event loop khaali rahe.

    Zaroori hai: ASK tool ka card 60 second tak wait karta hai. Agar ye loop
    par chalta to /tool/confirm ka POST kabhi serve hi nahi hota.
    """
    iterator = iter(generator)
    while True:
        item = await asyncio.to_thread(_next_or_done, iterator)
        if item is _DONE:
            return
        yield item


class ChatIn(BaseModel):
    text: str


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
    return HTMLResponse(html.replace("__PRABH_TOOLS_ON__", "1" if keeper.tools_on() else "0"))


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
    async for event in drain(engine.handle(data.text)):
        events.append(event)
    return {"events": events, "mode": engine.mode}


@app.websocket("/ws")
async def ws(sock: WebSocket):
    denied = security.verify(
        sock.headers.get("origin", ""),
        sock.headers.get("host", ""),
        sock.query_params.get("token", ""),
    )
    if denied:
        await sock.close(code=1008)
        return

    await sock.accept()
    await sock.send_json({"type": "status", "value": "idle"})
    log.info("websocket connected")
    try:
        while True:
            payload = await sock.receive_json()
            async for event in drain(engine.handle(payload.get("text", ""))):
                await sock.send_json(event)
    except WebSocketDisconnect:
        log.info("websocket disconnected")
    except Exception as exc:
        log.error("websocket error: %s: %s", type(exc).__name__, exc)
