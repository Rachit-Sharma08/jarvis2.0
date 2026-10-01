"""WebSocket clients ka in-process hub. Ek jagah se publish, sab par bhejo.

Iska kaam: server ke alag-alag hisse (stats pump, quick tool, chat) ko ek hi
tarah se UI tak pahunchana, bina har jagah connection list sambhaale.

Do baatein yaad rakhni:
- `publish()` kisi bhi THREAD se call ho sakta hai (tool `asyncio.to_thread`
  me chalta hai). Isliye `call_soon_threadsafe` zaroori hai — `Queue.put_nowait`
  seedha thread se crash kara sakta hai.
- Queue bhari ho to event phenk dete hain. Stats/heartbeat discard-able hai;
  ek slow tab band karke usse reconnect karwa dena behtar hai.
"""

import asyncio


class Hub:
    def __init__(self) -> None:
        self._queues: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def attach(self, loop: asyncio.AbstractEventLoop) -> None:
        """Server start par ek baar. Iske bina thread-safe push nahi hoga."""
        self._loop = loop

    def subscribe(self, maxsize: int = 200) -> asyncio.Queue:
        """Nayi connection ke liye queue. `unsubscribe` bhoolna mat."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._queues.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._queues:
            self._queues.remove(queue)

    @property
    def clients(self) -> int:
        return len(self._queues)

    @staticmethod
    def _put(queue: asyncio.Queue, event: dict) -> None:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass          # slow client — stats chhup jaana theek hai

    def publish(self, event: dict) -> None:
        """Kisi bhi thread se bhej sakte hain. Exception kabhi nahi uthata."""
        loop = self._loop
        for queue in list(self._queues):
            if loop is not None and loop.is_running():
                try:
                    loop.call_soon_threadsafe(self._put, queue, event)
                except RuntimeError:
                    pass      # loop band ho gaya
            else:
                self._put(queue, event)


HUB = Hub()
