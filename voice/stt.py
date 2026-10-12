import asyncio
import io
import threading
import time

from groq import Groq

import config
from log_setup import get_logger
from voice import stt_guard

log = get_logger("stt")


class SttError(Exception):
    pass


def _client() -> Groq:
    """Groq client — STT ka **apna** chhota timeout + 1 retry.

    Pehle `config.BRAIN_TIMEOUT_GROQ` (10 s) use hota tha aur SDK apne aap 2 baar
    retry karta tha — 3.5 s ki audio par call **43 s** tak atak sakta tha (S-1
    audit: `stt failed (43503ms)`). Brain ka timeout STT ke liye sahi number nahi."""
    return Groq(api_key=config.GROQ_API_KEY,
                timeout=config.STT_TIMEOUT_SECONDS,
                max_retries=config.STT_MAX_RETRIES)


def _transcribe(audio: bytes) -> str:
    # `language` jaan-boojh kar NAHI bhejte. Romanized Hinglish (English
    # akshar + Hindi shabd) `language="hi"` par bigaad jata tha — saboot
    # ROUND2.md me. Whisper khud dono script pehchanta hai.
    reply = _client().audio.transcriptions.create(
        file=("mic.webm", io.BytesIO(audio)),
        model=config.GROQ_STT_MODEL,
    )
    return (reply.text or "").strip()


def _run_bounded(fn, audio, deadline):
    """`fn(audio)` ko ek **daemon** thread me chalao, `deadline` tak wait karo.

    **`asyncio.to_thread` akela kaafi nahi.** `wake/listen.py` `asyncio.run()`
    use karta hai, aur woh band hote waqt executor ka **join** wait karta hai
    (`shutdown_default_executor`) — matlab SDK atka to caller bhi atkta, chahe
    `asyncio.wait_for` ceiling laga di ho. Daemon thread + `join(timeout)` me
    caller turant laut aata hai; bacha hua thread process band hote par mar
    jata hai, koi nuksan nahi.

    Timeout: `TimeoutError`. Baaki exception as-is (wahi SttError banega)."""
    box = {}

    def run():
        try:
            box["text"] = fn(audio)
        except BaseException as exc:          # noqa: BLE001 - wapas bhejna hai
            box["error"] = exc

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(deadline)
    if thread.is_alive():
        raise TimeoutError(f"deadline {deadline:.1f}s")
    if "error" in box:
        raise box["error"]
    return box.get("text", "")


async def transcribe(audio: bytes, duration_ms=None) -> str:
    """Browser ka recording -> text (Hindi + English dono samajhta hai)."""
    if not config.has_groq():
        raise SttError("GROQ_API_KEY missing hai. .env check karo.")
    if not audio:
        raise SttError("Recording khaali aayi.")
    # Size guard YAHAN hai, sirf route me nahi. Wake path (`wake/listen.py`)
    # bhi yahin se guzarta hai, aur 11 MB ka blob provider tak bhejne ki zaroorat
    # nahi — quota bachega aur test bhi asli network par nahi jaayega.
    if len(audio) > config.AUDIO_MAX_BYTES:
        raise SttError("Recording bahut badi hai.")

    # Chhoti recording (600ms se kam) me insaan ki awaaz nahi hoti — call
    # jyada kharch karega aur text ghalt aayega.
    short = stt_guard.bad_duration(duration_ms)
    if short:
        log.info("stt guard: %s", short)
        raise SttError("Bahut chhoti recording. Thodi der bolke try karo.")

    start = time.perf_counter()
    try:
        # Do parde: `_run_bounded` SDK ke budget ka ceiling rakhta hai, aur
        # `to_thread` event loop ko free rakhta hai (HTTP route ke liye).
        text = await asyncio.to_thread(
            _run_bounded, _transcribe, audio, config.stt_deadline())
    except TimeoutError as exc:
        took = int((time.perf_counter() - start) * 1000)
        log.error("stt atka (%dms) - ceiling %.1fs: %s", took,
                  config.stt_deadline(), exc)
        raise SttError("Sun nahi paya (awaaz bhejne me waqt laga). Dobara boliye.")
    except Exception as exc:
        log.error("stt failed (%dms): %s: %s", int((time.perf_counter() - start) * 1000),
                  type(exc).__name__, exc)
        raise SttError(f"Sun nahi paya ({exc}).") from exc

    if not text:
        log.warning("stt ne khaali text diya")
        raise SttError("Sun nahi paya. Thoda loud bolke try karo.")

    # Khamoshi ka nishaan ya galat script — user ko text mat dikhao.
    bad = stt_guard.guard_text(text)
    if bad:
        log.info("stt guard: text reject — %s | %r", bad, text[:60])
        raise SttError("Sun nahi paya (awaz saaf nahi thi). Thoda loud bolke try karo.")

    log.info("TIME stt: %s %dms | %d chars", config.GROQ_STT_MODEL,
             int((time.perf_counter() - start) * 1000), len(text))
    return text