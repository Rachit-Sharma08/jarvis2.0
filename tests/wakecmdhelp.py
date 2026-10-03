"""Step 2c (wake command) ke fakes — dono test file inhi se import kare.

`test_wake_command.py` (poora flow) aur `test_wake_listen.py` (mic + pause) —
dono ko yehi chahiye. Repo ka niyam: asli mic/Groq/speaker **kabhi nahi**;
sirf fakes. Naya Step 2c test yahin se helper import kare, naya file me
`patch`/`Spy`/`FakeEngine` dubara mat likho.

Yahan kya hai:

- `patch()` — attribute test ke liye badlo, phir wapas (module naam string bhi)
- `Spy` — har call yaad rakhta hai, assert ke liye
- `FakeEngine` — `server.state.ENGINE` ki jagah (brain ya network bilkul nahi)
- `hub_spy()` — `command.HUB` ki jagah, publish hone wale event ikattha
- `engine_say(confirm)` — ek engine jo jawab deta hai (+ chahe to ek ASK card)
- `talk()` — poora `command.run`, sab fake ke saath
- `gatekeeper_uses()` — `wake/command.py` me gatekeeper ka kya import hua (AST)
"""

import contextlib
import importlib
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config  # noqa: E402
from core import events  # noqa: E402
from desktop import playback  # noqa: E402
from tests.wakehelp import FakeMic, loud  # noqa: E402
from wake import command, listen  # noqa: E402

CHUNKS = [loud(1) for _ in range(25)]


@contextlib.contextmanager
def patch(obj, name, value):
    """Attribute test ke liye badlo, phir wapas.

    `obj` module ka naam string ho (`"server.state"`) ya seedha module object."""
    if isinstance(obj, str):
        obj = importlib.import_module(obj)
    saved = getattr(obj, name)
    setattr(obj, name, value)
    try:
        yield
    finally:
        setattr(obj, name, saved)


class Spy:
    """Har call yaad rakhta hai — assert ke liye."""

    def __init__(self, result=None):
        self.calls = []
        self.result = result

    def __call__(self, *args, **kw):
        self.calls.append(args[0] if len(args) == 1 else args)
        return self.result


class FakeEngine:
    """`server/state.py` ke `ENGINE` ki jagah — brain ya network bilkul nahi."""

    def __init__(self, out=None):
        self.out = list(out or [])
        self.calls = []

    def handle(self, text, rid=""):
        self.calls.append((text, rid))
        for event in self.out:
            yield dict(event)


def hub_spy():
    """`command.HUB` ki jagah — publish hone wale event yahan ikattha hote hain."""
    box = Spy()
    box.events = []
    box.publish = lambda event: box.events.append(event)
    return box


def engine_say(confirm=False):
    """Ek engine jo sawal ka jawab deta hai (aur chahe to ek ASK card)."""
    out = [events.status("thinking")]
    if confirm:
        out.append(events.confirm("cid1", "write_file", "D:/prabh/test.txt", 60, "h1"))
    out.append(events.message("assistant", "Aaj ka din kya hai?", "JARVIS"))
    out.append(events.status("idle"))
    return out


def talk(allowed=None, heard="aaj ka din kya hai", out=None, confirm=False,
         mic_chunks=None, on_confirm=None):
    """Poora `command.run` — sab fake ke saath. -> (result, spy, hub, engine).

    `heard` = STT ka text (jo user ne bola). Jawab engine se aata hai."""
    mic = FakeMic(mic_chunks if mic_chunks is not None else CHUNKS)
    said, hub = Spy(1), hub_spy()
    engine = FakeEngine(engine_say(confirm=confirm) if out is None else out)
    stop = threading.Event()
    listen.reset()
    with patch(config, "COMMAND_WARMUP_SECONDS", 0), \
            patch(listen, "capture", lambda *a, **k: CHUNKS), \
            patch(listen, "to_text", lambda *a, **k: heard), \
            patch(playback, "say", said), \
            patch(command, "HUB", hub), \
            patch("server.state", "ENGINE", engine):
        got = command.run(mic, stop, allowed=allowed, on_confirm=on_confirm)
    return got, said, hub, engine


def gatekeeper_uses():
    """`wake/command.py` me gatekeeper ka kya use hua — **AST** se.

    Docstring me likha 'approve nahi hai' jaisa text se dhoka nahi chahiye —
    sirf asli `from gatekeeper... import ...` lines gin-te hain."""
    import ast

    src = (ROOT / "wake" / "command.py").read_text(encoding="utf-8")
    used = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("gatekeeper"):
            used.update(f"{node.module}.{alias.name}" for alias in node.names)
    return sorted(used)