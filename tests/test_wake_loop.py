"""Wake worker ka loop (Phase 5 Step 1) — fake mic + fake listener.

Worker ka `Session` (`wake/session.py`) asli thread me chalta hai, is liye test
me `wakehelp.wait()` se chhota intezaar lete hain. **Asli mic, Vosk model aur
sounddevice kabhi nahi chalti** — sirf `detect.build` aur `audio_mod.MicSource`
patch hote hain (yahi do cheez `Session.start()` maangta hai).

Jo check hota hai: trigger + `heard` state · cooldown (dobaara trigger nahi) ·
mute (pause) par khamoshi · mic band hone par `error` · crash-safe callbacks.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from wake import model as model_mod
from wake import session as session_mod
from wake import worker
from wakehelp import FakeListener, FakeMic, check, finish, loud, quiet, truthy, wait


def test_worker_loop():
    print("WORKER LOOP (fake mic + fake listener)")
    saved = (session_mod.detect.build, session_mod.audio_mod.MicSource)
    mic, heard, states = FakeMic(), [], []
    listener = FakeListener(["kuch aur", "hey sunday whatsapp kholo"])
    session_mod.detect.build = lambda: listener
    session_mod.audio_mod.MicSource = lambda: mic
    try:
        worker.stop()
        check("start True", worker.start(on_wake=heard.append, on_state=states.append), True)
        check("state listening", worker.state(), "listening")
        check("listening() bhi", worker.listening(), True)
        for _ in range(4):
            mic.feed(loud())
        mic.feed(quiet())
        wait(lambda: "heard" in states)
        check("wake trigger hua", heard, ["hey sunday"])
        check("state heard aaya", "heard" in states, True)
        check("ek hi trigger", worker.wakes(), 1)

        worker.set_paused(True)
        listener.queue.append("hey sunday")
        for _ in range(3):
            mic.feed(loud())
        mic.feed(quiet())
        wait(lambda: False, seconds=0.3)
        check("mute me trigger nahi", worker.wakes(), 1)

        worker.set_paused(False)
        wait(lambda: False, seconds=config.WAKE_COOLDOWN_SECONDS + 0.2)
        listener.queue.append("hello sunday")
        for _ in range(3):
            mic.feed(loud())
        mic.feed(quiet())
        wait(lambda: worker.wakes() == 2)
        check("unmute par fir se sun raha hai", worker.wakes(), 2)
        check("start dobara True", worker.start(), True)

        worker.stop()
        check("stop ke baad band", worker.state(), "off")
        check("mic band hua", mic.stopped, True)
        check("on_state crash-safe", "listening" in states, True)
        truthy("describe me state", "state=off" in worker.describe())
    finally:
        session_mod.detect.build, session_mod.audio_mod.MicSource = saved
        worker.stop()


def test_crash_safe():
    print("WORKER CALLBACK CRASH")
    saved = (session_mod.detect.build, session_mod.audio_mod.MicSource)
    mic = FakeMic()
    session_mod.detect.build = lambda: FakeListener(["hey sunday"])
    session_mod.audio_mod.MicSource = lambda: mic
    try:
        worker.stop()
        before = worker.wakes()          # count poore app ka hai, is suite ka nahi

        def boom(_phrase):
            raise RuntimeError("HUD fail")

        def bad_state(_value):
            raise RuntimeError("state fail")

        worker.start(on_wake=boom, on_state=bad_state)
        for _ in range(3):
            mic.feed(loud())
        mic.feed(quiet())
        wait(lambda: worker.wakes() > before)
        check("on_wake crash phir bhi ek trigger", worker.wakes(), before + 1)
        worker.stop()
    finally:
        session_mod.detect.build, session_mod.audio_mod.MicSource = saved
        worker.stop()


def test_worker_fail():
    print("WORKER FAIL (model/mic na ho)")
    saved = (session_mod.detect.build, session_mod.audio_mod.MicSource)
    session_mod.detect.build = _raise_model
    session_mod.audio_mod.MicSource = FakeMic
    try:
        worker.stop()
        states = []
        check("model na ho to start False", worker.start(on_state=states.append), False)
        check("state error", worker.state(), "error")
        check("state bheja bhi", states, ["error"])
        check("listening nahi", worker.listening(), False)
    finally:
        worker.stop()

    def boom_mic(*_a, **_k):
        raise RuntimeError("mic device busy")

    session_mod.detect.build = lambda: FakeListener()
    session_mod.audio_mod.MicSource = boom_mic
    try:
        check("mic na khule to False", worker.start(), False)
        check("state error (mic)", worker.state(), "error")
    finally:
        session_mod.detect.build, session_mod.audio_mod.MicSource = saved
        worker.stop()


def _raise_model(folder=""):
    raise model_mod.ModelMissing("model nahi mila")


def test_states_and_describe():
    print("SESSION STATES (direct)")
    fresh = session_mod.Session()
    check("naya session off", fresh.state(), "off")
    check("listening False", fresh.listening(), False)
    check("wakes 0", fresh.wakes(), 0)
    truthy("describe me wake", fresh.describe().startswith("wake="))
    fresh.set_paused(True)
    fresh.set_paused(False)
    fresh._say(None, "kuch-aur")
    check("bad state -> off", fresh.state(), "off")
    fresh.stop()
    check("stop se pehle bhi crash nahi", fresh.state(), "off")


for fn in (test_worker_loop, test_crash_safe, test_worker_fail, test_states_and_describe):
    fn()

finish("Saare wake loop test pass.")
