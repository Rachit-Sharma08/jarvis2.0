"""E-2 direct reply: simple tool par doosra LLM call nahi (sirf fake).

Koi asli brain/tool call nahi: `router.ask`/`execute` dono fake, `data/`
`tests/datasafe.py` se tmp par. Check: (i) open_app ALLOW -> LLM 2nd call 0,
jawab tool-result wala; (ii) DENY -> 2nd call 0 + gatekeeper ki asli wajah,
jhooth nahi; (iii) "aur" wala multi-step -> purana; (iv) list_dir -> purana;
(v) DIRECT_REPLY=0 -> purana; (vi) tool ka error result bhi seedha bola jata hai.
"""
import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from core import engine as engine_mod
from core.engine import Engine
from datasafe import isolated_data

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def asker(replies):
    def ask(*_args):
        return (replies.pop(0) if replies else "theek"), "groq"
    return ask


def act(tool, **args):
    return json.dumps({"action": tool, "args": args})


def run(text, replies, out="tool output"):
    """handle() chalao -> (events, LLM call count, jo tool chale)."""
    tools, engine = [], Engine()
    with mock.patch.object(engine_mod.router, "ask", side_effect=asker(list(replies))) as ask, \
            mock.patch.object(engine_mod, "execute",
                              side_effect=lambda n, a: tools.append(n) or out):
        events = list(engine.handle(text))
    return events, ask.call_count, tools


def last_answer(events):
    return [e for e in events if e["type"] == "message" and e["role"] == "assistant"][-1]["text"]


def test_direct_single_step():
    print("DIRECT: open_app ALLOW")
    events, calls, tools = run("chrome kholo", [act("open_app", name="chrome")])
    check("tool chala", tools, ["open_app"])
    check("LLM sirf 1 baar (2nd call 0)", calls, 1)
    check("jawab tool-result hai", last_answer(events), "tool output")


def test_direct_deny_no_lie():
    print("DIRECT: DENY par asli wajah")
    events, calls, tools = run("notepad band karo", [act("close_app", name="notepad")])
    check("tool chala hi nahi", tools, [])
    check("LLM sirf 1 baar", calls, 1)
    text = last_answer(events)
    check("'Ye nahi kar sakta:' shuru", text.startswith("Ye nahi kar sakta:"), True)
    check("gatekeeper ki wajah hai", "close_app abhi band hai" in text, True)
    check("jhooth nahi (already closed)", "already closed" in text.lower(), False)


def test_multi_step_old_path():
    print("PURANA: 'aur' wala multi-step")
    events, calls, tools = run(
        "chrome kholo aur youtube kholo",
        [act("open_app", name="chrome"), act("open_website", url="https://youtube.com"),
         "dono ho gaye"])
    check("dono tool chale", tools, ["open_app", "open_website"])
    check("LLM 3 baar (purana raasta)", calls, 3)


def test_other_tool_old_path():
    print("PURANA: list_dir (direct list me nahi)")
    events, calls, tools = run("desktop ki files dikhao",
                              [act("list_dir", path="C:/Users/fvcvv/Desktop"), "ye hain files"])
    check("tool chala", tools, ["list_dir"])
    check("LLM 2 baar", calls, 2)
    check("LLM ka jawab", last_answer(events), "ye hain files")


def test_flag_off_old_path():
    print("PURANA: DIRECT_REPLY=0")
    with mock.patch.object(config, "DIRECT_REPLY", False):
        events, calls, tools = run("chrome kholo", [act("open_app", name="chrome"), "chrome khul gaya"])
    check("tool chala", tools, ["open_app"])
    check("LLM 2 baar", calls, 2)
    check("LLM ka jawab", last_answer(events), "chrome khul gaya")


def test_tool_error_direct():
    print("DIRECT: tool ka error result")
    events, calls, tools = run("chrome kholo", [act("open_app", name="chrome")],
                               out="chrome.exe is PC par nahi mila.")
    check("tool chala", tools, ["open_app"])
    check("LLM sirf 1 baar", calls, 1)
    check("error seedha bola", last_answer(events), "chrome.exe is PC par nahi mila.")


for fn in (test_direct_single_step, test_direct_deny_no_lie, test_multi_step_old_path,
           test_other_tool_old_path, test_flag_off_old_path, test_tool_error_direct):
    with isolated_data():
        fn()

if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Direct reply test pass.")
