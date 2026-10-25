"""PCM helpers — RMS, encode, aur energy VAD. Pure, koi mic nahi.

`wake/audio.py` inhe **re-export** karta hai, is liye production code aur test
 dono `audio.chunk_to_rms()` / `audio.Vad()` hi likhte rahenge (ek hi raasta).
Ye file 5-Oct ke split ka hissa hai — `audio.py` 200 cross kar gaya tha.

VAD ka logic bilkul saada: har chunk ka RMS nikalo. Agar threshold se upar hai
to "bol raha hai", warna "chup". `hangover` is liye hai ki beech me ek chhota
ruk na ho to recording kat na jaaye.

Test: `tests/test_wake.py` (RMS/encode/VAD) — bina sounddevice ke.
"""

import numpy as np

import config


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
    """float32 (-1..1) -> 16-bit little-endian PCM. Pure function.

    PortAudio WASAPI float32 deta hai, aur queue/StT int16 chahte hain — yahi
    beech ka pul hai."""
    clipped = np.clip(samples, -1.0, 1.0)
    return (clipped * 32767.0).astype("<i2").tobytes()


# int16 ka full scale. 99.9% = "clip ho raha hai" (mic tez / AGC utha hua).
CLIP_LEVEL = 32767 * 0.999


def quality(chunks) -> tuple:
    """Captured audio ka haal -> `(peak_rms, clip_pct)`.

    Sirf **do number** — audio kahin save nahi hoti (privacy ka pakkaura).
    Log me isi se pata chalta hai ki mic tez hai (clip %) ya bahut dheere
    (peak RMS kam). S-1 audit me pata chala tha ki asli problem yahi thi:
    RMS 0.5+ matlab clip, aur Whisper aise audio me koi bhasha bana deta hai.

    Pure function — `None`/khaali list par `(0.0, 0.0)`, test me bina mic ke."""
    peak, total, clipped = 0.0, 0, 0
    for chunk in chunks or []:
        if not chunk:
            continue
        peak = max(peak, chunk_to_rms(chunk))
        samples = np.frombuffer(chunk, dtype="<i2")
        if not samples.size:
            continue
        total += samples.size
        clipped += int(np.count_nonzero(
            np.abs(samples.astype(np.int32)) >= CLIP_LEVEL))
    pct = round(100.0 * clipped / total, 2) if total else 0.0
    return round(peak, 4), pct


class RmsGain:
    """Simple RMS-based gain: quiet speech → gain up, loud → down. Khamoshi par
    bilkul touch nahi karta (battery)."""

    def __init__(self, target_rms: float = 0.08, max_gain: float = 12.0,
                 min_gain: float = 0.4, attack: float = 0.05, release: float = 0.01,
                 speech_gate: float = 1.5):
        self.target_rms = float(target_rms)
        self.max_gain = float(max_gain)
        self.min_gain = float(min_gain)
        self.attack = float(attack)
        self.release = float(release)
        self.speech_gate = float(speech_gate)
        self.env = 0.001
        self.g = 1.0

    def apply(self, block: np.ndarray) -> np.ndarray:
        x = np.asarray(block, dtype=np.float32)
        if x.size == 0:
            return x
        rms = float(np.sqrt(np.mean(x * x) + 1e-12))
        if rms > self.env:
            self.env = self.env + self.attack * (rms - self.env)
        else:
            self.env = self.env + self.release * (rms - self.env)
        if self.env < 0.001 * self.speech_gate:
            self.g = 1.0
            return x
        want = self.target_rms / max(self.env, 1e-6)
        g = min(self.max_gain, max(self.min_gain, want))
        if g > self.g:
            self.g += self.attack * (g - self.g)
        else:
            self.g += self.release * (g - self.g)
        return np.clip(x * self.g, -1.0, 1.0).astype(np.float32)


class AutoGain(RmsGain):
    pass


class FixedGain:
    """`JARVIS_WAKE_GAIN=4` jaisa fixed gain — debug/compare ke liye."""

    def __init__(self, factor: float = 1.0):
        self.factor = float(factor)
        self.applied = self.factor

    def apply(self, block: np.ndarray) -> np.ndarray:
        data = np.asarray(block, dtype=np.float32)
        if data.size == 0 or self.factor == 1.0:
            return data
        return np.clip(data * self.factor, -1.0, 1.0).astype(np.float32)


class Vad:
    """Energy VAD. `push()` har chunk ke saath: ab bol rahe ho ya nahi.

    - `True`  = user bol raha hai
    - `False` = khamoshi
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