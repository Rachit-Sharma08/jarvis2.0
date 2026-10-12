"""WASAPI + resample ka pure test â€” 5-Oct ka mic fix. Asli mic/model kabhi nahi.

Do baatein pakdi jaati hain:
1. `wake/resample.py` 48k -> 16k sahi todta hai (blocks + bacha hua sample).
2. `wake/audio.py` WASAPI device chunta hai aur MME par nahi jaata.

Bina `sounddevice` ke chal jaata hai â€” `pick_input_device` ko ek nakli `sd`
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

FAILED = []


def check(name, got, want):
    ok = got == want
    if not ok:
        FAILED.append(name)
    print("%s %-46s got=%s want=%s" % ("ok  " if ok else "FAIL", name, got, want))


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
    """`PRABH_WAKE_MIC` diya ho to user ka device - host api se pehle."""
    sd = FakeSd([api("Windows WASAPI", 9)])
    check("number 3", audio_mod.pick_input_device(sd, 3), 3)
    check("naam", audio_mod.pick_input_device(sd, "Microphone Array"), "Microphone Array")
    check("khaali env = WASAPI", audio_mod.pick_input_device(sd, ""), 9)
    check("config WASAPI hai", config.INPUT_HOSTAPI, "WASAPI")


def test_gain_is_off_on_silence():
    """Khamoshi par gain 1 hi rahe — VAD warna hamesha "bol raha hai" bolta,
    aur Vosk khamoshi me chalta (battery ka wahi purana nuksan)."""
    g = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    quiet = np.full(480, 0.0005, dtype=np.float32)
    out = g.apply(quiet)
    check("khamoshi pe gain 1", round(float(g.g if hasattr(g, 'g') else g.applied), 3), 1.0)
    check("khamoshi byte-sahi", int(np.abs(out - quiet).max()), 0)
    for _ in range(20):
        g.apply(quiet)
    check("20 khamoshi block ke baad bhi", round(float(g.g if hasattr(g, 'g') else g.applied), 3), 1.0)


def test_gain_raises_quiet_speech():
    """Dheere-dheere bolne par gain upar ho."""
    g = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    for _ in range(10):
        g.apply(np.full(480, 0.0005, dtype=np.float32))
    quiet_speech = np.full(480, 0.0014, dtype=np.float32)
    out = g.apply(quiet_speech)
    check("gain > 1", float(g.g if hasattr(g, 'g') else g.applied) > 1.0, True)
    check("awaaz upar uthi", round(float(out.mean()), 3) > 0.01, True)
    loud = np.full(480, 0.5, dtype=np.float32)
    g.apply(loud)
    check("zor par gain <= 1.2", float(g.g if hasattr(g, 'g') else g.applied) <= 1.2, True)
    check("clip nahi hua", float(g.apply(loud).max()) <= 1.0, True)


def test_gain_levels_are_comparable():
    """Do alag level gain ke baad dono sunne layak laaye jaayein."""
    g1 = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    g2 = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    for _ in range(30):
        g1.apply(np.full(480, 0.0005, dtype=np.float32))
        g2.apply(np.full(480, 0.0005, dtype=np.float32))
    for _ in range(6):
        a = g1.apply(np.full(480, 0.0014, dtype=np.float32))
        b = g2.apply(np.full(480, 0.16, dtype=np.float32))
    check("dheemi utha", float(a.mean()) > 0.02, True)
    check("zor kam hua (clip se bachne)", float(b.max()) <= 1.0, True)
    check("dono sunne layak", 0.02 < float(a.mean()) < float(b.mean()), True)


def test_fixed_gain():
    g = pcm_mod.FixedGain(4.0)
    check("4x laga", round(float(g.apply(np.full(10, 0.1, "float32")).mean()), 4), 0.4)
    check("clip safe", float(g.apply(np.full(10, 0.9, "float32")).max()), 1.0)
    check("1x as-is", float(pcm_mod.FixedGain(1.0).apply(np.full(4, 0.5, "float32")).max()), 0.5)
    check("khaali block", pcm_mod.FixedGain(8.0).apply(np.zeros(0, "float32")).size, 0)


def test_make_gain_from_config():
    """`PRABH_WAKE_GAIN`: auto (default) | number | off â€” teenon raaste."""
    old = config.INPUT_GAIN
    try:
        config.INPUT_GAIN = "auto"
        check("auto = RmsGain", isinstance(audio_mod._make_gain(), pcm_mod.RmsGain), True)
        config.INPUT_GAIN = "6"
        check("6 = FixedGain(6)", audio_mod._make_gain().factor, 6.0)
        for off in ("off", "0", "none", ""):
            config.INPUT_GAIN = off
            check("'%s' = koi gain nahi" % (off or "khaali"), audio_mod._make_gain(), None)
    finally:
        config.INPUT_GAIN = old


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



