"""Wake ke baad ka command: mic se utha lo, VAD se sahi waqt par band karo.

Step 1 worker sirf wake shabd ("Jarvis") sunta tha. Step 2 ka pehla hissa yahi hai — wake
ke baad thodi der aur suno aur jo user bola wahi raw PCM de do (STT usi ko
Groq par bhejega).

Teen window `config_wake.py` se aati hain:

- **Pre-roll** — mic chunk queue me pehle se maujood hota hai. "Jarvis, WhatsApp
  kholo" ek saath bola ho to "WhatsApp" bhi pakadna chahiye, is liye shuru hone
  se thoda pehle ka buffer bhi jodte hain.
- **End silence** — user chup ho gaya to command khatam. Har 30 ms me silence ka
  hisaab.
- **Wait** — pehla shabd `COMMAND_WAIT_SECONDS` me aaya hi nahi to `None`
  (warna mic khamoshi me chhatka khaaye rehte).
- **Max seconds** — safety: user bharta rahe to bhi 8 second me band.

`capture()` mic se sirf `chunks` queue (aur `alive`) maangti hai — asli
`MicSource` se bhi, test ke fake se bhi. Koi naya `InputStream` nahi khulta.

Kuch na mile to `None` (user ne kuch nahi kaha) — `config.NOT_HEARD` bolna
caller ka kaam hai.
"""

import queue
from collections import deque

import config
from log_setup import get_logger
from wake import audio as audio_mod

log = get_logger("wake_utterance")


def _blocks(seconds: float, block: float) -> int:
    return max(1, int(round(float(seconds) / block)))


def capture(mic, stop=None) -> list:
    """Mic se ek command uthakar list of raw PCM chunks. -> `[]` ya `None`.

    `mic` = `wake/audio.py` ka `MicSource` (ya test ka fake) — sirf `.chunks`
    queue aur `.alive` chahiye. `stop` = `threading.Event` (app band ho raha ho
    tab turant lautna hai).
    """
    block = audio_mod.BLOCK_SECONDS
    pre_n = _blocks(config.COMMAND_PRE_ROLL_SECONDS, block)
    max_n = _blocks(config.COMMAND_MAX_SECONDS, block)
    quiet_n = _blocks(config.COMMAND_END_SILENCE_SECONDS, block)
    min_n = _blocks(config.COMMAND_MIN_SECONDS, block)
    hang_n = _blocks(config.COMMAND_HANGOVER_SECONDS, block)
    wait_seconds = float(config.COMMAND_WAIT_SECONDS)

    vad = audio_mod.Vad(hangover_blocks=hang_n)
    preroll = deque(maxlen=pre_n)
    collected = None
    spoken = 0
    quiet = 0
    seen = 0
    empty = 0

    while seen < max_n:
        if stop is not None and stop.is_set():
            return None
        try:
            raw = mic.chunks.get(timeout=0.2)
        except queue.Empty:
            empty += 1
            if collected is not None:
                break                     # sunna band, jo mila wahi poora
            if not getattr(mic, "alive", True):
                return None
            if empty * 0.2 >= wait_seconds:
                break                     # user ne bolna hi shuru nahi kiya
            continue
        if not getattr(mic, "alive", True):
            return None if collected is None else collected
        seen += 1
        loud = vad.push(audio_mod.chunk_to_rms(raw))
        if collected is None:
            preroll.append(raw)
            if not loud:
                continue                  # abhi tak koi awaaz nahi
            collected = list(preroll)
            spoken = 1
            quiet = 0
            continue
        collected.append(raw)
        if loud:
            spoken += 1
        quiet = 0 if loud else quiet + 1
        if quiet >= quiet_n:
            break

    # Sirf **awaaz** ginti hai — aakhir ki khamoshi ko "0.6s bola" na samjho.
    if collected is None or spoken < min_n:
        log.info("command capture: chhota (%d chunk awaaz = %dms)", spoken, spoken * 30)
        return None
    log.info("command capture: %d chunk = %dms", len(collected), duration_ms(collected))
    return collected


def duration_ms(chunks: list) -> int:
    """Chunk list ki lambai millisecond me (STT guard ke liye)."""
    return int(len(chunks) * audio_mod.BLOCK_SECONDS * 1000)


def pcm(chunks: list) -> bytes:
    """Chunk list ko ek jodi PCM bytes me mila do."""
    return b"".join(chunks)


def is_stop_command(text: str) -> bool:
    """'ruk jao' / 'band karo' jaisa command? Step 2.5 ke liye taiyaar."""
    low = (text or "").strip().lower()
    return any(word in low for word in config.STOP_WORD)