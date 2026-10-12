"""Mic ke saath hone wale kaam — `wake/command.py` ki madad ka raasta.

`command.py` sirf **flow** sambhalta hai (kya karna hai, kis order me). Is file
me wo chaar kaam hain jinhe mic chahiye aur jinme koi brain/policy nahi hai:

1. `stop()` / `reset()` — app band ho raha hai to ye `_STOP` set karte hain.
   `wake/worker.py` ka `stop()` yahin aata hai, jiska join sirf 3 s ka hai —
   is liye capture aur aage ka TTS dono ko ye event rokta hai.
2. `drain()` — mic ki queue khaali. Do jagah zaroori hai: bolne se **pehle**
   (purana audio + "Ji, boliye" ki apni awaaz) aur bolne ke **baad** (TTS ka
   shor — warna `Session._loop` use wake shabd samajh kar dobara trigger kar
   deta tha).
3. `warmup()` — mic baithne do (`COMMAND_WARMUP_SECONDS`) phir queue khaali.
   Ye `COMMAND_PRE_ROLL_SECONDS` se alag hai: pre-roll command ke *andar*
   pehle ka buffer jodta hai, ye command se *pehle* mic settle karta hai.
4. `capture()` + `to_text()` — VAD se audio, phir WAV + Groq STT.

**Privacy:** recording sirf memory me rehti hai. `to_text()` bytes bana kar
STT ko deta hai aur kahin file nahi likhta — disk par koi audio nahi jaata.

Koi policy yahan nahi hai: mute/lock ka faisla `desktop/callbacks.py` ka
`allowed()` deta hai aur brain ka faisla `command.py` — is liye ye file pure
mic ka hissa hai aur test me asaani se fake ho jaati hai (`tests/wakehelp.py`).
"""

import asyncio
import queue
import threading
import time

import config
from log_setup import get_logger
from voice import stt as stt_mod
from wake import audio as audio_mod
from wake import utterance as utterance_mod
from wake import wav as wav_mod

log = get_logger("wake_listen")

# App band ho raha hai. `wake/session.py` apna `_stop` bhi deta hai — jo bhi
# pehle bita, rok deta hai.
_STOP = threading.Event()


def stop() -> None:
    """App band ho raha hai — capture aur aage ka TTS turant ruke."""
    _STOP.set()


def reset() -> None:
    """Nayi command se pehle `_STOP` khaali karo (test + worker restart)."""
    _STOP.clear()


def drain(mic, stop=None) -> int:
    """Mic ki queue khaali karo. -> kitne chunk phenke.

    `mic` = `wake/audio.py` ka `MicSource` ya test ka fake — sirf `.chunks`
    queue chahiye. Bounded hai (`MAX_QUEUE_BLOCKS`) taaki mic tez bharte rahe
    to ye loop na phanse."""
    stop = stop or _STOP
    dropped = 0
    while not stop.is_set() and dropped < audio_mod.MAX_QUEUE_BLOCKS:
        try:
            mic.chunks.get_nowait()
        except (queue.Empty, AttributeError):
            break
        dropped += 1
    return dropped


def drop_seconds(mic, stop=None, seconds: float = 0.2) -> int:
    """Sirf `seconds` tak ka audio phenko - **poora drain nahi** (beep ka hissa).

    Poora `drain()` command ko bhi phenk deta tha. -> kitne chunk phenke."""
    stop = stop or _STOP
    left = max(0, int(round(float(seconds) / audio_mod.BLOCK_SECONDS)))
    dropped = 0
    while dropped < left and not stop.is_set():
        try:
            mic.chunks.get_nowait()
        except (queue.Empty, AttributeError):
            break
        dropped += 1
    return dropped


