"""Telegram — phone se text (ya voice note) bhejo, ghar ka PC wahi kaam kare.

Ye wahi "Tab jaisa" channel hai: user phone par likhta hai, jawab yahan hi
aata hai, aur asli kaam is PC par hota hai.

Ek hi raasta: `server.state.ENGINE` — wahi object jo `/chat` aur wake word use
karte hain (alag `Engine()` banane ka niyam nahi hai). Tool ka raasta bhi wahi
(`engine.run_tool` → `keeper.review`), is liye yahan koi naya bypass nahi banta.

**Owner-only:** `config_telegram.CHAT_ID` ke alawa koi likhe to bot sirf uski
chat id bata deta hai — koi command nahi chalti. Token `.env` se aata hai.

Bot daemon thread me long-poll karta hai (`getUpdates`) — koi webhook, koi
public port nahi. App band = bot band. ASK card ka koi button yahan nahi hai,
is liye jo tool card maangta hai wo timeout par khud DENY ho jaata hai.
"""

import asyncio
import json
import threading
import time
import urllib.parse
import urllib.request

import config
import config_telegram
from log_setup import get_logger
from server.state import engine
from voice import stt

log = get_logger("telegram")

_API = "https://api.telegram.org/bot%s/%s"
_stop = threading.Event()
_thread = None


def _call(method: str, params: dict = None, timeout: float = 30) -> dict:
    """Telegram API ka ek call. Test isko badal deta hai (network kabhi nahi)."""
    data = urllib.parse.urlencode(params or {}).encode("utf-8")
    req = urllib.request.Request(
        _API % (config_telegram.TOKEN, method), data=data)
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8", "replace"))


def send(chat_id, text) -> None:
    """Jawab bhejo (lamba text tukdon me — Telegram 4096 par reject karta hai)."""
    text = (text or "").strip() or config.NOT_UNDERSTOOD
    size = config_telegram.TELEGRAM_MAX_CHARS
    for i in range(0, len(text), size):
        _call("sendMessage", {"chat_id": chat_id, "text": text[i:i + size]})


def owner(chat_id) -> bool:
    """Sirf owner ki chat? (Khaali allowlist = koi nahi.)"""
    return (bool(config_telegram.CHAT_ID)
            and str(chat_id) == str(config_telegram.CHAT_ID))


def ask(text: str) -> str:
    """ENGINE se ek jawab — aakhri `assistant` message."""
    async def run():
        out = ""
        async for ev in engine().handle(text, "tg%d" % int(time.time() * 1000)):
            if ev.get("type") == "message" and ev.get("role") == "assistant":
                out = ev.get("text") or out
        return out
    return asyncio.run(run())


def voice_text(file_id: str, duration) -> str:
    """Telegram voice note -> text (wahi STT: Groq / local, wahi guard)."""
    info = _call("getFile", {"file_id": file_id})
    path = ((info or {}).get("result") or {}).get("file_path") or ""
    if not path:
        return ""
    url = "https://api.telegram.org/file/bot%s/%s" % (config_telegram.TOKEN, path)
    with urllib.request.urlopen(url, timeout=30) as res:
        audio = res.read()
    return asyncio.run(stt.transcribe(audio, int(duration or 0) * 1000))


def handle(update: dict, reply=None) -> str:
    """Ek update ka faisla -> kya hua (test + log ke liye)."""
    msg = (update or {}).get("message") or {}
    chat = (msg.get("chat") or {}).get("id")
    if chat is None:
        return "ignore"
    reply = reply or send
    if not owner(chat):
        reply(chat, "Ye private assistant hai. Iski chat id: %s" % chat)
        return "not-owner"
    try:
        if msg.get("voice"):
            text = voice_text(msg["voice"].get("file_id"),
                              msg["voice"].get("duration")) or ""
        else:
            text = (msg.get("text") or "").strip()
        if not text:
            return "empty"
        reply(chat, ask(text))
        return "answered"
    except Exception as exc:
        log.error("telegram: %s: %s", type(exc).__name__, exc)
        reply(chat, "Nahi ho paya, Sir (%s)." % type(exc).__name__)
        return "error"


def _loop() -> None:
    """Long-poll: naya message aate hi handle; network girre to 5 s baad phir."""
    offset = 0
    while not _stop.is_set():
        try:
            data = _call("getUpdates",
                         {"offset": offset,
                          "timeout": config_telegram.TELEGRAM_POLL_SECONDS},
                         timeout=config_telegram.TELEGRAM_POLL_SECONDS + 15)
        except Exception as exc:
            log.warning("telegram poll fail: %s", exc)
            _stop.wait(5)
            continue
        for upd in (data or {}).get("result") or []:
            offset = max(offset, int(upd.get("update_id", 0)) + 1)
            try:
                handle(upd)
            except Exception as exc:      # ek update ka crash loop na mare
                log.error("telegram update crash: %s", exc)


def start() -> bool:
    global _thread
    if not config_telegram.has_telegram() or _thread is not None:
        return False
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="telegram", daemon=True)
    _thread.start()
    log.info("telegram bot chalu (owner chat set: %s)",
             bool(config_telegram.CHAT_ID))
    return True


def stop() -> None:
    global _thread
    _stop.set()
    if _thread is not None:
        _thread.join(timeout=3)
        _thread = None
