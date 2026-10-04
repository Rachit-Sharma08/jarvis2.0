"""`wake/listen.py` ke chaar kaam + pause/stop ke pakkaurey.

Step 2c ka test do file me hai. Yeh wala **mic aur pause** sambhalta hai:

- `drain()` purana queue phenkta hai (Jarvis apni awaaz na sun le)
- `warmup()` mic ke khulne ka wait, aur wo bhi drain karta hai
- `stop` lagane par `drain`/`warmup`/`capture`/`to_text`/`speak` sab ruk jaate hain
- command ke dauran mic **hold** rehta hai, aur MUTE aane par hold absorb ho jaata
  hai — **MUTE haar nahi maarta**

**Asli mic, Groq aur speaker kabhi nahi chalti** — `wakehelp.FakeMic` aur
`desktop.playback.say` ka patch. Pausing ke pakkaurey ke liye public
`wake_worker.paused()` (private `_paused` nahi).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.wakehelp import check, finish, quiet, show, truthy  # noqa: E402
from tests.wakecmdhelp import Spy, patch  # noqa: E402

import config  # noqa: E402
from desktop import playback  # noqa: E402
from tests.wakehelp import FakeMic  # noqa: E402
from wake import ask, listen  # noqa: E402
from wake import worker as wake_worker  # noqa: E402

CHUNKS = [quiet(1) for _ in range(25)]


def test_drain_and_warmup():
    show("listen: drain queue khaali karta hai, warmup bhi phenkta hai")
    from tests.wakehelp import FakeMic

    mic = FakeMic([quiet(1) for _ in range(10)])
    listen.reset()
    check("10 phenke", listen.drain(mic), 10)
    check("ab khaali", listen.drain(mic), 0)
    with patch(config, "COMMAND_WARMUP_SECONDS", 0.05):
        check("warmup ne bhi phenka", listen.warmup(FakeMic([quiet(1)])), 1)
    listen.reset()


def test_stop_event_stops_everything():
    show("stop: to_text aur speak dono ruke")
    said = Spy(1)
    listen.reset()
    listen.stop()
    check("to_text ruk gaya", listen.to_text(CHUNKS), "")
    check("speak nahi bola", ask.speak("kuch bhi"), 0)
    with patch(playback, "say", said):
        check("worker.stop() par bhi kuch nahi bola", wake_worker.stop(), None)
    check("kuch nahi bola", said.calls, [])
    listen.reset()


def test_mic_held_then_released():
    show("mic: command ke dauran hold, baad me chhod")
    seen = []
    truthy("hold mila", wake_worker.hold_for_command())
    seen.append(("during", wake_worker.paused()))
    wake_worker.release_from_command()
    seen.append(("after", wake_worker.paused()))
    check("command me sunna band, baad me chalu", seen,
          [("during", True), ("after", False)])


def test_mute_absorbs_hold():
    show("MUTE command ke beech me aaye to MUTE hi bache")
    truthy("pehle hold", wake_worker.hold_for_command())
    truthy("hold ne pause kiya", wake_worker.paused())
    wake_worker.set_paused(True)          # tray MUTE — hold absorb
    wake_worker.release_from_command()    # MUTE haar nahi maarta
    check("MUTE bacha raaha", wake_worker.paused(), True)
    wake_worker.set_paused(False)
    check("unmute ho gaya", wake_worker.paused(), False)


for fn in (test_drain_and_warmup, test_stop_event_stops_everything,
           test_mic_held_then_released, test_mute_absorbs_hold):
    fn()

finish("wake listen + pause (Step 2c) theek")