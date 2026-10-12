"""Mic ka ek hi owner — `sounddevice` se 16 kHz mono, energy VAD ke saath.

1. `MicSource` — hamesha chalti hai (duty cycle nahi, AGENTS.md ka niyam).
   Queue me **16 kHz int16 PCM** ke 30 ms blocks jaate hain.
2. `Vad` / `chunk_to_rms()` — VAD ka faisla (pure, test inhi se).

**5-Oct ka sabse bada bug: MME ka mic kachra deta hai.** MME par peak sirf
-19..-52 dB aata tha aur Vosk `"hey"`/`"huh"` sunta tha — 0 jarvis-hit. **WASAPI
+ callback API** par peak **-7.6 dB** aur wahi grammar `"hello jarvis"` pakad
leti thi. Is liye ab mic WASAPI se khulta hai (`pick_input_device`), capture
**native rate** par hota hai (48 kHz - 16 kHz par PortAudio `Invalid sample
rate` deta hai), aur `wake/resample.py` se 16 kHz par aata hai.

Is file me kuch bhi `if __name__` nahi — test me `chunk_to_rms()`, `encode()`,
`Vad`, `pick_input_device()` aur `wake/resample.py` pure functions se test hote
hain (`tests/test_wake_resample.py`).
"""

import queue
import threading

import numpy as np

import config
from log_setup import get_logger
from wake import resample
from wake.pcm import (AutoGain, FixedGain, RmsGain, Vad, chunk_to_rms,
                      encode, quality)   # noqa: F401 (re-export)

log = get_logger("wake_audio")

BLOCK_SECONDS = config.BLOCK_MS / 1000.0
MAX_QUEUE_BLOCKS = 400          # ~12 s. Zyada pile na ho, warna mic latency.
VOICE = "wake_input"


class MicUnavailable(Exception):
    """Mic nahi khul paya (permission/device/device busy). Reason user ko dikhana hai."""


class MicSource:
    """`sounddevice.InputStream` ka wrapper, **callback** API par (5-Oct).

    Do kaam yahin hote hain:
    1. mic WASAPI se kholna (`pick_input_device`) - MME se sirf kachra aata hai
    2. device ke native rate (48 kHz) ko `config.SAMPLE_RATE` (16 kHz) par
       laana - `wake/resample.py`, phir 30 ms ke blocks

    PortAudio apne thread se `self._on_audio` ko bulata hai; wo sirf array
    todta hai (kaam nahi karta). `start()` mic kholta hai, `stop()` band karta
    hai. Band karte waqt koi galti aaye to chup-chaap daba dete hain.
    """

    def __init__(self, device=None, rate: int = None, blocksize: int = None):
        self.rate = config.SAMPLE_RATE if rate is None else int(rate)
        self.blocksize = int(self.rate * BLOCK_SECONDS) if blocksize is None else int(blocksize)
        self.device = config.INPUT_DEVICE if device is None else device
        self.input_rate = self.rate
        self.chunks: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_BLOCKS)
        self.alive = False
        self.error = ""
        self.dropped = 0
        self._stream = None
        self._stop = threading.Event()
        self._decimator = resample.Decimator(1)
        self._blocker = resample.Blocker(self.blocksize)
        self._gain = _make_gain()

    # ---- zindagi ----
    def start(self) -> bool:
        import sounddevice as sd       # import late: app startup tez rahe

        if self.alive:
            return True
        device = pick_input_device(sd, self.device)
        try:
            self.input_rate = _native_rate(sd, device)
            self._decimator = resample.Decimator(
                resample.ratio_for(self.input_rate, self.rate))
            self._blocker = resample.Blocker(self.blocksize)
            self._stream = sd.InputStream(
                samplerate=self.input_rate, blocksize=0, device=device,
                dtype="float32", channels=config.CHANNELS,
                callback=self._on_audio,
            )
            self._stream.start()
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            log.error("mic nahi khula: %s | PortAudio 'MME error 1' ya "
                      "'device busy' = mic kisi aur app ne pakda hua hai "
                      "(Chrome/Teams/OBS band karke dubara kholo)", self.error)
            raise MicUnavailable(self.error) from exc
        self._stop.clear()
        self.alive = True
        log.info("mic khula: %s in=%d out=%d block=%dms device=%s",
                 hostapi_name(sd, device), self.input_rate, self.rate,
                 int(self.blocksize * 1000 / self.rate), device if device is not None
                 else "default")
        return True

    def stop(self) -> None:
        self._stop.set()
        stream = self._stream
        self._stream = None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception as exc:      # band karte waqt galti ko daba do
                log.warning("mic band karte waqt: %s: %s", type(exc).__name__, exc)
        self.alive = False
        log.info("mic band")

    # ---- PortAudio callback ----
    def _on_audio(self, indata, frames, time_info, status) -> None:
        """Sirf array todna hai - yahan koi kaam nahi, warna PortAudio ka thread
        atak jaata hai. PortAudio float32 deta hai, queue ko int16 chahiye."""
        if status:
            log.debug("mic status: %s", status)
        try:
            samples = indata[:, 0]
            if self._gain is not None:
                samples = self._gain.apply(samples)
            samples = self._decimator.feed(samples)
            for block in self._blocker.feed(samples):
                self._push(encode(block))
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            log.error("mic callback fail: %s", self.error)
            self.alive = False

    def _push(self, raw: bytes) -> None:
        try:
            self.chunks.put_nowait(raw)
        except queue.Full:
            # Consumer (Vosk) peeche reh gaya. Naya chunk sabse important
            # hai — purana hatao taaki live raha rahe (lag na paye).
            try:
                self.chunks.get_nowait()
                self.chunks.put_nowait(raw)
                self.dropped += 1
            except queue.Empty:
                pass


