from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from core.engine import Engine
from log_setup import get_logger
from server import security

log = get_logger("server")

app = FastAPI(title="Prabh")
engine = Engine()
app.mount("/ui", StaticFiles(directory=str(config.UI_DIR)), name="ui")


class ChatIn(BaseModel):
    text: str


@app.get("/")
async def index(request: Request):
    denied = security.verify_host(request.headers.get("host", ""))
    if denied:
        raise HTTPException(*denied)

    html = (config.UI_DIR / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html.replace(security.TOKEN_PLACEHOLDER, security.token()))


@app.post("/chat")
async def chat(data: ChatIn, request: Request):
    denied = security.verify(
        request.headers.get("origin", ""),
        request.headers.get("host", ""),
        request.headers.get(security.TOKEN_HEADER, ""),
    )
    if denied:
        raise HTTPException(*denied)

    events = list(engine.handle(data.text))
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
            for event in engine.handle(payload.get("text", "")):
                await sock.send_json(event)
    except WebSocketDisconnect:
        log.info("websocket disconnected")
    except Exception as exc:
        log.error("websocket error: %s: %s", type(exc).__name__, exc)