"""Wake trigger ke **teen raaste** + mic retry (5-Oct ka fix).

Purana system sirf ek raasta tha: Vosk khud `final` de, warna text kho gaya.
5-Oct ka live log dikhata hai `sun liya: 'hello'` phir `sun liya: 'yo'` - yaani
"Hlo Jarvis" do tukde me toot raha tha, dono pheke ja rahe the, aur doosra
command kabhi nahi chalta tha. Ab:

1. **final**   - `feed()` se text (purana raasta, abhi bhi hai)
2. **partial** - Vosk abhi bol raha hai aur wake shabd text me hai (sabse tez)
3. **flush**   - gate ne khamoshi par `FinalResult()` se pending text nikala

Aur mic: `MME error 1` (device busy) par `Session._open_mic()` 3 koshish karta
hai - pehle ek try me app hamesha "wake: nahi chala" ho jati thi.

**Asli mic, Vosk model aur sounddevice kabhi nahi** - `detect.build` aur
`audio_mod.MicSource` patch hote hain (jaise `test_wake_loop.py`).

Do cheezein jaan-boojh kar: (1) cooldown `0` kiya jaata hai (warna pichla test
ka trigger 1.5 s tak chunk phenk deta hai - cooldown ka apna test
`test_wake_loop.py` me hai), (2) `worker.stop()` **pehle** nahi, trigger ka
intezaar karne ke **baad** - warna async loop ko chance hi nahi milta.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from wake import session as session_mod
from wake import worker
from wakehelp import FakeListener, FakeMic, check, finish, loud, quiet, wait

heard_all = []          # module level (AGENTS: helper module level par rakho)


def trigger(phrase, mic=None, stop=None):
    """`Session._fire` teen args deta hai - naya fake teeno leta hai."""
    heard_all.append(phrase)


def _run(listener, chunks, want=1):
    """Worker chala kar chunk bhejo aur trigger ka intezaar karo.

    -> `(trigger list, trigger hua ya nahi)`. Cooldown 0, phir worker band.
    """
    global heard_all
    heard_all = []
    saved = (session_mod.detect.build, session_mod.audio_mod.MicSource,
             config.WAKE_COOLDOWN_SECONDS)
    mic = FakeMic()
    config.WAKE_COOLDOWN_SECONDS = 0.0
    session_mod.detect.build = lambda: listener
    session_mod.audio_mod.MicSource = lambda: mic
    try:
        worker.stop()
        before = worker.wakes()
        worker.start(on_wake=trigger)
        for raw in chunks:
            mic.feed(raw)
        if want:
            ok = wait(lambda: worker.wakes() > before, seconds=3.0)
        else:
            wait(lambda: False, seconds=0.6)
            ok = worker.wakes() == before
    finally:
        session_mod.detect.build, session_mod.audio_mod.MicSource = saved[:2]
        config.WAKE_COOLDOWN_SECONDS = saved[2]
        worker.stop()
    return heard_all, ok


def _silence_tail(extra=2):
    """Awaaz ke baad hangover + silence blocks (gate ka flush yahin hota hai)."""
    return [quiet()] * (config.VAD_HANGOVER_BLOCKS
                        + config.VAD_SILENCE_BLOCKS + extra)


def test_partial_trigger():
    print("TRIGGER: PARTIAL (sabse tez raasta)")
    listener = FakeListener(partial="hey jarvis")
    heard, ok = _run(listener, [loud(), loud(), loud()])
    check("partial se trigger hua", ok, True)
    check("trigger me greeting + naam", heard[-1:], ["hey jarvis"])
    check("sirf partial se (final khaali tha)", listener.finals, 0)


def test_flush_trigger():
    print("TRIGGER: FLUSH (khamoshi par pending text)")
    listener = FakeListener(pending="hello jarvis")
    heard, ok = _run(listener, [loud()] + _silence_tail())
    check("flush se trigger hua", ok, True)
    check("trigger text", heard[-1:], ["hello jarvis"])
    check("gate ne flush kiya", listener.flushes > 0, True)


def test_no_trigger_without_wake_word():
    print("TRIGGER: BEECH KA SHABD = trigger nahi")
    listener = FakeListener(pending="hello")
    heard, ok = _run(listener, [loud()] + _silence_tail(), want=0)
    check("sirf 'hello' se trigger nahi", ok, True)
    check("koi trigger text nahi", heard, [])


def test_final_still_works():
    print("TRIGGER: FINAL (purana raasta)")
    listener = FakeListener(["yo jarvis whatsapp kholo"])
    heard, ok = _run(listener, [loud(), loud()])
    check("final se trigger hua", ok, True)
    check("sirf wake hissa", heard[-1:], ["yo jarvis"])


def test_mic_retry():
    print("MIC RETRY (device busy)")
    saved = (session_mod.detect.build, session_mod.audio_mod.MicSource)
    attempts = {"n": 0}

    class BusyMic(FakeMic):
        """Pehli koshish me `MicUnavailable` (MME error 1), phir khul gaya."""

        def __init__(self):
            super().__init__()
            attempts["n"] += 1

        def start(self):
            if attempts["n"] < config.MIC_OPEN_ATTEMPTS:
                raise session_mod.audio_mod.MicUnavailable("MME error 1 (busy)")
            super().start()
            return True

    session_mod.detect.build = lambda: FakeListener()
    session_mod.audio_mod.MicSource = BusyMic
    try:
        worker.stop()
        ok = worker.start(on_wake=trigger)
        check("busy mic ke baad bhi start ho gaya", ok, True)
        check("sab koshish hui", attempts["n"], config.MIC_OPEN_ATTEMPTS)
        worker.stop()
    finally:
        session_mod.detect.build, session_mod.audio_mod.MicSource = saved
        worker.stop()


for fn in (test_partial_trigger, test_flush_trigger,
           test_no_trigger_without_wake_word, test_final_still_works,
           test_mic_retry):
    fn()

finish("Saare wake trigger test pass.")