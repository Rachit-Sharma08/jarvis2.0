"""Wake worker ka wiring (Step 1) — **asli mic kabhi nahi** khulta.

`worker.start()` asli chalta to Vosk model load + mic khul jaata, is liye yahan
`wake/session.py` ke **do** cheez (model build + `MicSource`) fake se badal kar
sirf wiring check hoti hai. Poora loop `test_wake_loop.py`, mic ka VAD
`test_wake.py` me hai.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from desktophelp import check, finish
from wake import worker as wake_worker
from wakehelp import use_fake_model

use_fake_model()   # `wake_available()` ke liye - asli Vosk model ki zarurat nahi


def test_worker_wiring():
    print("WAKE WORKER (wiring)")
    from wake import session as session_mod
    from wakehelp import FakeListener, FakeMic

    check("READY ab True hai", wake_worker.READY, True)
    check("state shuru me off", wake_worker.state(), "off")
    for name in ("start", "stop", "state", "listening", "set_paused", "wakes"):
        check(f"worker.{name} hai", callable(getattr(wake_worker, name, None)), True)
    check("wake shabd config me", config.WAKE_WORDS, ("jarvis",))

    saved = (session_mod.detect.build, session_mod.audio_mod.MicSource)
    mic = FakeMic()
    session_mod.detect.build = lambda: FakeListener()
    session_mod.audio_mod.MicSource = lambda: mic
    try:
        check("start True", wake_worker.start(), True)
        check("state listening", wake_worker.state(), "listening")
        wake_worker.set_paused(True)
        check("pause ke baad bhi listening", wake_worker.state(), "listening")
        wake_worker.set_paused(False)
    finally:
        wake_worker.stop()
        session_mod.detect.build, session_mod.audio_mod.MicSource = saved
    check("stop ke baad off", wake_worker.state(), "off")


test_worker_wiring()

finish("Saare wake worker wiring test pass.")