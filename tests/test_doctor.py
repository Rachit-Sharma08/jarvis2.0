"""`--doctor` ka faisla - saaf jawab, aur galat jawab nahi.

**Kyun:** doctor owner ka pehla sawaal hai ("chalega ya nahi?"). Wo jhooth bole
to user galat jagah dhoondta rehta hai. Yahan sirf faisla test hota hai -
asli mic/sounddevice/server kabhi nahi.

Har jaanch `_line()` se ek (mark, naam) deti hai; `run()` unhi par faisla karta
hai. Is liye test me checks ko fake karna kaafi hai.
"""

import socket
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
import doctor  # noqa: E402
from tests.wakecmdhelp import patch  # noqa: E402
from tests.wakehelp import check, finish  # noqa: E402

NAMES = ("_brain", "_stt", "_wake", "_mic", "_port", "_tools")


def only(**marks):
    """Har check ko fix mark do; naam ke hisaab se."""
    def make(name, mark):
        def part():
            return [doctor._line(mark, name, "test")]
        return part
    return {name: make(name.strip("_"), marks.get(name.strip("_"), doctor.OK))
            for name in NAMES}


class TestRun(unittest.TestCase):
    def run_doctor(self, **marks):
        saved = {name: getattr(doctor, name) for name in NAMES}
        try:
            for name, fn in only(**marks).items():
                setattr(doctor, name, fn)
            return doctor.run()
        finally:
            for name, fn in saved.items():
                setattr(doctor, name, fn)

    def test_sab_theek(self):
        check("sab OK = 0", self.run_doctor(), 0)

    def test_kuch_toota(self):
        check("ek FAIL = 1", self.run_doctor(mic=doctor.BAD), 1)

    def test_sirf_warn(self):
        check("sirf WARN = 0", self.run_doctor(wake=doctor.WARN), 0)

    def test_crash_bhi_fail(self):
        def boom():
            raise RuntimeError("hardware phat gaya")
        saved = doctor._mic
        doctor._mic = boom
        try:
            check("crash = 1", doctor.run(), 1)
        finally:
            doctor._mic = saved


class TestBrain(unittest.TestCase):
    def test_key_nahi(self):
        with patch(config, "has_groq", lambda: False), \
                patch(config, "has_gemini", lambda: False):
            marks = [m for m, _, _ in doctor._brain()]
        check("dono key nahi = FAIL", marks, [doctor.BAD])

    def test_groq(self):
        with patch(config, "has_groq", lambda: True):
            marks = [m for m, _, _ in doctor._brain()]
        check("groq key = OK", marks, [doctor.OK])


class TestPort(unittest.TestCase):
    def test_free(self):
        """Band port par 'khaali' - doctor kuch shuru nahi karta."""
        with socket.socket() as probe:
            probe.bind((config.SERVER_HOST, 0))
            free_port = probe.getsockname()[1]
        with patch(config, "SERVER_PORT", free_port):
            marks = doctor._port()
        check("khaali port = OK", [m for m, _, _ in marks], [doctor.OK])
        check("message me 'khaali'", "khaali" in marks[0][2], True)

    def test_busy(self):
        """App pehle se chal raha ho to bhi OK (dohra server nahi)."""
        with socket.socket() as busy:
            busy.bind((config.SERVER_HOST, 0))
            busy.listen(1)
            port = busy.getsockname()[1]
            with patch(config, "SERVER_PORT", port):
                marks = doctor._port()
        check("busy port = OK", [m for m, _, _ in marks], [doctor.OK])
        check("message me 'chal raha'", "chal raha" in marks[0][2], True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("doctor theek" if result.wasSuccessful() else "FAIL")
