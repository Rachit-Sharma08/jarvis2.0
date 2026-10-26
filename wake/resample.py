"""Mic ka native rate -> 16 kHz, aur fixed-size blocks. Sirf arrays - audio nahi.

5-Oct ka asli bug: WASAPI mic **48 kHz native** hai, aur PortAudio use 16 kHz
par kholne se `Invalid sample rate` bolta hai. Is liye capture **device ke native
rate** par karte hain aur yahan 48k -> 16k (3:1) karte hain.

`Decimator` har 3 sample ka **mean** leta hai - wo ek box low-pass bhi hai, is
liye aliasing (5 kHz+ ki awaaz 16 kHz par fold hoti hai) kam ho jaati hai. isi
record par Vosk ne `"hello jarvis"` pehchan liya tha.

Is file me mic, thread ya `sounddevice` nahi hai - sirf `numpy`. Test inhe
bina sounddevice ke chalate hain (`tests/test_wake_resample.py`).
"""

import numpy as np

RATIO = 3


class Decimator:
    """N:1 decimation. `feed()` me jitna mile utna array, bacha hua agli call me."""

    def __init__(self, ratio: int = RATIO):
        self.ratio = max(1, int(ratio))
        self._tail = np.zeros(0, dtype=np.float32)

    def feed(self, samples) -> np.ndarray:
        data = np.concatenate([self._tail, np.asarray(samples, dtype=np.float32)])
        usable = (data.size // self.ratio) * self.ratio
        if usable == 0:
            self._tail = data
            return np.zeros(0, dtype=np.float32)
        out = data[:usable].reshape(-1, self.ratio).mean(axis=1)
        self._tail = data[usable:]
        return out.astype(np.float32)


class Blocker:
    """Bada array -> fixed-size blocks (30 ms ka list). Bacha hua yaad rakhta hai."""

    def __init__(self, size: int):
        self.size = max(1, int(size))
        self._tail = np.zeros(0, dtype=np.float32)

    def feed(self, samples) -> list:
        data = np.concatenate([self._tail, np.asarray(samples, dtype=np.float32)])
        count = data.size // self.size
        out = [data[i * self.size:(i + 1) * self.size] for i in range(count)]
        self._tail = data[count * self.size:]
        return out

    def pending(self) -> int:
        return int(self._tail.size)


class Fractional:
    """Kisi bhi rate -> 16 kHz. Linear interpolation (speech ke liye kaafi).

    `Decimator` sirf poore ratio (48k/3) par chalta tha; 44.1 kHz par
    `ratio_for` 1 deta tha = kuch nahi, aur awaaz 2.75x tez/slow ho jaati thi.
    Ye class usi gap ko bharta hai. Linear interpolation aliasing nahi rokta
    (8 kHz se upar ka hissa fold hota hai) — speech ke liye ye theek hai.
    """

    def __init__(self, input_rate: int, output_rate: int = 16000):
        self.step = max(1.0, float(input_rate) / float(output_rate))
        self._tail = np.zeros(0, dtype=np.float32)
        self._pos = 0.0          # `_tail` ke coordinates me agli sample ki jagah

    def feed(self, samples) -> np.ndarray:
        data = np.concatenate([self._tail, np.asarray(samples, dtype=np.float32)])
        if data.size < 2:
            self._tail = data
            return np.zeros(0, dtype=np.float32)
        positions = np.arange(self._pos, data.size - 1, self.step)
        if positions.size == 0:
            self._tail = data
            return np.zeros(0, dtype=np.float32)
        out = np.interp(positions, np.arange(data.size), data).astype(np.float32)
        keep = int(np.floor(positions[-1]))
        self._tail = data[keep:]
        self._pos = float(positions[-1] - keep) + self.step
        return out


def ratio_for(input_rate: int, output_rate: int = 16000) -> int:
    """48k -> 16k = 3. Poora divide na ho (ya rate chhota ho) to 1 = kuch nahi."""
    try:
        high, low = int(input_rate), int(output_rate)
    except (TypeError, ValueError):
        return 1
    if high <= low or high % low:
        return 1
    return high // low


def make(input_rate, output_rate: int = 16000):
    """Rate pair ke liye sahi resampler: poora ratio -> `Decimator` (fast)."""
    try:
        high, low = int(input_rate), int(output_rate)
    except (TypeError, ValueError):
        return Decimator(1)
    if high == low:
        return Decimator(1)
    ratio = ratio_for(high, low)
    if ratio > 1:
        return Decimator(ratio)
    return Fractional(high, low)