def warmup(mic, stop=None, deadline=None) -> int:
    """Mic settle hone do, phir queue khaali karo. -> kitne chunk phenke.

    Ye command se pehle hota hai — warna `warmup` ke pehle ka buffer capture ke
    shuru me chala jaata aur pehla shabd kat-ta hai.

    `deadline` = absolute `time.monotonic()`. Mic **hamesha** chalta hai, is liye
    "Ji, boliye" bolte waqt bhi settle ho raha hota hai — `wake/command.py` ack
    shuru karne ka time yahan deta hai, aur jitna poora ho chuka hai utna hi
    wait hota hai. Pehle hamesha `COMMAND_WARMUP_SECONDS` (1 s) ka **dead time**
    tha, jabki ack ki awaaz already 2 s chal chuki hoti thi. Ab wo 1 s har baar
    bach jaata hai. Deadline na mile to poora warmup (test ka raasta)."""
    stop = stop or _STOP
    if deadline is None:
        deadline = time.monotonic() + float(config.COMMAND_WARMUP_SECONDS)
    while time.monotonic() < deadline:
        if stop.is_set():
            return 0
        time.sleep(0.02)
    return drain(mic, stop)


def peek_speech(mic, stop=None, seconds: float = None, threshold: float = None) -> tuple:
    """`seconds` tak suno — kya user bol **hi** raha hai? -> `(bol raha hai, RMS)`.

    Ye `"Ji, boliye"` se pehle chalta hai (Step 2 ka speed fix). Pehle hamari ack
    user ki awaaz ke upar bol deti thi, command ka pehla shabd kat-ta tha aur
    use lagta tha "sun nahi pa raha". Ab agar bol raha hai to ack chhoot jaata
    hai — aur ye chhota intezaar mic ka kaam bhi kar deta hai (settle + pehli
    awaaz pakadna), is liye warm-up alag se nahi lagta.

    **Chunk phenke nahi jaate** — jo bhi mila, wahi order me wapas queue me
    daal diye jaate hain, warna `capture()` ko command chhoot jayegi. Ye
    recording hi hai: memory me rehti hai, koi file nahi (privacy ka niyam).

    `threshold` = `config.VAD_THRESHOLD` se thoda **neeche** (0.8 hissa): is
    chhoti window me awaaz poore 30 ms chunk me bhi kamzor ho sakti hai.
    """
    stop = stop or _STOP
    seconds = config.COMMAND_ACK_PEEK_SECONDS if seconds is None else float(seconds)
    threshold = (config.VAD_THRESHOLD * 0.8 if threshold is None else float(threshold))
    deadline = time.monotonic() + seconds
    heard, peak = [], 0.0
    while time.monotonic() < deadline and not stop.is_set():
        try:
            heard.append(mic.chunks.get(timeout=0.02))
        except (queue.Empty, AttributeError):
            continue
        try:
            peak = max(peak, audio_mod.chunk_to_rms(heard[-1]))
        except Exception as exc:      # kharab chunk: chup-chaap aage badho
            log.warning("peek: RMS nahi mila: %s: %s", type(exc).__name__, exc)
    for chunk in heard:
        try:
            mic.chunks.put_nowait(chunk)
        except (queue.Full, AttributeError):
            break                       # queue bhar gayi - purana naya rehne do
    return bool(peak >= threshold and heard), round(peak, 4)


def capture(mic, stop=None) -> list:
    """VAD se ek command uthao. -> chunk list ya `None` (kuch suna hi nahi).

    `wake/utterance.py` ki hi window chalti hai (end-silence, min/max, wait) —
    is liye wake window ka control wahi rakha gaya hai, sirf raasta badla."""
    return utterance_mod.capture(mic, stop or _STOP)


async def _transcribe(chunks: list) -> str:
    audio = wav_mod.to_wav(utterance_mod.pcm(chunks))
    return await stt_mod.transcribe(audio, utterance_mod.duration_ms(chunks))


def to_text(chunks: list, stop=None) -> str:
    """Captured PCM -> text. `''` matlab samajh nahi aaya.

    STT guard yahin se aata hai (chhoti recording, khamoshi ke jaise phrases
    jaise "Thank you.", galat script) — wake ke liye koi alag guard nahi banaya,
    `voice/stt_guard.py` wahi chalta hai jo browser wale raaste par chalta hai.
    Net/brain ki galti par bhi `''` (caller `NOT_UNDERSTOOD` bolega)."""
    stop = stop or _STOP
    if stop.is_set():
        return ""
    try:
        text = asyncio.run(_transcribe(chunks))
    except stt_mod.SttError as exc:
        log.info("stt guard/natak: %s", exc)
        return ""
    except Exception as exc:
        log.error("stt crash: %s: %s", type(exc).__name__, exc)
        return ""
    log.info("command text: %r", text[:80])
    return text