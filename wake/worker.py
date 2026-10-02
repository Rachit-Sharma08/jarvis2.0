"""Wake word worker — Step 3a me sirf STUB.

Shell (tray, HUD, supervisor) pehle bana rahe hain, wake baad me. Is liye
ye file abhi sirf itna karti hai ki `desktop/app.py` ko ek saaf raasta mile:
`start()` / `stop()` / `state()`.

Step 1 me is file ki jagah asli worker aayega:
  model.py   — Vosk model load (models/vosk-model-small-en-us-0.15)
  audio.py   — sounddevice se mic, EK hi owner
  detect.py  — Vosk recognizer
  phrase.py  — "hello sunday" / "hey sunday" ka pakadna
  worker.py  — yehi file, state machine

Tab tak wake jaan-boojh kar band rehta hai: koi mic nahi khulta, koi audio
kahin nahi jata. Tray ka rang `off` dikhta hai.
"""

import threading

from log_setup import get_logger

log = get_logger("wake")

READY = False            # Step 1 me True hoga
_stop = threading.Event()


def start(on_wake=None, on_state=None) -> bool:
    """Worker chalao. Abhi nahi chal sakta — Step 1 me sahi hoga. -> chala ya nahi"""
    if not READY:
        log.info("wake word abhi nahi hai (Step 1 me aayega) — mic nahi khula")
        if on_state is not None:
            on_state("off")
        return False
    return _start_real(on_wake, on_state)     # Step 1 me bharenge


def stop() -> None:
    _stop.set()


def state() -> str:
    return "off"


def _start_real(_on_wake, _on_state) -> bool:      # pragma: no cover
    """Step 1 me replace hoga. Ab tak koi call nahi aata."""
    raise NotImplementedError("wake worker Step 1 me banta hai")
