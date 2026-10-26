import asyncio

from html import escape

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from brain import checkup
from core import sysstats
from gatekeeper import keeper
from log_setup import get_logger
from server import security
from server.brain_routes import router as brain_router
from server.drain import drain
from server.hub import HUB
from server.hud_routes import router as hud_router
from server.state import engine as shared_engine
from server.tool_routes import router as tool_router
from server.voice_routes import router as voice_router
from server.ws_routes import router as ws_router
from voice import stt_local

log = get_logger("server")

app = FastAPI(title=config.ASSISTANT_NAME)
# Ek hi Engine poore server me (server/state.py) — /chat, /ws aur /hud/quick
# teono ka mode aur gatekeeper state ek jaisa rahe.
engine = shared_engine()
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
    # `same-origin` — baharee site ko referrer jaata hi nahi (privacy waisi hi
    # rehti hai), lekin apne hi page ka referrer server ko dikhta hai. Isse
    # `server/security.py` same-origin GET (jaise /brain/status, jisme browser
    # Origin header bhejta hi nahi) par jaanch kar paata hai. `no-referrer` hota
    # to wo jaanch chalti hi nahi thi.
    response.headers["Referrer-Policy"] = "same-origin"
    return response


def fill_html(html: str, theme: str = "") -> str:
    """`index.html` ke placeholders bhar do — token, tools, naam, theme.

    Ye **pure function** hai is liye test `GET /` chala ke ( asli server, port,
    Edge) verify karne ki zaroorat nahi padti. Route sirf isko call karta hai —
    yahin se naam aata hai, is liye UI me "Jarvis" hard-code nahi hai.

    `theme` (KAAM B): sirf `"gold"`. Route `?theme=` se deta hai, warna
    `config.hud_theme()` (`JARVIS_HUD_THEME`). Whitelist `config.HUD_THEMES`
    me hai — koi bhi adhoori value ya query string seedha `<html data-theme>`
    me nahi jaati (warna ek `?theme=<script>` se attribute injection hota).
    `resolve_theme()` wo whitelist hai; is function me dobara check nahi.
    """
    html = html.replace(security.TOKEN_PLACEHOLDER, security.token())
    html = html.replace("__JARVIS_TOOLS_ON__", "1" if keeper.tools_on() else "0")
    # Naam config se (config_name.ASSISTANT_NAME / DISPLAY_NAME). UI, tray aur
    # shortcut — sab ek hi jagah se badalte hain.
    html = html.replace("__JARVIS_ASSISTANT_NAME__", escape(config.ASSISTANT_NAME))
    html = html.replace("__JARVIS_DISPLAY_NAME__", escape(config.DISPLAY_NAME))
    html = html.replace("__JARVIS_HUD_THEME__", theme or config.hud_theme())
    # Startup warning plain text hai — ise HTML me escape karke hi daalte hain.
    return html.replace("__JARVIS_BRAIN_WARN__", escape(checkup.banner()))


def resolve_theme(raw: str) -> str:
    """`?theme=` ya config se asli theme. **Sirf** do maane jaate hain.

    Ye whitelist ka ek hi raasta hai (KAAM B). `fill_html()` is par bharosa
    karta hai — is liye yahan se guzar ke koi value `<html data-theme="...">`
    me nahi aa sakti, na ki ek query string attribute injection ban sakti hai.
    """
    want = (raw or "").strip().lower()
    if want in config.HUD_THEMES:
        return want
    return config.hud_theme()


@app.get("/")
async def index(request: Request):
    denied = security.verify_host(request.headers.get("host", ""))
    if denied:
        raise HTTPException(*denied)

    # `?theme=` sirf whitelist (`gold`) se guzarta hai; warna config ka value.
    return HTMLResponse(fill_html(
        (config.UI_DIR / "index.html").read_text(encoding="utf-8"),
        resolve_theme(request.query_params.get("theme", ""))))


@app.post("/chat")
async def chat(data: ChatIn, request: Request):
    denied = security.verify_request(request, request.headers.get(security.TOKEN_HEADER, ""))
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
    # Local STT model (faster-whisper) background me load — pehli command par
    # 4 s ka load na lage. Key na ho to bhi JARVIS sun sake.
    stt_local.warm_async()
    # 'HUD ready' sirf `desktop/app.py` bolta hai (startup ki 4 line, ek jagah).
    # Yahan sirf HTTP layer ka haalat.
    log.info("http routes ready: stats pump + %d quick buttons",
             len(config.QUICK_BUTTONS))
