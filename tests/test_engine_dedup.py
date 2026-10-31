"""Per-turn tool dedup: same tool+args dobara na chale (E-1).

Sirf fakes - koi asli brain/tool/provider call nahi. Gatekeeper asli rehta hai
(NO_CARDS default 1): SAFE tools seedha, run_command hamesha DENY.
"""

import json
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from core import engine as engine_mod
from core.engine import Engine
from datasafe import isolated_data
from gatekeeper import keeper
from gatekeeper.limiter import Limiter

# `.env` me JARVIS_TRUST=1 ho to run_command bhi ALLOW ho jaata hai.
config.TRUST_ALL = False


def collect(gen):
    out = []
    while True:
        try:
            out.append(next(gen))
        except StopIteration:
            return out


def run(replies, text="kuch karo"):
    calls, reviews = [], []
    engine = Engine()
    saved = keeper.LIMITER
    keeper.LIMITER = Limiter(enabled=True, per_minute=config.TOOL_MAX_CALLS_PER_MINUTE)
    real_review = keeper.review

    def spy(tool, args, mode):
        verdict, payload = real_review(tool, args, mode)
        reviews.append((tool, verdict))
        return verdict, payload

    def fake(name, args):
        calls.append((name, args))
        return "tool output"

    try:
        with mock.patch.object(
            engine_mod.router, "ask",
            side_effect=lambda *a: (replies.pop(0) if replies else "theek", "groq")
        ), mock.patch.object(engine_mod, "execute", side_effect=fake), \
                mock.patch.object(keeper, "review", spy):
            events = collect(engine.handle(text))
    finally:
        keeper.LIMITER = saved
    return events, calls, reviews, engine


def action(tool, **args):
    return json.dumps({"action": tool, "args": args})


def last_answer(events):
    return [e for e in events if e["type"] == "message" and e["role"] == "assistant"][-1]["text"]


def test_same_action_runs_once():
    # "aur" = multi-step -> purana raasta (E-2 seedha jawab is par nahi lagta).
    events, calls, reviews, engine = run([action("get_time_date")] * 5, "kuch karo aur phir dekho")
    assert len(calls) == 1, f"tool {len(calls)} baar chala"
    assert len(reviews) == 1, f"review {len(reviews)} baar hua"
    assert "tool output" in last_answer(events)
    notes = [m for m in engine.history if "abhi ho chuka" in m["content"]]
    assert len(notes) == 1, f"note {len(notes)} baar gaya"


def test_deny_runs_once():
    events, calls, reviews, engine = run([action("run_command", command="dir")] * 5)
    assert calls == [], "DENY ke baad execute ho gaya"
    assert len([r for r in reviews if r[0] == "run_command"]) == 1
    answer = last_answer(events)
    assert "shell command abhi band hai" in answer
    assert "tool nahi chala" not in answer
    assert "5 tool step" not in answer


def test_different_args_both_run():
    replies = [action("add_todo", text="doodh"), action("add_todo", text="ande"), "dono ho gaye"]
    events, calls, reviews, engine = run(replies, "kuch karo aur phir dekho")
    assert len(calls) == 2, f"dono add_todo chale: {calls}"


def test_cap_message_is_last_result():
    replies = [action("add_todo", text=f"t{i}") for i in range(9)]
    events, calls, reviews, engine = run(replies, "kuch karo aur phir dekho")
    assert len(calls) == config.TOOL_MAX_STEPS, f"cap {len(calls)} tha"
    answer = last_answer(events)
    assert "5 tool step" not in answer
    assert "tool output" in answer


if __name__ == "__main__":
    # engine.handle() memory me likhta hai - asli data/memory.json se door.
    with isolated_data():
        test_same_action_runs_once()
        test_deny_runs_once()
        test_different_args_both_run()
        test_cap_message_is_last_result()
    print("SUITE GREEN")
