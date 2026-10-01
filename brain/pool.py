"""Do-tier model pool. Tier 1 tez+stable, Tier 2 reserve.

Flow: Tier 1 ke providers pehle. Sab fail (ya cooldown par) ho to hi Tier 2.
Har provider fail hote hi agla turant try hota hai — wait nahi.

Ek provider ke andar: 1 retry (max_tokens badha kar) phir agla model, phir agla
provider. Retry sirf 'empty' par — 429/402/404 par retry bekaar hai.

Gemini OpenAI-compatible nahi, uske liye apna gemini_client (bhi 2500 tokens).
"""

import time

from brain import gemini_client, groq_client, health, openai_pool, pool_config
from brain.openai_pool import CallError
from log_setup import get_logger

log = get_logger("pool")

ACTIVE_TIER = None      # abhi kaunsa tier chal raha hai
ACTIVE_PROVIDER = None  # last successful provider
ACTIVE_MODEL = None     # last successful model


def _short(text: str, limit: int = 140) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "..."


def _ask_openai(provider: dict, history: list, persona: str, model: str) -> str:
    return openai_pool.chat(
        provider, history, persona, model,
        max_tokens=pool_config.MAX_TOKENS,
        temperature=pool_config.TEMPERATURE,
        reasoning_effort=pool_config.REASONING_EFFORT,
    )


def _ask_with_retry(provider: dict, history: list, persona: str, model: str) -> str:
    """1 retry, max_tokens 5000. Retry sirf 'empty' par."""
    try:
        return _ask_openai(provider, history, persona, model)
    except CallError as exc:
        if exc.kind != "empty":
            raise
        log.warning("%s %s khaali jawab — 1 retry (5000 tokens)", provider["name"], model)
        time.sleep(1.0)
        return openai_pool.chat(
            provider, history, persona, model,
            max_tokens=pool_config.MAX_TOKENS_RETRY,
            temperature=pool_config.TEMPERATURE,
            reasoning_effort=pool_config.REASONING_EFFORT,
        )


def _run_provider(provider: dict, history: list, persona: str, problems: list) -> tuple:
    """Is provider ko chalao. Ok -> (answer, model). Fail -> problems me daal ke ''."""
    name = provider["name"]

    if not pool_config.has_key(provider):
        problems.append(f"{name}: key nahi hai")
        return "", ""

    rest = health.blocked_reason(name)
    if rest:
        problems.append(rest)
        return "", ""

    # 404 ke baad bhi model list me agla valid model ho sakta hai.
    model = pool_config.pick_model(provider, health.GONE)
    if not model:
        problems.append(f"{name}: saare models 404")
        return "", ""

    if provider["api_style"] == "gemini":
        try:
            return gemini_client.ask(history, persona), provider["model"]
        except Exception as exc:
            problems.append(_short(f"{name}: {exc}"))
            health.fail(name, _kind_of(exc), str(exc))
            return "", ""

    if provider["api_style"] == "groq":
        try:
            return groq_client.ask(history, persona), provider["model"]
        except Exception as exc:
            problems.append(_short(f"{name}: {exc}"))
            health.fail(name, _kind_of(exc), str(exc))
            return "", ""

    try:
        return _ask_with_retry(provider, history, persona, model), model
    except CallError as exc:
        problems.append(_short(f"{name}: {exc}"))
        if exc.kind == "gone":
            # 404 permanent — agle valid model ko chance mile.
            health.model_gone(name, model, str(exc))
        elif exc.kind == "billing" and name in pool_config.FREE_ONLY:
            # Free-only provider: billing word = turant band (agle din tak).
            health.fail(name, "billing", str(exc), exc.retry_after)
        else:
            health.fail(name, exc.kind, str(exc), exc.retry_after)
        return "", ""
    except Exception as exc:
        problems.append(_short(f"{name}: {exc}"))
        health.fail(name, "other", str(exc))
        return "", ""


def _kind_of(exc: Exception) -> str:
    """Groq/Gemini client ka exception -> health category."""
    try:
        return health.classify(exc)
    except Exception:
        return "other"


def ask(history: list, persona: str) -> tuple:
    """(answer, provider_name). Sab fail = saaf message har provider ke reason ke saath."""
    global ACTIVE_TIER, ACTIVE_PROVIDER, ACTIVE_MODEL
    start = time.perf_counter()
    problems = []

    for tier in (pool_config.TIER1, pool_config.TIER2):
        for provider in pool_config.tier_order(tier):
            answer, model = _run_provider(provider, history, persona, problems)
            if answer:
                ACTIVE_TIER, ACTIVE_PROVIDER, ACTIVE_MODEL = tier, provider["name"], model
                took = int((time.perf_counter() - start) * 1000)
                log.info("TIME pool: T%d %s %s total %dms", tier, provider["name"], model, took)
                return answer, provider["name"]
        if problems:
            log.warning("Tier %d ke sab fail — agla tier", tier)

    problems += [_short(w) for w in health.warnings()]
    log.error("Pool fail: %s", " | ".join(problems), exc_info=True)
    return (
        "Abhi koi brain jawab nahi de paya. Ye reasons mila:\n"
        + "\n".join(f"- {p}" for p in problems),
        "none",
    )


def status() -> dict:
    """/brain/status ke liye. Koi key ya secret nahi — sirf naam/tier/cooldown."""
    providers = []
    for p in pool_config.all_tiers():
        providers.append({
            "name": p["name"],
            "tier": p["tier"],
            "model": pool_config.pick_model(p, health.GONE),
            "has_key": bool(p["key"]),
            "cooldown": health.cooldowns().get(p["name"], ""),
            "last_fail": health.last_fail(p["name"]),
        })
    return {
        "active_tier": ACTIVE_TIER,
        "provider": ACTIVE_PROVIDER,
        "model": ACTIVE_MODEL,
        "cooldowns": health.cooldowns(),
        "last_fail_reasons": {p["name"]: health.last_fail(p["name"]) for p in pool_config.POOL},
        "gone_models": dict(health.GONE),
        "providers": providers,
    }


def reset() -> None:
    """Test ke liye. Server restart par sab naya hota hai."""
    global ACTIVE_TIER, ACTIVE_PROVIDER, ACTIVE_MODEL
    ACTIVE_TIER = ACTIVE_PROVIDER = ACTIVE_MODEL = None
    health.reset_all()