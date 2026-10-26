"""WASAPI + resample ka pure test — 5-Oct ka mic fix. Asli mic/model kabhi nahi.

Do baatein pakdi jaati hain:
1. `wake/resample.py` 48k -> 16k sahi todta hai (blocks + bacha hua sample).
2. `wake/audio.py` WASAPI device chunta hai aur MME par nahi jaata.

Bina `sounddevice` ke chal jaata hai — `pick_input_device` ko ek nakli `sd`
deta hoon (`FakeSd`). Isi PC par live proof: MME par Vosk `"hey"` sunta tha
(0 jarvis), WASAPI par `"hello jarvis"`.
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from wake import audio as audio_mod
from wake import pcm as pcm_mod
from wake import resample

from tests.pcmhelp import FAILED, check  # noqa: E402  (shared list - dono files)


class FakeSd:
    """`sounddevice` ka nakla - sirf do function jo `pick_input_device` use karta hai."""

    def __init__(self, apis, query_error=False):
        self.apis = apis
        self.query_error = query_error

    def query_hostapis(self):
        if self.query_error:
            raise RuntimeError("PortAudio nahi mila")
        return self.apis


def api(name, default_input):
    return {"name": name, "default_input_device": default_input}


def test_ratio():
    check("48k -> 16k", resample.ratio_for(48000, 16000), 3)
    check("16k -> 16k (kuch nahi)", resample.ratio_for(16000, 16000), 1)
    check("44.1k -> 16k (poora divide nahi)", resample.ratio_for(44100, 16000), 1)
    check("8k -> 16k (chhota)", resample.ratio_for(8000, 16000), 1)
    check("bad input", resample.ratio_for("abc", 16000), 1)
    check("config SAMPLE_RATE", resample.ratio_for(48000, config.SAMPLE_RATE), 3)


def test_decimator():
    d = resample.Decimator(3)
    out = d.feed(np.ones(9, dtype=np.float32))
    check("9 sample -> 3", out.size, 3)
    check("mean sahi", round(float(out[0]), 4), 1.0)
    check("bacha hua 0", d.feed(np.ones(5, dtype=np.float32)).size, 1)
    check("ratio 1 = as-is", resample.Decimator(1).feed(np.ones(4, "float32")).size, 4)
    check("chhota input", resample.Decimator(3).feed(np.ones(2, "float32")).size, 0)
    loud = resample.Decimator(3).feed(np.full(6, 0.5, dtype=np.float32))
    check("0.5 ka mean", round(float(loud[0]), 4), 0.5)
    d2 = resample.Decimator(3)
    total = 0
    for _ in range(4):                      # chunk-chunk feed: total sahi hona chahiye
        total += d2.feed(np.ones(480, dtype=np.float32)).size
    check("4x480 -> 640", total, 640)


def test_fractional():
    """44.1k -> 16k: pehle `ratio_for` 1 deta tha = kuch nahi (awaaz 2.75x tez)."""
    rate, secs, hz = 44100, 1.0, 440.0
    t = np.arange(int(rate * secs)) / rate
    sine = np.sin(2 * np.pi * hz * t).astype(np.float32)
    out = resample.Fractional(rate, 16000).feed(sine)
    check("1s @44.1k -> ~16000 sample", abs(out.size - 16000) <= 2, True)
    # Frequency bani rahe: 440 Hz sine ke zero-crossings 1 s me ~880.
    crossings = int(np.sum(np.diff(np.signbit(out))))
    check("440 Hz bani rahi", abs(crossings - 880) <= 8, True)

    # Chunk-chunk feed par total wahi (tail/position sambhal raha hai).
    f = resample.Fractional(rate, 16000)
    total = sum(f.feed(sine[i:i + 441]).size for i in range(0, sine.size, 441))
    check("chunk-chunk bhi ~16000", abs(total - 16000) <= 2, True)
    check("khaali input", resample.Fractional(rate, 16000).feed(
        np.zeros(0, dtype=np.float32)).size, 0)


def test_make():
    check("48k = Decimator(3)", type(resample.make(48000)).__name__, "Decimator")
    check("48k ratio", resample.make(48000).ratio, 3)
    check("44.1k = Fractional", type(resample.make(44100)).__name__, "Fractional")
    check("16k = passthrough", resample.make(16000).ratio, 1)
    check("bad input = passthrough", resample.make("abc").ratio, 1)


def test_blocker():
    b = resample.Blocker(480)
    check("1440 -> 3 blocks", len(b.feed(np.ones(1440, dtype=np.float32))), 3)
    check("bacha hua", b.pending(), 0)
    b2 = resample.Blocker(480)
    check("1000 -> 2 blocks", len(b2.feed(np.ones(1000, dtype=np.float32))), 2)
    check("40 bacha", b2.pending(), 40)
    check("480 bharne se pehle", len(b2.feed(np.ones(440, dtype=np.float32))), 1)
    check("size 0 se koi crash nahi", len(resample.Blocker(0).feed(np.ones(5, "float32"))), 5)


def test_pick_device_prefers_wasapi():
    sd = FakeSd([api("MME", 1), api("Windows DirectSound", 4),
                 api("Windows WASAPI", 9), api("Windows WDM-KS", 17)])
    check("WASAPI chuna", audio_mod.pick_input_device(sd), 9)
    check("MME khaali hai", audio_mod.pick_input_device(FakeSd([api("MME", 1)])), None)
    check("WDM-KS sirf", audio_mod.pick_input_device(
        FakeSd([api("Windows WDM-KS", 17)])), None)
    check("hostapi list fail", audio_mod.pick_input_device(
        FakeSd([], query_error=True)), None)


def test_pick_device_respects_env():
    """`JARVIS_WAKE_MIC` diya ho to user ka device - host api se pehle."""
    sd = FakeSd([api("Windows WASAPI", 9)])
    check("number 3", audio_mod.pick_input_device(sd, 3), 3)
    check("naam", audio_mod.pick_input_device(sd, "Microphone Array"), "Microphone Array")
    check("khaali env = WASAPI", audio_mod.pick_input_device(sd, ""), 9)
    check("config WASAPI hai", config.INPUT_HOSTAPI, "WASAPI")


def test_audio_reexports():
    """`audio.chunk_to_rms`/`encode`/`Vad` ka raasta nahi toota (re-export)."""
    check("rms re-export", audio_mod.chunk_to_rms(audio_mod.encode(
        np.full(100, 0.5, dtype=np.float32))) > 0.4, True)
    check("Vad re-export", audio_mod.Vad(threshold=0.01, hangover_blocks=2).push(0.5), True)
    check("encode 32767", int(np.frombuffer(
        audio_mod.encode(np.array([9.0], "float32")), "<i2")[0]), 32767)


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("FAIL:", FAILED if FAILED else "koi nahi")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())



