"""WebSocket `/ws` — chat + live stats dono ek hi connection par.

Purana kaam (chat → engine → events) waise hi hai. Naya: har
`STATS_INTERVAL_SECONDS` me ek `stats` event publish hota hai, taaki UI ke
SYSTEM panel ko polling karne ki zarurat na pade.

Connection loop do kaam saath-saath karta hai:
- client se message (receive_json) — chat ke liye
- hub se server event (queue.get) — stats/activity/confirm ke liye

`asyncio.wait(FIRST_COMPLETED)` se dono par wait karte hain. Dono kaam ek
thread me nahi jaate — engine `drain()`/`to_thread` se chalta hai, jaise pehle.
"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import config
from core import sysstats
from log_setup import get_logger
from server import security
from server.drain import drain
from server.hub import HUB
from server.state import engine as shared_engine

log = get_logger("ws")
router = APIRouter()


async def stats_pump() -> None:
    """Har 2 second ek stats event. Hamesha chalta rehta hai, har client alag."""
    while True:
        try:
            await asyncio.sleep(config.STATS_INTERVAL_SECONDS)
            HUB.publish({"type": "stats", "data": sysstats.stats()})
        except asyncio.CancelledError:
            return
        except Exception as exc:      # pump na to sirf stats ruke, chat safe
            log.error("stats pump: %s: %s", type(exc).__name__, exc)
            await asyncio.sleep(config.STATS_INTERVAL_SECONDS)


@router.websocket("/ws")
async def ws(sock: WebSocket) -> None:
    denied = security.verify_request(sock, sock.query_params.get("token", ""))
    if denied:
        await sock.close(code=1008)
        return

    await sock.accept()
    queue = HUB.subscribe()
    await sock.send_json({"type": "status", "value": "idle"})
    # Naya client ko abhi ka haalat bhi bhejo (desktop mic/tools) — warna
    # pill "DESKTOP …" hi rehta jab state server se pehle set ho chuki ho.
    for event in HUB.welcome():
        await sock.send_json(event)
    log.info("websocket connected")

    pump = asyncio.create_task(stats_pump())
    try:
        while True:
            got = asyncio.create_task(queue.get())
            heard = asyncio.create_task(sock.receive_json())
            done, pending = await asyncio.wait(
                {got, heard}, return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()

            if got in done:                       # server → browser
                try:
                    await sock.send_json(got.result())
                except (WebSocketDisconnect, RuntimeError):
                    raise
                continue

            payload = heard.result()               # browser → server
            text = str(payload.get("text", ""))
            rid = str(payload.get("rid", ""))
            # Shared engine — /chat aur /hud/quick ke saath wahi mode/state.
            async for event in drain(shared_engine().handle(text, rid)):
                await sock.send_json(event)

    except WebSocketDisconnect:
        log.info("websocket disconnected")
    except Exception as exc:
        log.error("websocket error: %s: %s", type(exc).__name__, exc)
    finally:
        pump.cancel()
        HUB.unsubscribe(queue)
