"""Fix round 1 â€” brain side: models, permanent 404, 10 min skip, tools-OFF
prompt, ek combined message, router rest, stage timing."""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from brain import health, pool, router
from brain.prompt import build

FAILED = []

def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")

def reset():
    # Round 2: pool + health ke saare state (NEXT_DAY, HUMAN bhi) saaf karo.
    pool.reset()

def test_models_configured():
    print("MODELS")
    check("groq primary", config.GROQ_MODELS[0], "openai/gpt-oss-120b")
    check("groq fallback", config.GROQ_MODELS[1], "openai/gpt-oss-20b")
    check("gemini primary", config.GEMINI_MODELS[0], "gemini-3.5-flash")
    check("gemini fallback list me", "gemini-flash-latest" in config.GEMINI_MODELS, True)
    check("groq timeout 10s", config.BRAIN_TIMEOUT_GROQ, 10.0)
    check("gemini timeout 15s", config.BRAIN_TIMEOUT_GEMINI, 15.0)
    check("skip 10 min", config.PROVIDER_SKIP_SECONDS, 600)

def test_classify():
    print("ERROR CLASSIFY")
    check("groq 404 = gone", health.classify(Exception("404 model_not_found x")), "gone")
    check("gemini 404 = gone", health.classify(Exception("404 NOT_FOUND no longer available")), "gone")
    check("402 payment_required = busy", health.classify(Exception("402 payment_required")), "busy")
    check("insufficient_credit = billing", health.classify(
        Exception("insufficient_credits")), "billing")
    check("429 = busy", health.classify(Exception("429 Rate Limit Error")), "busy")
    check("503 = busy", health.classify(Exception("503 overloaded")), "busy")
    check("timeout = other", health.classify(Exception("APITimeoutError")), "other")
    check("voice uuid me 429 = other", health.classify(
        Exception("prabh/3b554273-4299-48b9-9aaf-eefd438e3941: forced fail")), "other")
    check("asli 429 = busy", health.classify(Exception("Error code: 429 - rate limit")), "busy")
    check("5030 = other", health.classify(Exception("upstream 5030 request failed")), "other")

def test_permanent_model():
    print("PERMANENT 404")
    reset()
    from brain import groq_client
    for gone in config.GROQ_MODELS:
        health.model_gone("groq", gone, "404 model_not_found")
    check("model GONE me gaya", config.GROQ_MODEL in health.GONE, True)
    check("warning line bani", any(config.GROQ_MODEL in w for w in health.warnings()), True)
    check("provider skip nahi hua", health.blocked_reason("groq"), "")
    try:
        groq_client.ask([{"role": "user", "content": "hi"}], "p")
        check("GONE model par API call hui", "0 try", "BrainError")
    except groq_client.BrainError as exc:
        check("0 try = koi API call nahi", "0 try" in str(exc), True)
        check("hata chuke bola", "hata chuke" in str(exc), True)
    finally:
        reset()

    # Sirf pehla model gone: fallback list se kaam chalna chahiye.
    health.model_gone("groq", config.GROQ_MODELS[0], "404")
    calls = []

    class FakeGroq:
        @staticmethod
        def create(**kwargs):
            calls.append(kwargs["model"])
            message = type("M", (), {"content": "ok"})()
            choice = type("C", (), {"message": message})()
            return type("R", (), {"choices": [choice]})()

    real_client = groq_client.Groq
    groq_client.Groq = lambda **kw: type("C", (), {"chat": type("Ch", (), {
        "completions": FakeGroq})()})()
    try:
        answer = groq_client.ask([{"role": "user", "content": "hi"}], "p")
    finally:
        groq_client.Groq = real_client
        reset()
    check("gone model skip hua", calls, [config.GROQ_MODELS[1]])
    check("fallback se jawab mila", answer, "ok")

