"""Wake ka digital gain — `RmsGain`, gate, aur `JARVIS_WAKE_GAIN` teeno raaste.

Ye file 14-Oct raat me bani jab `test_wake_resample.py` 200 cross kar gaya. Gain
ka hissa alag rakha gaya kyunki usme **alag hi ek sach** hai — wo gate ka
dead zone hai (neeche dekho), jo resample/device se bilkul alag baat hai.

Ye test **bina asli mic ke** chalta hai: `RmsGain` pure numpy hai, sirf
`np.full(...)` blocks diye jaate hain. Asli mic kabhi nahi khulti.

---

## Sabse zaroori baat: gate ka DEAD ZONE

`RmsGain` ka `speech_gate` ka matlab hai "ye RMS awaaz nahi, ise mat uthaiye".
Gate = `0.001 * speech_gate` (default **0.0015**).

Envelope apne input RMS par **atanakta** hai. Is liye agar input RMS gate se
kam hai, to envelope us par hi atka rehta hai — chahe 1 block ho ya 4000.
Math-check kiya: RMS 0.0014 par 4000 block baad bhi `env = 0.001400 < 0.0015`,
gain hamesha 1.0.

Yaani **0.0015 se neeche ki koi awaaz kabhi amplify nahi hoti.** Battery ke
liye ye bura nahi (VAD ko fan ka shor uth nahi milta), lekin agar teri mic ki
asli "dheere bolne" wali awaaz 0.0015 se neeche hai to gain us par bilkul
nahi chalega.

`config_audio.py` ke comments me teen measurement hain — dheemi awaaz **0.0014**
aur **0.0055**, aur mic ka fan-wala shor **0.0026** tak. Teeno ek dusre se
**overlap** karte hain, is liye gate ka sahi number inhe aise hi decide hoga:
**asli mic par measure karke.** Ye test sirf **abhi ka faisal** pin karta hai —
tuning badalne par is test ko update karna padega (AGENTS 8.1.5 ke mutabiq
value badalna "hisab me aata hai", naya fail nahi).
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
from tests.pcmhelp import FAILED, check, gain_value  # noqa: E402
from wake import audio as audio_mod  # noqa: E402
from wake import pcm as pcm_mod  # noqa: E402

# `RmsGain` ka default speech gate: `0.001 * 1.5`.
GATE = 0.001 * 1.5

# `config_audio.py` ke comments ka measured "door/dheere bolne" level — ye gate
# se upar hai, is liye ye real case hai.
QUIET_SPEECH = 0.0055


def test_gain_is_off_on_silence():
    """Khamoshi par gain 1 hi rahe — VAD warna hamesha "bol raha hai" bolta,
    aur Vosk khamoshi me chalta (battery ka wahi purana nuksan)."""
    g = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    quiet = np.full(480, 0.0005, dtype=np.float32)
    out = g.apply(quiet)
    check("khamoshi pe gain 1", round(gain_value(g), 3), 1.0)
    check("khamoshi byte-sahi", int(np.abs(out - quiet).max()), 0)
    for _ in range(20):
        g.apply(quiet)
    check("20 khamoshi block ke baad bhi", round(gain_value(g), 3), 1.0)


def test_gate_blocks_sub_threshold_speech():
    """Gate ke **neeche** ki awaaz kabhi gain nahi paati (dead zone).

    Ye jaan-boojh kar lock kiya gaya behaviour hai — pehle ye test 0.0014 bolta
    tha aur fail hota tha, jisse laga ki production kharab hai. Asli wajah ye
    nikli ki 0.0015 se neeche ka poora hissa amplified nahi hota.
    """
    below = np.full(480, GATE * 0.93, dtype=np.float32)   # 0.001395
    g = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    for _ in range(50):
        g.apply(np.full(480, 0.0005, dtype=np.float32))
    out = g.apply(below)
    check("gate se neeche gain 1 hi", round(gain_value(g), 4), 1.0)
    check("gate se neeche byte-sahi chhua nahi",
          int(np.abs(out - below).max()), 0)
    for _ in range(2000):                # envelope atka hai — hichal nahi sakta
        g.apply(below)
    check("2000 block baad bhi gain 1", round(gain_value(g), 4), 1.0)


def test_gain_raises_quiet_speech():
    """Gate se **upar** ki dheemi awaaz par gain uthta hai."""
    g = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    for _ in range(10):
        g.apply(np.full(480, 0.0005, dtype=np.float32))
    quiet_speech = np.full(480, QUIET_SPEECH, dtype=np.float32)
    out = quiet_speech
    for _ in range(60):                  # envelope attack ke saath upar chadhta hai
        out = g.apply(quiet_speech)
    check("gain > 1", gain_value(g) > 1.0, True)
    check("awaaz upar uthi", float(out.mean()) > 0.03, True)

    loud = np.full(480, 0.5, dtype=np.float32)
    # Gain wapas laane me ~500 block lagte hain: `release=0.01` hai (har block
    # par sirf 1%), yaani ~15 s ka audio @30 ms. Pehle ye check 1 block baad
    # hota tha aur **chhup-chaap pass** tha — sirf is liye ki gain kabhi utha hi
    # nahi tha (input gate ke neeche tha).
    for _ in range(600):
        g.apply(loud)
    check("zor par gain <= 1.2", gain_value(g) <= 1.2, True)
    check("clip nahi hua", float(g.apply(loud).max()) <= 1.0, True)


def test_gain_levels_are_comparable():
    """Do alag level gain ke baad dono sunne layak laaye jaayein."""
    g1 = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    g2 = pcm_mod.RmsGain(target_rms=0.08, max_gain=20.0)
    for _ in range(30):
        g1.apply(np.full(480, 0.0005, dtype=np.float32))
        g2.apply(np.full(480, 0.0005, dtype=np.float32))
    a = b = None
    for _ in range(60):
        a = g1.apply(np.full(480, QUIET_SPEECH, dtype=np.float32))
        b = g2.apply(np.full(480, 0.16, dtype=np.float32))
    check("dheemi utha", float(a.mean()) > 0.03, True)
    check("zor kam hua (clip se bachne)", float(b.max()) <= 1.0, True)
    check("dono sunne layak", 0.03 < float(a.mean()) < float(b.mean()), True)


def test_fixed_gain():
    g = pcm_mod.FixedGain(4.0)
    check("4x laga", round(float(g.apply(np.full(10, 0.1, "float32")).mean()), 4), 0.4)
    check("clip safe", float(pcm_mod.FixedGain(1.0).apply(np.full(4, 0.5, "float32")).max()), 0.5)
    check("khaali block", pcm_mod.FixedGain(8.0).apply(np.zeros(0, "float32")).size, 0)


def test_make_gain_from_config():
    """`JARVIS_WAKE_GAIN`: auto (default) | number | off — teenon raaste."""
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


def main():
    for fn in (test_gain_is_off_on_silence, test_gate_blocks_sub_threshold_speech,
               test_gain_raises_quiet_speech, test_gain_levels_are_comparable,
               test_fixed_gain, test_make_gain_from_config):
        print(f"       {fn.__name__}")
        fn()
    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        return 1
    print("wake gain (RMS, gate, config) theek")
    return 0


if __name__ == "__main__":
    sys.exit(main())