def _make_gain():
    """`PRABH_WAKE_GAIN` se gain: `auto` (default) | number | `off`.

    `auto` = `wake/pcm.py` ka `AutoGain` (khamoshi nahi chhedta). Number = fixed
    gain. `off` = `None` — mic jaisa hai waisa jaata hai. Baaki hisse
    (`config_wake.INPUT_GAIN`) me se aata hai, yahan koi magic number nahi."""
    mode = config.INPUT_GAIN
    if mode in ("off", "0", "none", "false", ""):
        return None
    try:
        fixed = float(mode)
    except ValueError:
        return RmsGain(target_rms=config.INPUT_GAIN_TARGET, max_gain=config.INPUT_GAIN_MAX)
    return FixedGain(fixed)


def pick_input_device(sd, wanted=None):
    """WASAPI ka mic chuno — MME se sirf kachra aata hai (5-Oct ka pehla bug).

    `wanted` (`PRABH_WAKE_MIC`) diya ho to use-as-is (user ka faisla). warna
    WASAPI host API ka default capture device. Kuch na mile to `None` (PortAudio
    apna default lega) — crash nahi karenge.
    """
    if wanted not in (None, ""):
        return wanted
    try:
        for api in sd.query_hostapis():
            if config.INPUT_HOSTAPI in str(api["name"]).upper():
                index = api["default_input_device"]
                if index is not None and int(index) >= 0:
                    return int(index)
    except Exception as exc:       # enumerate na hua to default par ghisna hai
        log.warning("host api nahi mila: %s: %s", type(exc).__name__, exc)
    return None


def hostapi_name(sd, device) -> str:
    """Log ke liye: device kis host API ka hai (`MME`/`WASAPI`/...)."""
    try:
        return str(sd.query_devices(device, kind="input")["hostapi"])
    except Exception:
        return "?"


def _native_rate(sd, device) -> int:
    """Device ka apna capture rate. WASAPI 48 kHz maangta hai — 16 kHz par
    PortAudio `Invalid sample rate` deta hai (5-Oct)."""
    try:
        info = sd.query_devices(device, kind="input")
        return int(info["default_samplerate"]) or config.SAMPLE_RATE
    except Exception:
        return config.SAMPLE_RATE