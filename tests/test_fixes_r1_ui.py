"""Fix round 1 — UI/startup: rid (duble message), startup checkup, banner."""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from brain import checkup, health
from datasafe import isolated_data

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
    checkup.WARNINGS.clear()


def test_rid_events():
    print("RID / DUBLE MESSAGE")
    import core.engine as engine_module
    from core.engine import Engine

    class FakeRouter:
        def ask(self, history, persona):
            return "test jawab", "groq"

    real = engine_module.router
    engine_module.router = FakeRouter()
    try:
        out = list(Engine().handle("hello", rid="r-test-1"))
    finally:
        engine_module.router = real
    check("har event par rid", all(e.get("rid") == "r-test-1" for e in out), True)
    check("rid na ho par crash nahi", isinstance(list(Engine().handle("")), list), True)
    assistant = [e for e in out if e["type"] == "message" and e["role"] == "assistant"]
    check("ek hi assistant message", len(assistant), 1)
    ui = (config.UI_DIR / "app.js").read_text(encoding="utf-8")
    check("UI me dedupe", "alreadyShown" in ui, True)
    check("UI rid bhejta hai", "rid," in ui or "rid }" in ui, True)
    check("UI ek hi render path", (ui.count("function handleEvent"), 1), (1, 1))


def test_checkup_lists_only():
    print("STARTUP CHECKUP")
    reset()
    check("groq list url", checkup.GROQ_LIST.endswith("/openai/v1/models"), True)
    check("gemini list url", "generativelanguage" in checkup.GEMINI_LIST, True)
    check("timeout chhota", checkup.TIMEOUT <= 5.0, True)
    source = (config.BASE_DIR / "brain" / "checkup.py").read_text(encoding="utf-8")
    check("LLM call nahi hai", "chat.completions" not in source and "generate_content" not in source, True)
    check("sirf GET hai", source.count("httpx.get") == 2 and "httpx.post" not in source, True)
    reset()


def test_checkup_good_and_bad():
    print("CHECKUP OK / GALAT")
    reset()

    def good():
        return set(config.GEMINI_MODELS)
    problems = checkup._check("gemini", config.GEMINI_MODELS, good, "k")
    check("sahi model par warning nahi", problems, [])
    check("sahi model GONE nahi", [m for m in config.GEMINI_MODELS if m in health.GONE], [])

    def bad():
        return {"gemini-1.0-old"}
    try:
        problems = checkup._check("gemini", config.GEMINI_MODELS, bad, "k")
        gone = [m for m in config.GEMINI_MODELS if m in health.GONE]
    finally:
        reset()
    check("galat model warning di", config.GEMINI_MODELS[0] in " ".join(problems), True)
    check("saare galat model ek saath GONE", sorted(gone), sorted(config.GEMINI_MODELS))
    check("ek line per galat model", len(problems), len(config.GEMINI_MODELS))

    def raises():
        raise RuntimeError("network down")
    try:
        problems = checkup._check("gemini", config.GEMINI_MODELS, raises, "k")
        gone = [m for m in config.GEMINI_MODELS if m in health.GONE]
    finally:
        reset()
    check("list fail par warning", "model list nahi mili" in " ".join(problems), True)
    check("list fail par GONE nahi (network issue)", gone, [])

    check("key na ho par warning", checkup._check("groq", config.GROQ_MODELS, good, ""),
          ["groq: API key nahi hai"])


def test_banner():
    print("UI BANNER")
    reset()
    check("sab theek par banner khaali", checkup.banner(), "")
    health.model_gone("groq", "gone-model", "404")
    banner = checkup.banner()
    check("banner me warning", "Brain warning" in banner, True)
    check("banner me model naam", "gone-model" in banner, True)
    check("banner chhota", len(banner) <= 303, True)

    # Startup warning + health warning ek hi baar.
    reset()
    checkup.WARNINGS.append("groq model gone-model abhi available nahi hai")
    health.model_gone("groq", "gone-model", "404")
    banner = checkup.banner()
    check("dupe line hat gayi", banner.count("gone-model"), 1)

    index = (config.UI_DIR / "index.html").read_text(encoding="utf-8")
    check("index me placeholder", "__PRABH_BRAIN_WARN__" in index, True)
    check("banner div hai", 'id="brainwarn"' in index, True)
    # Phase 4 me style.css hud_*.css me split ho gaya — brainwarn ab hud_panel.css me hai.
    css = (config.UI_DIR / "hud_panel.css").read_text(encoding="utf-8")
    check("css me .brainwarn", ".brainwarn" in css, True)
    reset()


# Engine test memory me likhta hai - asli data/memory.json se door.
with isolated_data():
    for fn in (test_rid_events, test_checkup_lists_only, test_checkup_good_and_bad, test_banner):
        fn()

print("FAIL:", FAILED if FAILED else "koi nahi")
sys.exit(1 if FAILED else 0)
