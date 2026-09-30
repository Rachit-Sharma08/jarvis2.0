"""Fix round 1 — Gemini timeout cooldown, client wiring, brain crash safety."""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from brain import health

FAILED = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def reset():
    health.GONE.clear()
    health.UNTIL.clear()
    health.LAST.clear()


def test_gemini_timeout_cooldown():
    """Gemini 15s me na aaye to har request pe 15s ruke na — 10 min rest le."""
    print("GEMINI TIMEOUT")
    import time as _t
    from brain import gemini_client

    check("timeout pehchana", gemini_client._is_timeout(
        Exception("504 DEADLINE_EXCEEDED")), True)
    check("sdk timeout pehchana", gemini_client._is_timeout(Exception("APITimeoutError")), True)
    check("403 timeout nahi", gemini_client._is_timeout(Exception("403 permission")), False)

    reset()
    saved = gemini_client._call

    def slow(model, prompt, persona):
        _t.sleep(0.01)
        raise TimeoutError("request timed out")

    gemini_client._call = slow
    try:
        gemini_client.ask([{"role": "user", "content": "hi"}], "p")
    except gemini_client.BrainError:
        pass
    finally:
        gemini_client._call = saved
    check("timeout par skip hua", "rest par" in health.blocked_reason("gemini"), True)
    check("504 reason bana", "timeout" in health.LAST.get("gemini", ""), True)
    check("groq rest nahi hua", health.blocked_reason("groq"), "")

    reset()
    calls = []

    def busy(model, prompt, persona):
        calls.append(model)
        raise Exception("503 The model is overloaded")

    gemini_client._call = busy
    saved_wait = config.GEMINI_RETRY_WAIT
    config.GEMINI_RETRY_WAIT = 0.01
    try:
        gemini_client.ask([{"role": "user", "content": "hi"}], "p")
    except gemini_client.BrainError:
        pass
    finally:
        gemini_client._call = saved
        config.GEMINI_RETRY_WAIT = saved_wait
    check("har model par 1 retry (2 try)", calls.count(calls[0]), 2)
    check("dusra model try nahi hua", sorted(set(calls)), [config.GEMINI_MODELS[0]])
    check("503 ke baad skip", "rest par" in health.blocked_reason("gemini"), True)
    reset()

    # Groq: 429 par sirf ek try — dusra model bhi nahi, provider 10 min rest.
    reset()
    from brain import groq_client

    calls.clear()

    class BusyGroq:
        @staticmethod
        def create(**kwargs):
            calls.append(kwargs["model"])
            raise Exception("Error code: 429 - rate limit exceeded")

    saved_groq = groq_client.Groq
    groq_client.Groq = lambda **kw: type("C", (), {"chat": type("Ch", (), {
        "completions": BusyGroq})()})()
    try:
        groq_client.ask([{"role": "user", "content": "hi"}], "p")
    except groq_client.BrainError:
        pass
    finally:
        groq_client.Groq = saved_groq
    check("groq: ek hi try", calls, [config.GROQ_MODELS[0]])
    check("groq 10 min rest", "rest par" in health.blocked_reason("groq"), True)
    reset()


def test_client_wiring():
    print("CLIENT WIRING")
    read = lambda p: (config.BASE_DIR / p).read_text(encoding="utf-8")
    check("groq timeout set", "timeout=config.BRAIN_TIMEOUT_GROQ" in read("brain/groq_client.py"), True)
    check("gemini http timeout set", "HttpOptions(timeout" in read("brain/gemini_client.py"), True)
    check("gemini 1 retry", "for attempt in (1, 2)" in read("brain/gemini_client.py"), True)
    check("router traceback", "exc_info=True" in read("brain/router.py"), True)
    tts_src = read("voice/tts.py")
    check("tts voice last4 log", "voice=..%s" in tts_src, True)
    check("tts chars log", "chars=%d" in tts_src, True)
    check("tts provider log", "provider=%s" in tts_src, True)


def test_brain_crash_is_contained():
    """20:41 wala IndexError yahan aaya tha. Ab koi brain crash poora engine
    girayega nahi, ek message aayega, aur log me poora traceback likha jayega."""
    print("BRAIN CRASH")
    import logging
    import core.engine as engine_module
    from core.engine import Engine

    class Crashing:
        def ask(self, history, persona):
            raise IndexError("pop from empty list")

    real = engine_module.router
    engine_module.router = Crashing()
    records = []

    class Grab(logging.Handler):
        def emit(self, record):
            records.append(record)

    engine_log = logging.getLogger("engine")
    handler = Grab()
    engine_log.addHandler(handler)
    try:
        out = list(Engine().handle("kya haal", rid="r-crash"))
    finally:
        engine_module.router = real
        engine_log.removeHandler(handler)

    texts = [e["text"] for e in out if e["type"] == "message" and e["role"] == "assistant"]
    check("engine crash nahi hua", len(out) > 0, True)
    check("ek hi assistant message", len(texts), 1)
    check("user message safe", texts[0].startswith("Kuch gadbad"), True)
    crashes = [r for r in records if "brain crash" in r.getMessage()]
    check("crash log hua", len(crashes), 1)
    check("traceback attach hai", bool(crashes) and crashes[0].exc_info is not None, True)
    check("IndexError naam log me",
          "pop from empty list" in (crashes[0].getMessage() if crashes else ""), True)
    check("history me crash nahi", isinstance(Engine().history, list), True)


for fn in (test_gemini_timeout_cooldown, test_client_wiring, test_brain_crash_is_contained):
    fn()

print("FAIL:", FAILED if FAILED else "koi nahi")
sys.exit(1 if FAILED else 0)
