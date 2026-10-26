"""`main.py` (browser raasta) bhi wake word sunta hai - ya chup-chaap behra hai?

**Asli bug:** README ka Raasta B (`python main.py`) me wake worker kabhi
shuru hi nahi hota tha. Sirf `desktop/app.py` usse chalata hai. Is liye
"Hlo Jarvis" bolne par kuch nahi hota tha - app chal raha ho tab bhi.

Yahan poora `main()` chalta hai, par server/mic/network **kabhi nahi**:
`uvicorn.run`, `wake.worker`, `checkup.run` aur single lock sab fake hain.
"""

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
import main  # noqa: E402
from desktop import callbacks, single  # noqa: E402
from desktop.state import STATE  # noqa: E402
from tests.wakecmdhelp import patch  # noqa: E402
from tests.wakehelp import check, finish  # noqa: E402
from wake import worker as worker_mod  # noqa: E402


class FakeLock:
    def __init__(self):
        self.released = 0

    def acquire(self):
        return self

    def release(self):
        self.released += 1


class BusyLock:
    released = 0

    def acquire(self):
        raise single.AlreadyRunning("Jarvis pehle se CHAL raha hai (pid=123).")


class TestMain(unittest.TestCase):
    def run_main(self, started=True, lock=None):
        events = []
        lock = lock or FakeLock()

        def fake_start(on_wake=None, on_state=None):
            events.append(("start", on_wake, on_state))
            return started

        def fake_stop():
            events.append(("stop",))

        def fake_uvicorn(*_a, **_kw):
            events.append(("uvicorn",))

        out = io.StringIO()
        with patch(main.checkup, "run", lambda: []), \
                patch(config, "ensure_workspace", lambda: None), \
                patch(single, "Single", lambda: lock), \
                patch(worker_mod, "start", fake_start), \
                patch(worker_mod, "stop", fake_stop), \
                patch(main.uvicorn, "run", fake_uvicorn), \
                redirect_stdout(out):
            main.main()
        return events, out.getvalue(), lock

    def test_wake_shuru_hota_hai(self):
        events, out, lock = self.run_main()
        check("wake start hua", events[0][0], "start")
        check("on_wake wahi callback", events[0][1], callbacks.on_wake)
        check("on_state STATE.set_wake", events[0][2], STATE.set_wake)
        check("server chala", ("uvicorn",) in events, True)
        check("wake band hua", events[-1], ("stop",))
        check("lock chhoda", lock.released, 1)
        check("user ko bataya", "Wake word ON" in out, True)

    def test_wake_fail_saaf_bataye(self):
        with patch(config, "wake_available", lambda: (False, "mic band hai")):
            events, out, _ = self.run_main(started=False)
        check("fail par bhi stop", events[-1], ("stop",))
        check("wajah dikhe", "WARNING: wake word OFF - mic band hai" in out, True)

    def test_pehle_se_chal_raha(self):
        events, out, lock = self.run_main(lock=BusyLock())
        check("kuch shuru nahi", events, [])
        check("lock chhoda nahi", lock.released, 0)
        check("saaf message", "pehle se CHAL raha hai" in out, True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("main wake theek" if result.wasSuccessful() else "FAIL")
