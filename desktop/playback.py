"""Speaker ka ek raasta — TTS bytes ko bajao (Phase 5 Step 2).

Browser ka purana `ui/speaker.js` sirf HUD ke liye bacha hai. Jarvis ki apni
awaaz (wake ke baad "Ji, boliye", aur brain ke jawab) Python me yahin se aati
hai — `desktop/playback.py`.

Teen kaam, sab isi file me:

1. `decode(bytes)` — mp3/wav/ogg ko 16-bit mono PCM me badal do.
   `miniaudio.decode` memory buffer leta hai. **Caveat:** `decode_file` sirf
   filename leta hai, aur bytes dene par wo poora buffer ko `FileNotFoundError`
   ke message me daal deta hai — yaani terminal par pura audio dump. Is liye
   yahan sirf `decode()` call hota hai.
2. `play(bytes)` — us PCM ko `sounddevice` se suna do.
3. `say(text)` — `voice/tts.py` se awaaz bana kar `play()` se chala do.

**TTS ka ek hi raasta** `voice/tts.py` hai (AGENTS.md) — yahan koi provider
nahi chuna jaata. Ye function **thread** se call hota hai (wake worker, tray),
is liye async TTS call `asyncio.run` se jaata hai.

Crash kabhi upar na aaye: har galti `log` me, return me `0`. Wake thread ek
baar phat gaya to mic hi sunna chhod dega.

Test me `miniaudio` aur `sounddevice` dono fake hain (`_modules` patch karta
hai) — asli speaker kabhi nahi bajti. Asli check ke liye:
`python -m desktop.playback --list` aur `python -m desktop.playback --say "Ji, boliye"`.
"""

import asyncio
import sys

import numpy as np

import config
from log_setup import get_logger

log = get_logger("playback")


class PlaybackError(Exception):
    """Awaz nahi ban/suni ja saki. Hamesha message me sirf error ka naam."""


def _modules() -> tuple:
    """(miniaudio, sounddevice) — import late, jaise `wake/audio.py` karta hai.

    App startup tez rahe is liye dono sirf jab sach me bajana ho tab load hote
    hain. Test bhi yahi patch karta hai.
    """
    import miniaudio
    import sounddevice as sd

    return miniaudio, sd


def _output_rows(found) -> list:
    """`query_devices()` ki list me se sirf output wale -> [(index, name), ...]."""
    rows = []
    for dev in found:
        try:
            if int(dev["max_output_channels"]) > 0:
                rows.append((int(dev["index"]), str(dev["name"])))
        except Exception:               # koi ajeeb entry — chhod do
            continue
    return rows


def available() -> tuple:
    """Speaker + decoder dono hain? -> (bool, reason). Reason UI me dikhta hai."""
    try:
        _mini, sd = _modules()
        found = sd.query_devices()
    except Exception as exc:
        return False, "speaker check fail: %s" % type(exc).__name__
    if not _output_rows(found):
        return False, "koi output device nahi mila"
    return True, ""


def decode(audio: bytes, rate: int = None) -> tuple:
    """TTS bytes -> (numpy int16 array, sample_rate).

    `rate` nahi diya to `config.OUTPUT_RATE`. MP3/WAV/OGG — jo bhi
    `voice/tts.py` ke kisi provider ne diya, sab yahan chalna chahiye.
    """
    rate = int(rate or config.OUTPUT_RATE)
    if not audio:
        raise PlaybackError("Boli hui awaaz khaali aayi.")
    miniaudio, _ = _modules()
    try:
        decoded = miniaudio.decode(
            bytes(audio),
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=1,
            sample_rate=rate,
        )
    except Exception as exc:
        raise PlaybackError("Audio samajh nahi aaya (%s)." % type(exc).__name__) from exc

    # `decoded.samples` miniaudio ka apna int16 buffer hai. `np.asarray` (na ki
    # `bytes()`) is liye — wapas raw bytes banane par wahi list/bhar wala buffer
    # banega, jo int16 se seedha padha ja sakta hai.
    samples = np.asarray(decoded.samples, dtype="<i2")
    if samples.size == 0:
        raise PlaybackError("Audio me koi awaaz nahi mili.")
    return samples, int(decoded.sample_rate)


def play(audio: bytes, rate: int = None) -> int:
    """Raw TTS bytes bajao. -> kitni der lagi (ms). Galti par `PlaybackError`."""
    samples, sample_rate = decode(audio, rate)
    _, sd = _modules()
    try:
        sd.play(samples, samplerate=sample_rate, device=config.OUTPUT_DEVICE,
                blocking=True)
    except Exception as exc:
        raise PlaybackError("Speaker nahi chal paya (%s)." % type(exc).__name__) from exc
    ms = int(len(samples) * 1000 / sample_rate)
    log.info("speaker: %dms (%d samples @ %d Hz)", ms, samples.size, sample_rate)
    return ms


def beep(freq: int = None, ms: int = None) -> int:
    """Chhota beep - "Ji, boliye" ki jagah (woh ~5 s leti thi).

    Wahi raasta: `numpy` sine + `_modules()` ka `sounddevice`. Koi naya package
    ya nayi file nahi. -> kitne ms baja (0 = nahi baja).
    """
    freq, ms = int(freq or config.ACK_BEEP_HZ), int(ms or config.ACK_BEEP_MS)
    rate = int(config.OUTPUT_RATE)
    wave = np.sin(2 * np.pi * freq * np.arange(int(rate * ms / 1000)) / rate)
    tone = (wave * 8000).astype("<i2")          # halka - dheere se aaye jaaye
    _, sd = _modules()
    try:
        sd.play(tone, samplerate=rate, device=config.OUTPUT_DEVICE, blocking=True)
    except Exception as exc:
        log.warning("beep nahi baja: %s: %s", type(exc).__name__, exc)
        return 0
    log.info("beep: %dHz %dms", freq, ms)
    return ms


def say(text: str, mode: str = None, rate: int = None) -> int:
    """Text bol kar suno. -> kitni der lagi (ms); `0` matlab nahi bola.

    Thread se call karo (wake worker / tray). Koi bhi galti upar nahi aati —
    sirf log, warna wake thread toot jayega.

    **Cache:** `tts.speak_cached()` wala raasta — constant text ("Ji, boliye",
    "confirm kijiye") pehli baar ban-ta hai, phir memory se (har baar ~1.5 s
    bachta hai). Chat ka jawab bhi yahin se jaata hai, par wo unique hai is liye
    cache khud hit nahi hota. Yahan naya provider chain **kabhi** mat likho.
    """
    from voice import tts

    mode = mode or config.DEFAULT_MODE
    limit = float(config.PLAYBACK_TIMEOUT_SECONDS)
    try:
        audio, provider = asyncio.run(
            asyncio.wait_for(tts.speak_cached(text, mode), limit)
        )
    except asyncio.TimeoutError:
        log.error("tts timeout (%ds)", int(limit))
        return 0
    except Exception as exc:
        # TtsError ka message provider ki wajah batata hai (key/limit) — wo
        # user ke liye nahi, log ke liye hai. UI ko sirf "nahi bola" dikhega.
        log.warning("tts nahi hua: %s: %s", type(exc).__name__, exc)
        return 0
    log.info("speak: provider=%s mode=%s chars=%d bytes=%d",
             provider, mode, len(text or ""), len(audio))
    try:
        return play(audio, rate)
    except PlaybackError as exc:
        log.error("playback nahi hua: %s", exc)
        return 0
