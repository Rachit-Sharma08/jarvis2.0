"""Wake se **brain** tak ka raasta — saare fake, koi asli provider nahi.

`test_wake_command.py` (poora flow) aur `test_wake_listen.py` (mic + pause) ke
saath ye teesra file hai. Yahan sirf wo raaste jo **brain se** aate hain:

- brain ne kuch nahi diya ya saare provider fail hue
- **ASK card** par awaaz se allow nahi - card sirf dikhta hai
- "confirm kijiye" generator rukne se **pehle** boli jaaye (warna 60 s khamoshi)

Fakes `tests/wakecmdhelp.py` se. Asli network call **kabhi nahi**.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.wakehelp import check, finish, show, truthy  # noqa: E402
from tests.wakecmdhelp import (CHUNKS, FakeEngine, FakeMic, Spy,  # noqa: E402
                               engine_say, gatekeeper_uses, hub_spy, patch, talk)

import config  # noqa: E402
from core import events  # noqa: E402
from desktop import playback  # noqa: E402
from wake import command, listen  # noqa: E402


def _mic():
    return FakeMic(CHUNKS)


def test_brain_failed():
    show("run: brain ne jawab nahi diya -> chhoti spoken error")
    _got, said, _hub, _engine = talk(out=[events.status("idle")])
    check("chhoti line boli", said.calls[-1], config.BRAIN_FAILED)
    truthy("500 char se chhoti", len(config.BRAIN_FAILED) < 60)


def test_brain_fail_speaks_short_not_reasons():
    show("run: saare provider fail -> reasons na padhe, BRAIN_FAILED bole")
    # Asli crash raasta: engine log event me `data.brain = "none"` deta hai, aur
    # message me SAARE provider ke technical reasons hote hain. Awaaz wo list
    # nahi padhni chahiye - sirf chhoti `BRAIN_FAILED` line.
    out = [
        events.log("jawab none se aya", data={"brain": "none"}),
        events.message("assistant",
                       "Abhi koi brain jawab nahi de paya. Ye reasons mila:\n"
                       "- groq-120b: 429 busy\n- gemini: timeout\n- nvidia: 402 credits",
                       "JARVIS"),
        events.status("idle"),
    ]
    got, said, hub, _engine = talk(out=out)
    check("flow ok", got, "ok")
    check("sirf BRAIN_FAILED bola", said.calls[-1], config.BRAIN_FAILED)
    check("koi reason awaaz par nahi", any("429" in c for c in said.calls), False)
    truthy("par HUD par reasons dikhe",
           [e for e in hub.events
            if e.get("type") == "message" and "429" in e.get("text", "")])


def test_brain_crash_also_short():
    show("run: brain crash (try/except) par bhi chhoti line")
    # `core/engine.py` ka crash raasta bhi brain_name = "none" deta hai.
    out = [
        events.log("jawab none se aya", data={"brain": "none"}),
        events.message("assistant", "Kuch gadbad ho gayi. Dobara try karo.", "JARVIS"),
        events.status("idle"),
    ]
    _got, said, _hub, _engine = talk(out=out)
    check("BRAIN_FAILED bola", said.calls[-1], config.BRAIN_FAILED)


def test_ask_confirm_spoken_before_wait():
    show("ASK: 'confirm kijiye' generator rukne se PEHLE boli jaye")
    # Asli engine confirm event ke BAAD `keeper.wait()` par rukta hai (60 s).
    # Agar command wahin nahi bolti, to user ko card dikhta hai par awaaz aati
    # hi nahi - 60 second khamoshi. Generator jaanbujh kar block hota hai, aur
    # resume hone ka mark deta hai.
    marks = []

    def say_spy(text, *a, **k):
        marks.append(("spoke", text))
        return 0

    class BlockingEngine(FakeEngine):
        def handle(self, text, rid=""):
            for event in self.out:
                yield dict(event)
                marks.append(("engine-resumed", event.get("type")))

    hub = hub_spy()
    engine = BlockingEngine(engine_say(confirm=True))
    with patch(config, "COMMAND_WARMUP_SECONDS", 0), \
            patch(listen, "capture", lambda *a, **k: CHUNKS), \
            patch(listen, "to_text", lambda *a, **k: "test.txt bana do"), \
            patch(playback, "say", say_spy), patch(command, "HUB", hub), \
            patch("server.state", "ENGINE", engine):
        command.run(_mic(), threading.Event())

    spoke = [i for i, m in enumerate(marks)
             if m == ("spoke", config.CONFIRM_VOICE)]
    resumed = [i for i, m in enumerate(marks)
               if m == ("engine-resumed", "confirm")]
    truthy("confirm wali line boli hi gayi", spoke)
    truthy("generator confirm ke baad resume hua", resumed)
    check("AWAZ generator rukne se PEHLE aayi", spoke[0] < resumed[0], True)


def test_ask_card_never_approves():
    show("ASK card: awaaz se allow nahi — sirf HUD + 'confirm kijiye'")
    from gatekeeper import keeper

    said, hub, waited = Spy(1), hub_spy(), Spy()
    engine = FakeEngine(engine_say(confirm=True))
    opened = Spy()
    with patch(config, "COMMAND_WARMUP_SECONDS", 0), \
            patch(listen, "capture", lambda *a, **k: CHUNKS), \
            patch(listen, "to_text", lambda *a, **k: "test.txt bana do"), \
            patch(playback, "say", said), patch(command, "HUB", hub), \
            patch(keeper, "wait", waited), \
            patch("server.state", "ENGINE", engine):
        got = command.run(_mic(), threading.Event(), on_confirm=opened)
    check("result asked", got, "asked")
    check("HUD khula", len(opened.calls), 1)
    truthy("card HUD par gaya", [e for e in hub.events if e.get("type") == "confirm"])
    check("confirm ki line boli", said.calls[-2], config.CONFIRM_VOICE)
    check("card ka faisla nahi liya", waited.calls, [])
    check("command ne gatekeeper ka module bhi import nahi kiya",
          hasattr(command, "keeper"), False)
    check("gatekeeper se sirf mask hi use hua", gatekeeper_uses(),
          ["gatekeeper.audit.mask"])


for fn in (test_brain_failed, test_brain_fail_speaks_short_not_reasons,
           test_brain_crash_also_short, test_ask_card_never_approves,
           test_ask_confirm_spoken_before_wait):
    fn()

finish("wake -> brain (Step 2c) theek")