def test_ten_min_skip():
    print("10 MIN SKIP")
    reset()
    health.skip("gemini", "503 overloaded")
    reason = health.blocked_reason("gemini")
    check("skip shuru hua", "rest par" in reason, True)
    # Round 2: cooldown ab '10 min baad' jaisa human-readable (600s nahi).
    check("~10 min dikha", "10 min" in reason, True)
    health.UNTIL["gemini"] -= 601
    check("time guzarne par free", health.blocked_reason("gemini"), "")
    health.skip("tts_x", "402", seconds=10)
    left = health.blocked_reason("tts_x")
    check("custom seconds lag raha hai", "9s" in left or "10s" in left, True)
    health.UNTIL["tts_x"] -= 11
    check("custom seconds guzre", health.blocked_reason("tts_x"), "")
    reset()
    # Round 2: paid_plan/billing word = 'billing' category, provider BAND.
    check("402 paid_plan = billing", health.classify_and_skip("elevenlabs", "402 paid_plan_required"), "billing")
    check("elevenlabs BAND", "BAND" in health.blocked_reason("elevenlabs"), True)
    check("khaali error skip nahi", health.classify_and_skip("edge", "weird failure"), "other")
    check("edge chalta rahe", health.blocked_reason("edge"), "")
    reset()

def test_tools_off_prompt():
    print("TOOLS OFF PROMPT")
    short = build("PERSONA", tools_on=False)
    on = build("PERSONA", tools_on=True)
    check("OFF par persona", short.startswith("PERSONA"), True)
    check("OFF par tool spec nahi", "run_command" in short, False)
    check("OFF par JSON rule nahi", '"action"' in short, False)
    check("OFF par tools band bola", "tools BAND" in short, True)
    check("ON par tool spec hai", "run_command" in on, True)
    check("ON par JSON rule hai", '"action"' in on, True)
    check("ON zyada lamba", len(on) > len(short) + 300, True)

def test_one_combined_message():
    print("EK MESSAGE, DONO ERRORS")
    reset()
    import brain.pool_config as pc
    saved_pool, saved_ask = pc.POOL, pool._ask_with_retry
    fake = (pc._p(name="groq", tier=pc.TIER1, key="k", models=("g1",)),
            pc._p(name="gemini", tier=pc.TIER2, key="k", models=("gem1",)))

    def dead(provider, history, persona, model):
        raise RuntimeError(f"{provider['name']} ka error")

    pc.POOL, pool._ask_with_retry = fake, dead
    try:
        answer, name = router.ask([{"role": "user", "content": "hi"}], "p")
    finally:
        pc.POOL, pool._ask_with_retry = saved_pool, saved_ask
        reset()
    check("brain = none", name, "none")
    check("ek hi message", answer.count("Abhi koi brain"), 1)
    check("groq ka error hai", "groq ka error" in answer, True)
    check("gemini ka error hai", "gemini ka error" in answer, True)

def test_router_skips_resting():
    print("ROUTER REST")
    reset()
    import brain.pool_config as pc
    saved_pool, saved_ask = pc.POOL, pool._ask_with_retry
    fake = (pc._p(name="groq", tier=pc.TIER1, key="k", models=("g1",)),
            pc._p(name="gemini", tier=pc.TIER2, key="k", models=("gem1",)))
    called = []

    def good(provider, history, persona, model):
        called.append(provider["name"])
        return "gemini se"

    health.skip("groq", "429")
    pc.POOL, pool._ask_with_retry = fake, good
    try:
        answer, name = router.ask([{"role": "user", "content": "hi"}], "p")
    finally:
        pc.POOL, pool._ask_with_retry = saved_pool, saved_ask
        reset()
    check("rest wala skip hua", name, "gemini")
    check("sirf ek call", called, ["gemini"])

def test_stopwatch():
    print("STAGE TIMING")
    import time as _t
    from core.timing import Stopwatch
    watch = Stopwatch("test")
    start = _t.perf_counter()
    _t.sleep(0.01)
    took = watch.stage("groq", start)
    total = watch.total()
    check("stage 10ms+", took >= 10, True)
    check("total >= stage", total >= took, True)
    check("stage list me", watch.stages[0][0], "groq")


for fn in (test_models_configured, test_classify, test_permanent_model, test_ten_min_skip,
           test_tools_off_prompt, test_one_combined_message, test_router_skips_resting,
           test_stopwatch):
    fn()

print("FAIL:", FAILED if FAILED else "koi nahi")
sys.exit(1 if FAILED else 0)
