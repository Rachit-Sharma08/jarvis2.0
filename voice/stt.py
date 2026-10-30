import asyncio
import io
import threading
import time

from groq import Groq

import config
from log_setup import get_logger
from voice import stt_guard
from voice import stt_local

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
    # Filename `.wav` hai kyunki audio WAV hai (`wake/wav.py`); pehle `.webm`
    # likha tha — Groq format naam se bhi andaza lagata hai.
    reply = _client().audio.transcriptions.create(
        file=("mic.wav", io.BytesIO(audio)),
        model=config.GROQ_STT_MODEL,
        # Hinglish hint + `temperature=0` (29-Oct): bina hint ke turbo model
        # "ku?" / "Tee. Tee." jaisa kachra deta tha. `language` jaan-boojh kar
        # nahi bhejte — romaanized text bigadta hai (upar wali line).
        prompt=config.STT_PROMPT,
        temperature=0,
    )
    return (reply.text or "").strip()


def _transcribe_local(audio: bytes) -> str:
    """Free/offline raasta — `voice/stt_local.py` (faster-whisper, CPU)."""
    return stt_local.transcribe(audio)


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


def provider() -> str:
    """Kaun sunega: `groq` (cloud) | `local` (offline) | `''` (koi nahi).

    `JARVIS_STT_LOCAL` se: `auto` (default) = Groq key ho to Groq, warna local;
    `local` = hamesha offline; `groq` = sirf cloud; `off` = local band.
    """
    mode = config.STT_LOCAL
    if mode in ("local", "whisper", "offline"):
        return "local" if stt_local.available() else ""
    if mode in ("groq", "cloud"):
        return "groq" if config.has_groq() else ""
    if config.has_groq():
        return "groq"
    if mode in ("0", "off", "false", "no", "disabled"):
        return ""
    return "local" if stt_local.available() else ""


def _provider_error() -> SttError:
    if config.STT_LOCAL in ("local", "whisper", "offline"):
        return SttError("Local STT model nahi mila (models/faster-whisper-small).")
    return SttError("Koi STT nahi: GROQ_API_KEY khaali hai aur local model bhi nahi mila.")


def _may_fall_back() -> bool:
    """Groq fail hone par local try karein? `groq` mode forced hai to nahi."""
    if config.STT_LOCAL in ("groq", "cloud"):
        return False
    return stt_local.available()


async def _listen(which: str, audio: bytes) -> str:
    """Ek provider se sunna - ceiling + event loop dono sambhale hue."""
    fn = _transcribe if which == "groq" else _transcribe_local
    deadline = (config.stt_deadline() if which == "groq"
                else config.STT_LOCAL_DEADLINE_SECONDS)
    # Do parde: `_run_bounded` provider ke budget ka ceiling rakhta hai, aur
    # `to_thread` event loop ko free rakhta hai (HTTP route ke liye).
    return await asyncio.to_thread(_run_bounded, fn, audio, deadline)


def _failed(exc: Exception, took: int) -> SttError:
    """Provider ka exception -> user ke liye saaf Hinglish message."""
    if isinstance(exc, TimeoutError):
        log.error("stt atka (%dms): %s", took, exc)
        return SttError("Sun nahi paya (awaaz bhejne me waqt laga). Dobara boliye.")
    log.error("stt failed (%dms): %s: %s", took, type(exc).__name__, exc)
    return SttError(f"Sun nahi paya ({exc}).")


async def transcribe(audio: bytes, duration_ms=None) -> str:
    """Browser/wake ki recording -> text (Hindi + English dono samajhta hai)."""
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

    which = provider()
    if not which:
        raise _provider_error()

    start = time.perf_counter()
    try:
        text = await _listen(which, audio)
    except TimeoutError as exc:
        # Budget khatam - ab local par jaana matlab user ko dobara 75 s ka
        # intezaar. Turant saaf message (S-1 ka niyam: caller atke nahi).
        raise _failed(exc, int((time.perf_counter() - start) * 1000)) from exc
    except Exception as exc:
        took = int((time.perf_counter() - start) * 1000)
        # Groq turant gira (network/429/5xx) to local model se sun lo. Warna key
        # hone par bhi JARVIS behra ho jata - wahi purana bug, doosre raaste se.
        if which != "groq" or not _may_fall_back():
            raise _failed(exc, took) from exc
        log.warning("groq fail (%dms): %s - local par", took, exc)
        which = "local"
        try:
            text = await _listen("local", audio)
        except Exception as exc2:
            raise _failed(exc2, int((time.perf_counter() - start) * 1000)) from exc2

    if not text:
        log.warning("stt ne khaali text diya (%s)", which)
        raise SttError("Sun nahi paya. Thoda loud bolke try karo.")

    # Khamoshi ka nishaan ya galat script — user ko text mat dikhao.
    bad = stt_guard.guard_text(text)
    if bad:
        log.info("stt guard: text reject — %s | %r", bad, text[:60])
        raise SttError("Sun nahi paya (awaz saaf nahi thi). Thoda loud bolke try karo.")

    log.info("TIME stt: %s %dms | %d chars", which,
             int((time.perf_counter() - start) * 1000), len(text))
    return text
