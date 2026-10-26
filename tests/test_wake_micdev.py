"""Mic device probe — gated mic par exclusive, healthy par shared.

Yahi bug tha: shared WASAPI par Realtek ka AEC speaker ki awaaz cancel karta
hai (0.9 tone ka peak 0.0049 vs exclusive 0.0486) — JARVIS ko sunai hi nahi
deta tha. `auto` ko is liye digital-silence (p10) se faisla karna hai, warna
ek-do spike (chair/notification) mic ko galti se shared par bhej deta tha.

**Asli mic kabhi nahi** — `fake_sd` sirf itna `sounddevice` hai jitna
`wake/micdev.py` use karta hai.
"""

import os
import sys
import types

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.pcmhelp import FAILED, check
from tests.wakecmdhelp import patch
from wake import micdev


class FakeIn:
    """`sd.InputStream` ka nakla — turant callback se buffer bhar deta hai."""

    value = 0.0

    def __init__(self, samplerate=48000, channels=1, device=None, dtype=None,
                 callback=None, blocksize=0, **kw):
        block = max(1, int(samplerate * 0.03))
        data = np.full((block, channels), self.value, dtype=np.float32)
        for _ in range(int(samplerate * 0.5) // block):
            callback(data, block, None, None)

    def start(self):
        pass

    def stop(self):
        pass

    def close(self):
        pass


def fake_sd(value, api="Windows WASAPI"):
    """Itna hi `sounddevice` jitna `micdev` use karta hai."""
    class Fake:
        @staticmethod
        def query_devices(device=None, kind=None):
            return {"hostapi": 0, "default_samplerate": 48000, "name": "Mic"}

        @staticmethod
        def query_hostapis(index):
            return {"name": api}

        @staticmethod
        def WasapiSettings(exclusive=False):
            return {"exclusive": exclusive}

        InputStream = type("In", (FakeIn,), {"value": value})
    return Fake()


def test_exclusive_auto():
    quiet = types.SimpleNamespace(sleep=lambda _s: None)
    with patch(micdev, "time", quiet):
        with patch(config, "MIC_EXCLUSIVE", "auto"):
            check("digital silence -> exclusive",
                  micdev.wasapi_extra(fake_sd(0.0), 9), {"exclusive": True})
            check("healthy floor -> shared",
                  micdev.wasapi_extra(fake_sd(0.001), 9), None)
        with patch(config, "MIC_EXCLUSIVE", "1"):
            check("force exclusive",
                  micdev.wasapi_extra(fake_sd(0.001), 9), {"exclusive": True})
        with patch(config, "MIC_EXCLUSIVE", "0"):
            check("force shared", micdev.wasapi_extra(fake_sd(0.0), 9), None)
        with patch(config, "MIC_EXCLUSIVE", "auto"):
            check("WASAPI ke bahar exclusive nahi",
                  micdev.wasapi_extra(fake_sd(0.0, api="Windows WDM-KS"), 9), None)


def test_names_and_rate():
    sd = fake_sd(0.0)
    check("hostapi naam", micdev.hostapi_name(sd, 9), "Windows WASAPI")
    check("native rate", micdev.native_rate(sd, 9), 48000)
    check("query fail = ?", micdev.hostapi_name(object(), 9), "?")


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("FAIL:", FAILED if FAILED else "koi nahi")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
