"""Server start par halki jaanch: sirf models-list endpoint, ek bhi LLM token nahi.

Sirf ye pata karta hai ki config me likha model abhi available hai ya nahi.
List call fail ho to model ko permanent ban NAHI karte (network issue hoga) —
sirf warning log aur UI banner me dikhta hai.
"""

import httpx

import config
from brain import health, openai_pool, pool_config
from log_setup import get_logger

log = get_logger("checkup")

GROQ_LIST = "https://api.groq.com/openai/v1/models"
GEMINI_LIST = "https://generativelanguage.googleapis.com/v1beta/models"
TIMEOUT = 5.0

WARNINGS = []


def _groq_models() -> set:
    reply = httpx.get(GROQ_LIST, headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
                      timeout=TIMEOUT)
    reply.raise_for_status()
    return {item["id"] for item in reply.json().get("data", [])}


def _gemini_models() -> set:
    reply = httpx.get(GEMINI_LIST, params={"key": config.GEMINI_API_KEY}, timeout=TIMEOUT)
    reply.raise_for_status()
    return {item["name"].replace("models/", "") for item in reply.json().get("models", [])}


def _check(provider: str, models, fetch, present: str) -> list:
    if not present:
        return [f"{provider}: API key nahi hai"]
    try:
        available = fetch()
    except Exception as exc:
        message = f"{provider}: model list nahi mili ({type(exc).__name__}) — skip nahi kiya"
        log.warning("checkup: %s", message)
        return [message]
    missing = [m for m in models if m not in available]
    for model in models:
        if model in available:
            log.info("checkup: %s model %s OK", provider, model)
    for model in missing:  # saare galat models ek saath hatao, ek ek karke nahi
        health.model_gone(provider, model, "models list me nahi hai")
        log.warning("checkup: %s model %s hata diya gaya", provider, model)
    return [f"{provider} model {model} abhi available nahi hai" for model in missing]


def _nvidia_models() -> set:
    """Sirf /models list — isme koi token/credit nahi lagta, isliye startup me safe."""
    provider = pool_config.by_name()["nvidia"]
    return set(openai_pool.models_list(provider))


def _openrouter_models() -> set:
    provider = pool_config.by_name()["openrouter"]
    return set(openai_pool.models_list(provider))


def run() -> list:
    """Startup me chalao. Returns UI banner ke liye ek line per problem.

    Round 2: startup par KABHI probe nahi chalta (credits lagega). Sirf free
    /models list dekhi jaati hai. Probe chahiye to `python -m brain.probe`.
    """
    warnings = _check("groq", config.GROQ_MODELS, _groq_models, config.GROQ_API_KEY)
    warnings += _check("gemini", config.GEMINI_MODELS, _gemini_models, config.GEMINI_API_KEY)
    warnings += _check("nvidia", config.NVIDIA_MODELS, _nvidia_models, config.NVIDIA_API_KEY)
    warnings += _check("openrouter", config.OPENROUTER_MODELS, _openrouter_models,
                       config.OPENROUTER_API_KEY)
    WARNINGS[:] = warnings
    if warnings:
        log.warning("startup jaanch: %s", " | ".join(warnings))
    else:
        log.info("startup jaanch: saare configured models available hain")
    return warnings


def banner() -> str:
    """Chhota sa message jo UI par dikhta hai. Yehi line do baar na aaye."""
    lines = list(WARNINGS)
    for line in health.warnings():
        if "hata diya gaya" in line:
            model = line.split("model ", 1)[1].split(" hata diya gaya")[0]
            if model in " ".join(lines):
                continue  # startup warning me already bata diya
        lines.append(line)
    if not lines:
        return ""
    return "Brain warning: " + " | ".join(dict.fromkeys(lines))[:300]
