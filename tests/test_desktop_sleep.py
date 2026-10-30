"""Battery: 'so jao' — sirf mic + gate chalu, jaagne ka ek hi raasta.

Ye test **asli mic/speaker/browser/HUD kabhi nahi** chalata. Sab fake:
`desktop/sleep.py` ke `matches` pure hai, `enter/wake_up` sirf `STATE` +
`set_hud` badalte hain (fake app se), aur poora command
`tests/wakecmdhelp.py` ke `talk()` se — jisme brain, STT, playback aur HUB sab
fake hain.

Jo cheezein yahan pakdi jaati hain:
1. 'So jao' ka guard — chhota text hi, warna "band ho jao kya matlab hai" se
   app galti se so jaa jaati.
2. Wake ke baad `command.run()` **brain tak nahi jaata** (ASK ka raasta bhi nahi)
   — sirf haalat badalta hai.
3. Dono guard ek jaisa: `desktop/sleep.py` (pure) aur `wake/command.py` ka
   `_is_sleep` — har `config.SLEEP_WORDS` shabd dono par True, warna ek jagah
   shabd add karke doosri chup ho jaati.
4. So raha hai aur "Jarvis" bola -> `callbacks.on_wake` pehle `asleep` hatata
   hai, phir HUD kholta hai aur command chalata hai (jaag gaya = poori uthna).
5. Tray ka item palat leta hai.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tests.wakehelp import check, finish, truthy  # noqa: E402
from tests.wakecmdhelp import patch, talk  # noqa: E402

import config  # noqa: E402
from desktop import actions as actions_mod  # noqa: E402
from desktop import callbacks as cb  # noqa: E402
from desktop import playback  # noqa: E402
from desktop import sleep as sleep_mod  # noqa: E402
from desktop.state import STATE  # noqa: E402
from wake import command  # noqa: E402


class FakeHud:
    def __init__(self):
        self.opened = self.closed = 0

    def open(self):
        self.opened += 1

    def close(self):
        self.closed += 1


class FakeApp:
    def __init__(self):
        self.hud = FakeHud()


def boom(*_a, **_k):
    raise RuntimeError("no window")


def test_sleep_words_matched():
    for text in ("so jao", "Sone jao", "band ho jao", "so jaiye", "soye raho"):
        check("sleep word: " + text, sleep_mod.matches(text), True)


def test_long_text_not_sleep():
    """Chhota guard — lambe vaakya me 'so jao' ho to bhi app nahi soegi."""
    check("5 shabd = command", sleep_mod.matches("band ho jao kya matlab hai"), False)
    check("koi baat nahi", sleep_mod.matches("aaj mausam kaisa hai"), False)
    check("khaali", sleep_mod.matches(""), False)
    check("None", sleep_mod.matches(None), False)


def test_every_config_word_in_both_guards():
    """`config.SLEEP_WORDS` ka har shabd DONO guard me pakda jaye.

    `wake/` ko `desktop/` ka import nahi karwana (niyam) — is liye guard code
    do jagah hai. Sirf ek jagah shabd add hua to doosri chup ho jaati."""
    for word in config.SLEEP_WORDS:
        text = "jarvis " + word
        check("desktop guard: " + word, sleep_mod.matches(text), True)
        check("wake guard: " + word, command._is_sleep(text), True)


def test_enter_closes_hud_and_sets_flag():
    app = FakeApp()
    STATE.set_asleep(False)
    check("enter badla", sleep_mod.enter(app), True)
    check("hud band", app.hud.closed, 1)
    truthy("asleep", STATE.asleep())
    check("dobara enter = badlav nahi", sleep_mod.enter(app), False)


def test_hud_close_crash_still_sleeps():
    """HUD band na bhi ho to so jana rehna chahiye — crash sirf log me."""
    app = FakeApp()
    app.hud.close = boom
    STATE.set_asleep(False)
    sleep_mod.enter(app)
    truthy("crash par bhi so gaya", STATE.asleep())
    STATE.set_asleep(False)


def test_wake_up_clears_flag():
    STATE.set_asleep(True)
    check("jaag gaya", sleep_mod.wake_up(), True)
    check("asleep off", STATE.asleep(), False)


def test_toggle_round_trip():
    app = FakeApp()
    STATE.set_asleep(False)
    check("toggle -> so jao", sleep_mod.toggle(app), True)
    check("toggle -> jaag jao", sleep_mod.toggle(app), False)


def test_command_sleep_skips_brain():
    """'Jarvis, so jao' -> sirf haalat. Brain/ASK card kuch nahi."""
    STATE.set_asleep(False)
    got, said, _hub, engine = talk(heard="jarvis so jao", on_sleep=lambda: None)
    check("command.run = sleep", got, "sleep")
    check("brain chhua hi nahi", engine.calls, [])
    # `ACK_ON_WAKE` tuple hai, har baar me se ek random boli jaati hai — is liye
    # `==` nahi, `in` sahi pakkaura hai.
    check("pehle ack bola", said.calls[0] in config.ACK_ON_WAKE, True)
    truthy("sleep ack bhi bola", config.SLEEP_ACK in said.calls)


def test_command_sleep_calls_callback():
    """`on_sleep` chalta hai — `desktop/sleep.py` ka `enter()` yahin se aata hai."""
    fired = []
    got, _said, _hub, engine = talk(heard="so jao", on_sleep=lambda: fired.append(1))
    check("result", got, "sleep")
    check("callback chala", fired, [1])
    check("brain nahi", engine.calls, [])


def test_command_normal_text_not_sleep():
    """Awaaz me 'band' aaya to app nahi so jani chahiye."""
    got, _said, _hub, engine = talk(heard="band kar do ye file")
    check("normal command", got, "ok")
    check("brain chala", len(engine.calls), 1)


def test_on_wake_wakes_from_sleep():
    """So raha hai aur 'Jarvis' bola -> pehle flag hatta hai, phir command.

    HUD `on_heard` par khulti hai (false wake par nahi), is liye fake command
    bhi wahi callback chalata hai."""
    app, said = FakeApp(), []

    def fake_run(*_a, **kw):
        said.append("RAN")
        (kw.get("on_heard") or (lambda: None))()

    STATE.set_asleep(True)
    with patch(playback, "say", lambda text, stop=None: said.append(text)), \
            patch(config, "COMMAND_WARMUP_SECONDS", 0), \
            patch(cb.command, "run", fake_run):
        cb.on_wake("jarvis", mic=object(), stop=threading.Event(), _app=app)
    check("jaag gaya", STATE.asleep(), False)
    check("HUD khula", app.hud.opened, 1)
    truthy("command bhi chala", "RAN" in said)


def test_tray_action_toggles():
    app = FakeApp()
    STATE.set_asleep(False)
    actions_mod.Actions(app).toggle_sleep()
    truthy("tray se so jaya", STATE.asleep())
    actions_mod.Actions(app).toggle_sleep()
    check("tray se jaag gaya", STATE.asleep(), False)


def test_sleep_ack_short():
    """SLEEP_ACK chhota hona chahiye — TTS + playback dono me waqt lagta hai
    (Step 2 ka asli bug: 4.3 s sirf playback me)."""
    check("slepy ack chhota", len(config.SLEEP_ACK) <= 40, True)
    check("tray label", config.SLEEP_FROM_TRAY, "SO JAAO")


for fn in (test_sleep_words_matched, test_long_text_not_sleep,
           test_every_config_word_in_both_guards, test_enter_closes_hud_and_sets_flag,
           test_hud_close_crash_still_sleeps, test_wake_up_clears_flag,
           test_toggle_round_trip, test_command_sleep_skips_brain,
           test_command_sleep_calls_callback, test_command_normal_text_not_sleep,
           test_on_wake_wakes_from_sleep, test_tray_action_toggles,
           test_sleep_ack_short):
    try:
        fn()
    except Exception as exc:
        print("CRASH:", fn.__name__, type(exc).__name__, exc)

STATE.set_asleep(False)
finish("so jao (battery)")