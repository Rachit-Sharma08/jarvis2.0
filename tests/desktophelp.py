"""Desktop test suite ka shared helper (tests/poolhelp.py jaisa).

Sirf `check()` aur runner — koi asli mic, browser, tray ya registry nahi.

Playback ke liye yahan teen fake hain: `FakeMini` (`miniaudio`), `FakeSd`
(`sounddevice`) aur unhe `sys.modules` me lagane wala `install_audio`. Asli
speaker kabhi nahi bajti — `desktop/playback.py` late import karta hai, is
liye `sys.modules` me fake daalna kaafi hai.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def truthy(name, got):
    check(name, bool(got), True)


def show(name):
    print(f"       {name}")


def finish(title):
    print()
    if FAILED:
        print(f"{len(FAILED)} test fail: {FAILED}")
        sys.exit(1)
    print(title)
    sys.exit(0)


# ---- speaker ke fake (desktop/playback.py ke liye) ----

PCM = (1000, 2000, -3000, 4000)


class FakeFormat:
    """`miniaudio.SampleFormat` — sirf SIGNED16 chahiye."""

    SIGNED16 = "signed16"


class FakeDecoded:
    def __init__(self, samples=PCM, sample_rate=32000, nchannels=1):
        self.samples = list(samples)
        self.sample_rate = sample_rate
        self.nchannels = nchannels


class FakeMini:
    """`miniaudio` ka nakli. `decode_file` jaan-boojh kar nahi hai — wo bytes
    lekar apna poora error message dump kar deta hai."""

    SampleFormat = FakeFormat

    def __init__(self, samples=PCM, boom=False, sample_rate=None):
        self.samples = list(samples)
        self.boom = boom
        self.sample_rate = sample_rate
        self.calls = []

    def decode(self, data, output_format=None, nchannels=None, sample_rate=None):
        self.calls.append({
            "bytes": len(data),
            "output_format": output_format,
            "nchannels": nchannels,
            "sample_rate": sample_rate,
        })
        if self.boom:
            raise ValueError("dr_mp3 nahi samjha")
        # Asli miniaudio maangi hui hi rate deta hai — yahi nakli bhi.
        return FakeDecoded(self.samples, self.sample_rate or sample_rate)


class FakeSd:
    """`sounddevice` ka nakli. `play` kya mila, sab yaad rakhta hai.

    Dhyan: asli `query_devices()` sab devices ki list deta hai — `kind` dene par
    sirf default device ka dict. Yahi shape rakhi hai (input + output entries).
    """

    def __init__(self, outputs=1, boom=False, devices_boom=False):
        self.rows = [{"index": 0, "name": "Fake Mic", "max_output_channels": 0}]
        for at in range(outputs):
            self.rows.append({"index": at + 1, "name": "Fake Speakers",
                              "max_output_channels": 2})
        self.boom = boom
        self.devices_boom = devices_boom
        self.played = []

    def query_devices(self, kind=None):
        if self.devices_boom:
            raise RuntimeError("PortAudio nahi khula")
        return list(self.rows)

    def play(self, data, samplerate=None, device=None, blocking=False):
        if self.boom:
            raise RuntimeError("device busy")
        self.played.append({
            "samples": len(data),
            "samplerate": samplerate,
            "device": device,
            "blocking": blocking,
        })


def install_audio(mini=None, sd=None):
    """Dono fake `sys.modules` me daal do. -> (mini, sd, saved)"""
    fake_mini = FakeMini() if mini is None else mini
    fake_sd = FakeSd() if sd is None else sd
    saved = {name: sys.modules.get(name) for name in ("miniaudio", "sounddevice")}
    sys.modules["miniaudio"] = fake_mini
    sys.modules["sounddevice"] = fake_sd
    return fake_mini, fake_sd, saved


def remove_audio(saved):
    """`install_audio` ke baad `sys.modules` wapas ( asli module na rahe)."""
    for name, was in saved.items():
        if was is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = was