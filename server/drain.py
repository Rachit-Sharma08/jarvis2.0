"""Engine generator ko thread se chalana — dono raaste ke liye ek hi helper.

`/chat` (HTTP) aur `/ws` (WebSocket) dono engine ka generator consume karte hain.
Ye function dono jagah chalti hai, isliye engine ka raasta ek hi rehta hai.

Zaroori kyun: ASK tool ka card 60 second tak wait karta hai. Agar ye generator
seedha event loop par chalta to `/tool/confirm` ka POST kabhi serve hi nahi hota
— user ALLOW hi nahi daba paata. `asyncio.to_thread` se loop khaali rehta hai.
"""

import asyncio

_DONE = object()


def _next_or_done(iterator):
    return next(iterator, _DONE)


async def drain(generator):
    """Generator ke har event ko async-ly aage badhao. `_DONE` par ruk jao."""
    iterator = iter(generator)
    while True:
        item = await asyncio.to_thread(_next_or_done, iterator)
        if item is _DONE:
            return
        yield item
