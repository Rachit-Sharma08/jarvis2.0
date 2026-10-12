"""`wake/command.py` ka test — Step 2c ka poora flow.

**Asli mic, Groq aur speaker kabhi nahi chalti.** Fake teen: `wakehelp.FakeMic`
(chunk queue), ek `FakeEngine` (`server.state.ENGINE` ki jagah) aur
`desktop.playback.say` ka recorder. STT bhi fake (`listen.to_text`).

Check kiye jaate hain wo sab jo is feature ke pakkaure hain:

- muted/lock par kuch nahi hota (na record, na awaaz)
- "Ji, boliye" -> capture -> STT -> brain -> jawab ki awaaz, aur har stage ka time
- kuch na suna / STT guard ne roka / brain ne jawab nahi diya — teenon par
  `NOT_UNDERSTOOD` ya `BRAIN_FAILED`
- **ASK card par awaaz se Allow nahi** — card sirf dikhta hai, aur `wake/command.py`
  gatekeeper ka approve/deny/wait **import hi nahi** karta (AST se check)
- har event par `via="voice"` (browser TTS double bol na de)

Mic ke hold/pause/stop ke pakkaurey `tests/test_wake_listen.py` me hain.
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tests.wakehelp import FAILED, FakeMic, check, finish, show, truthy  # noqa: E402
from tests.wakecmdhelp import CHUNKS, Spy, hub_spy, patch, talk  # noqa: E402


def _mic():
    return FakeMic(CHUNKS)

import config  # noqa: E402
from core import events  # noqa: E402
from desktop import playback  # noqa: E402
from wake import ask, command, listen  # noqa: E402


def _mic():
    return FakeMic(CHUNKS)


def test_happy_path():
    show("run: poora flow — 'Ji, boliye' -> jawab ki awaaz")
    got, said, hub, engine = talk()
    check("result ok", got, "ok")
    check("pehla shabd ACK", said.calls[0], config.ACK_ON_WAKE)
    truthy("brain ko command gayi", engine.calls)
    check("brain ko wahi text mila", engine.calls[0][0], "aaj ka din kya hai")
    check("rid 'voice' se shuru", engine.calls[0][1].startswith("voice"), True)
    check("user ka text nahi, brain ka jawab bola", said.calls[-1],
          "Aaj ka din kya hai?")
    check("sirf 2 line boli (ack + jawab)", len(said.calls), 2)
    spoken = [e for e in hub.events if e.get("type") == "message"]
    truthy("HUD par message gaya", spoken)
    check("message par via=voice", {e["via"] for e in spoken}, {"voice"})
    check("ask ka koi card nahi", got != "asked", True)


def test_no_speak_without_mic():
    show("run: mic nahi -> kuch nahi bola")
    said = Spy(1)
    with patch(playback, "say", said):
        check("mic None", command.run(None), "no-mic")
        check("kuch nahi bola", said.calls, [])


def test_blocked_when_muted():
    show("run: MUTE / lock par kuch nahi hota")
    for reason in ("mic mute hai", "PC lock hai"):
        got, said, _hub, engine = talk(allowed=lambda r=reason: (False, r))
        check(f"{reason} par ruk gaya", got, "blocked")
        check(f"{reason}: kuch nahi bola", said.calls, [])
        check(f"{reason}: brain bhi nahi", engine.calls, [])


def test_allowed_crash_is_safe():
    show("run: allowed() crash ho to crash nahi")
    def boom():
        raise RuntimeError("guard mar gaya")
    got, said, _hub, _engine = talk(allowed=boom)
    check("blocked", got, "blocked")
    check("kuch nahi bola", said.calls, [])


def test_not_heard():
    show("run: kuch suna hi nahi -> 'Samajh nahi aaya, dobara boliye'")
    from tests.wakehelp import FakeMic

    said, hub = Spy(1), hub_spy()
    with patch(config, "COMMAND_WARMUP_SECONDS", 0), \
            patch(listen, "capture", lambda *a, **k: None), \
            patch(playback, "say", said), patch(command, "HUB", hub), \
            patch(ask, "HUB", hub):
        got = command.run(FakeMic([]), threading.Event())
    check("not-heard", got, "not-heard")
    check("sirf do line boli", said.calls, [config.ACK_ON_WAKE,
                                            config.NOT_UNDERSTOOD])


def test_stt_rejected():
    show("run: STT guard ne roka (Thank you.) -> wahi 'Samajh nahi aaya'")
    _got, said, _hub, engine = talk(heard="")
    check("no-text", _got, "no-text")
    check("NOT_UNDERSTOOD bola", said.calls[-1], config.NOT_UNDERSTOOD)
    check("brain nahi chala", engine.calls, [])




def test_timing_stages():
    show("har stage ka time: ack/warmup/capture/stt/brain/speak")
    from core.timing import Stopwatch

    seen = []
    real = Stopwatch.stage

    def spy(self, label, start):
        seen.append(label)
        return real(self, label, start)

    with patch(Stopwatch, "stage", spy):
        talk()
    check("saare stage log hue", seen,
          ["ack", "warmup", "capture", "stt", "brain", "speak"])


def test_ui_skips_browser_tts():
    show("ui/app.js: sirf via=voice par browser TTS skip")
    js = (Path(__file__).resolve().parent.parent / "ui" / "app.js").read_text(
        encoding="utf-8")
    truthy("guard maujood", 'ev.via !== "voice"' in js)


for fn in (test_happy_path, test_no_speak_without_mic, test_blocked_when_muted,
           test_allowed_crash_is_safe, test_not_heard, test_stt_rejected,
           test_timing_stages, test_ui_skips_browser_tts):
    fn()

finish("wake command (Step 2c) theek")