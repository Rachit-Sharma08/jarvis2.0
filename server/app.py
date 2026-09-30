from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from core.engine import Engine
from log_setup import get_logger

log = get_logger("server")

app = FastAPI(title="Prabh")
engine = Engine()
app.mount("/ui", StaticFiles(directory=str(config.UI_DIR)), name="ui")


class ChatIn(BaseModel):
    text: str


@app.get("/")
async def index():
    return FileResponse(config.UI_DIR / "index.html")


@app.post("/chat")
async def chat(data: ChatIn):
    events = list(engine.handle(data.text))
    return {"events": events, "mode": engine.mode}


@app.websocket("/ws")
async def ws(sock: WebSocket):
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