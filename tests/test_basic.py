import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from brain import router
from core import events, modes
from core.engine import Engine
from datasafe import isolated_data

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def test_mode_switch():
    print("MODE SWITCH")
    check("default mode", Engine().mode, "sunday")
    check("sirf sunday (Phase 5)", config.SUNDAY_ONLY, True)
    check("'Prabh,' par switch band", modes.detect_mode("Prabh, kya haal", "sunday")[0], "sunday")
    check("'Sunday' se switch", modes.detect_mode("Sunday plan batao", "prabh")[0], "sunday")
    check("bina naam mode nahi badla", modes.detect_mode("kya haal", "prabh")[0], "prabh")
    check("naam badal gaya text me", modes.detect_mode("sundaya kya hua", "sunday")[0], "sunday")
    check("prefix hata diya", modes.detect_mode("Sunday, plan batao", "sunday")[1], "plan batao")
    check("dono personas alag", modes.persona_for("sunday") != modes.persona_for("prabh"), True)


def test_brain_fallback():
    print("BRAIN FALLBACK")
    import brain.pool as pool
    import brain.pool_config as pc

    saved_pool, saved_ask = pc.POOL, pool._ask_with_retry

    def fake_ask(provider, history, persona, model):
        if provider["name"] == "groq":
            raise RuntimeError("limit khatam")
        return "gemini se jawab"

    fake = (
        pc._p(name="groq", tier=pc.TIER1, key="k", models=("g-120b",)),
        pc._p(name="gemini", tier=pc.TIER2, key="k", models=("gem-flash",)),
    )
    pc.POOL, pool._ask_with_retry = fake, fake_ask
    try:
        pool.reset()
        answer, name = pool.ask([{"role": "user", "content": "hi"}], "persona")
        check("groq fail par gemini", name, "gemini")
        check("gemini ka jawab", answer, "gemini se jawab")
    finally:
        pc.POOL, pool._ask_with_retry = saved_pool, saved_ask

    def all_dead(provider, history, persona, model):
        raise RuntimeError("500 server error")

    pc.POOL, pool._ask_with_retry = fake, all_dead
    try:
        pool.reset()
        answer, name = pool.ask([{"role": "user", "content": "hi"}], "persona")
        check("dono fail par brain=none", name, "none")
        check("dono fail par jawaab mila", answer != "", True)
        check("reason bhi bataya", "groq" in answer and "gemini" in answer, True)
    finally:
        pc.POOL, pool._ask_with_retry = saved_pool, saved_ask
        pool.reset()


def test_engine_events():
    print("ENGINE EVENTS")
    engine = Engine()

    class FakeRouter:
        def ask(self, history, persona):
            return "test jawab", "groq"

    import brain.router as brain_router
    import core.engine as engine_module
    engine_module.router = FakeRouter()
    # Phase 5: sirf Sunday — "Prabh," par mode nahi badalta, is liye
    # mode-change ka log event bhi nahi aata.
    try:
        out = list(engine.handle("Prabh, hello"))
    finally:
        engine_module.router = brain_router
    kinds = [e["type"] for e in out]
    statuses = [e["value"] for e in out if e["type"] == "status"]
    check("pehle listening", statuses[0], "listening")
    check("thinking aaya", "thinking" in statuses, True)
    check("last idle", statuses[-1], "idle")
    check("mode sunday hi raha", engine.mode, "sunday")
    check("mode change ka log nahi", any("mode badla" in e.get("text", "") for e in out), False)
    check("user message bheja", any(e["type"] == "message" and e["role"] == "user" for e in out), True)
    check("assistant message aaya", kinds.count("message"), 2)
    check("pehle 3 events sahi", [e["type"] for e in out][:3], ["status", "message", "status"])
    # Flag off karne par switch + uska log wapas — code maarta nahi hai.
    engine_module.router = FakeRouter()
    config.SUNDAY_ONLY = False
    try:
        eng2 = engine_module.Engine()
        eng2.mode = "prabh"
        out2 = list(eng2.handle("Sunday, hello"))
    finally:
        config.SUNDAY_ONLY = True
        engine_module.router = brain_router
    check("flag off par switch hua", eng2.mode, "sunday")
    check("switch ka log aaya", any(e["type"] == "log" for e in out2), True)
    first = list(engine.handle(""))[0]
    check("khaali message safe", [first["type"], first["value"]], ["status", "listening"])
    blocked = list(engine.run_tool("weather", {}))
    check("unknown tool block", [e["decision"] for e in blocked], ["deny"])


def test_events_module():
    print("EVENTS")
    check("status ok", events.status("thinking"), {"type": "status", "value": "thinking"})
    check("message ok", events.message("user", "hi")["role"], "user")
    check("galat status rok diya", _raises(events.status, "dancing"), True)
    check("log me data gaya", events.log("x", data={"mode": "prabh"})["data"]["mode"], "prabh")


def _raises(fn, arg):
    try:
        fn(arg)
    except ValueError:
        return True
    return False


# Engine test ke dauran memory ko asli data/ me likhta hai - helper se tmp me.
with isolated_data():
    test_mode_switch()
    test_brain_fallback()
    test_engine_events()
    test_events_module()

print()
if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Saare test pass.")