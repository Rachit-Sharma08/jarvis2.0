"""Dead voice-flag audit + drain ki hadd — KAAM 2 ka saboot.

`test_self_hearing.py` (tail guard ka kaam) se alag, sirf yahi teen sawaal:

1. `PLAYBACK_MUTE_MIC` (dead flag) **hataya ja chuka hai** — koi file na define
   karti hai na padhti hai (29-Oct). Asli rok ka raasta `wake/worker.py` ka
   `hold_for_command()` / `release_from_command()` hai.
2. `listen.drain()` 400 chunk (~12 s) tak bounded hai — jabki jawab ka TTS
   18 s tak chalta hai. **Yahi self-hearing ki asli wajah hai.**
3. Is liye tail guard (`config.PLAYBACK_TAIL_GUARD_SECONDS`) zaroori hai.

Source-scan par bharosa kam hai, is liye har check me asal file/line bhi hai.
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.wakehelp import check, finish
from wake import audio as audio_mod
from wake import listen


class TestPlaybackMuteMicAudit(unittest.TestCase):
    """Dead flag wapas na aaye — audit ka hissa."""

    def test_flag_removed(self):
        check("config me nahi", hasattr(config, "PLAYBACK_MUTE_MIC"), False)
        used = []
        paths = list((ROOT / "wake").glob("*.py")) + \
            list((ROOT / "desktop").glob("*.py")) + [ROOT / "config_wake.py"]
        for path in paths:
            if "PLAYBACK_MUTE_MIC" in path.read_text(encoding="utf-8"):
                used.append(path.name)
        check("kahin define/use nahi", used, [])

    def test_real_mechanism_is_hold(self):
        """Asli rok ka raasta `hold_for_command` / `release_from_command` hai."""
        src = (ROOT / "wake" / "worker.py").read_text(encoding="utf-8")
        check("hold_for_command hai", "def hold_for_command(" in src, True)
        check("release_from_command hai", "def release_from_command(" in src, True)
        cmd = (ROOT / "wake" / "command.py").read_text(encoding="utf-8")
        check("command hold leti hai", "hold_for_command()" in cmd, True)

    def test_drain_bound_is_the_real_limit(self):
        """SABOOT: drain 400 chunk tak — 18 s ki awaaz 12 s se lambi hai."""
        secs = (audio_mod.MAX_QUEUE_BLOCKS * audio_mod.BLOCK_SECONDS)
        check("drain ki hadd ~12 s", round(secs), 12)
        check("drain bounded hai",
              "dropped < audio_mod.MAX_QUEUE_BLOCKS" in
              (ROOT / "wake" / "listen.py").read_text(encoding="utf-8"), True)
        check("is liye tail guard zaroori", secs < 18.0, True)
        check("listen.drain maujood", callable(listen.drain), True)


