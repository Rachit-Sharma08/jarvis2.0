"""Mic ka ek hi owner — `sounddevice` se 16 kHz mono, energy VAD ke saath.

Do chizein yahan hain, aur sirf yahan:

1. `MicSource` — hamesha chalti hai (duty cycle nahi, AGENTS.md ka niyam).
   Har 30 ms ka chunk `queue.Queue` me daalti hai.
2. `Utterance` — VAD se pata lagata hai ki user bol raha hai ya chup. Wake worker
   isse se audio *uthata* hai, is liye recording ka control worker ka hai.

VAD ka logic bilkul saada: har chunk ka RMS nikalo. Agar threshold se upar hai
to "bol raha hai", warna "chup". `HANGOVER` is liye hai ki beech me ek chhota
ruk na ho to recording kat na jaaye.

Is file me kuch bhi `if __name__` nahi — test me `chunk_to_rms()` aur
`Vad.should_stop()` pure functions se test hote hain.
"""

import queue
import threading

import numpy as np

import config
from log_setup import get_logger

log = get_logger("wake_audio")

BLOCK_SECONDS = config.BLOCK_MS / 1000.0
MAX_QUEUE_BLOCKS = 400          # ~12 s. Zyada pile na ho, warna mic latency.
VOICE = "wake_input"


class MicUnavailable(Exception):
    """Mic nahi khul paya (permission/device/device busy). Reason user ko dikhana hai."""


def chunk_to_rms(chunk: bytes) -> float:
    """Raw 16-bit little-endian PCM -> RMS (0..1). Pure function, test me yahi."""
    if not chunk:
        return 0.0
    samples = np.frombuffer(chunk, dtype="<i2")
    if samples.size == 0:
        return 0.0
    magnitude = np.sqrt(np.mean(np.square(samples.astype(np.float32))))
    return float(magnitude / 32768.0)


def encode(samples: np.ndarray) -> bytes:
    """float32 (-1..1) -> 16-bit little-endian PCM. Pure function."""
    clipped = np.clip(samples, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()


class Vad:
    """Energy VAD. `push()` har chunk ke saath: ab bol rahe ho ya nahi.

    - `voice` = True  → user bol raha hai
    - `voice` = False → khamoshi
    - `hangover` blocks tak pehle ki awaaz pehle maani jaati hai
    """

    def __init__(self, threshold: float = None, hangover_blocks: int = None):
        self.threshold = config.VAD_THRESHOLD if threshold is None else float(threshold)
        self.hangover = (config.VAD_HANGOVER_BLOCKS
                         if hangover_blocks is None else int(hangover_blocks))
        self._hot = 0

    def loud(self, rms: float) -> bool:
        return rms >= self.threshold

    def push(self, rms: float) -> bool:
        """Chunk ka RMS do. -> ab bol rahe ho?"""
        if self.loud(rms):
            self._hot = self.hangover
            return True
        if self._hot > 0:
            self._hot -= 1
            return True
        return False

    def speaking(self) -> bool:
        return self._hot > 0

    def reset(self) -> None:
        self._hot = 0


class MicSource:
    """`sounddevice.InputStream` ka wrapper. Ek thread, ek hi owner.

    `start()` mic kholta hai aur background thread me chunks queue me daalta hai.
    `stop()` band karta hai. Daalna kabhi crash nahi karta — mic band ho to
    sirf `self.alive = False`.
    """

    def __init__(self, device=None, rate: int = None, blocksize: int = None):
        self.rate = config.SAMPLE_RATE if rate is None else int(rate)
        self.blocksize = int(self.rate * BLOCK_SECONDS) if blocksize is None else int(blocksize)
        self.device = config.INPUT_DEVICE if device is None else device
        self.chunks: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_BLOCKS)
        self.alive = False
        self.error = ""
        self.dropped = 0
        self._stream = None
        self._thread = None
        self._stop = threading.Event()

    # ---- zindagi ----
    def start(self) -> bool:
        import sounddevice as sd       # import late: app startup tez rahe

        if self.alive:
            return True
        try:
            self._stream = sd.InputStream(
                samplerate=self.rate, blocksize=self.blocksize, device=self.device,
                dtype="int16", channels=config.CHANNELS,
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
        self._thread = threading.Thread(target=self._pump, name=VOICE, daemon=True)
        self._thread.start()
        log.info("mic khula: rate=%d block=%dms device=%s", self.rate,
                 self.blocksize, self.device or "default")
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
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        log.info("mic band")

    # ---- andar ----
    def _pump(self) -> None:
        """Stream se chunk uthakar queue me daalo. Thread marte bhi mic band.

        `read()` **blocking** hai — pura chunk aane tak ruk jaata hai. Is liye
        uske baad koi `sleep()` nahi: pehle yahan `sd.sleep(30ms)` tha, jo
        chunk ko ~43 ms me la raha tha (30 + 30). Do nuksan — CPU dobara
        jaagna, aur `utterance.capture()` chunk *ginti* par chalti hai, to
        chuppi ki "0.9 s" window asli me 1.4 s ho jaati thi (jawab late).
        """
        while not self._stop.is_set():
            try:
                data, _overflow = self._stream.read(self.blocksize)
            except Exception as exc:
                self.error = f"{type(exc).__name__}: {exc}"
                log.error("mic read fail: %s", self.error)
                self.alive = False
                return
            raw = data.tobytes()
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