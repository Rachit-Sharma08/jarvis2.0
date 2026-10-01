"""Model pool ki list: provider, tier, preferred models, tokens, limits.

Ek jagah se poori chain control hoti hai. Naya provider/model yahan add hota hai,
code me nahi. 'latest' naam par bharosa nahi — preferred list ke order me
probe-verified model pehle, phir baaki valid candidates.
"""

import config

# Tokens. config me ek hi source hai (BRAIN_MAX_TOKENS).
MAX_TOKENS = config.BRAIN_MAX_TOKENS
MAX_TOKENS_RETRY = config.BRAIN_MAX_TOKENS_RETRY
REASONING_EFFORT = config.BRAIN_REASONING_EFFORT
TEMPERATURE = 0.7

TIER1, TIER2 = 1, 2

# Provider ka free-only flag. Response me billing/payment/insufficient_credit
# dikhe to turant band. OpenRouter sirf ':free' model.
FREE_ONLY = ("nvidia", "openrouter")

# Ye words kisi bhi response me dikhe to provider free-only hone par band.
BILLING_WORDS = (
    "payment required", "insufficient_credit", "insufficient credit",
    "insufficient_credits", "insufficient funds", "billing", "payment",
    "add credits", "credits expired", "credit balance is too low",
    "exceeded your current quota", "purchase", "subscription",
)


def _p(**kw) -> dict:
    """Provider ka ek entry. Tier 1 = tez+stable, Tier 2 = reserve."""
    base = {
        "tier": TIER2, "timeout": 20.0, "retries": 1, "rate_limit": 0,
        "api_style": "openai", "key": "", "models": (), "model": "",
    }
    base.update(kw)
    return base


# ---- Pool order (list ka order hi failover order hai) ----

POOL = (
    # Tier 1 — tez aur stable. Groq gpt-oss-120b abhi sabse reliable.
    _p(name="groq", tier=TIER1, timeout=10.0, api_style="groq",
       key=config.GROQ_API_KEY, model=config.GROQ_MODEL,
       models=(config.GROQ_MODEL, "openai/gpt-oss-20b")),

    # Tier 2 — reserve. T1 sab fail ho tabhi yahan aata hai.
    _p(name="gemini", timeout=15.0, api_style="gemini",
       key=config.GEMINI_API_KEY, model=config.GEMINI_MODEL,
       models=(config.GEMINI_MODEL, "gemini-flash-latest")),

    _p(name="openrouter", timeout=30.0, key=config.OPENROUTER_API_KEY,
       base_url=config.OPENROUTER_BASE_URL,
       # Sirf :free. Probe-verified Sept 2026.
       models=("qwen/qwen3.8-27b:free", "nvidia/nemotron-3-super-120b-a12b:free",
               "google/gemma-4-31b-it:free", "nvidia/nemotron-3.5-lightning:free"),
       model="qwen/qwen3.8-27b:free"),

    _p(name="groq_slow", timeout=20.0, api_style="groq", key=config.GROQ_API_KEY,
       model="openai/gpt-oss-20b", models=("openai/gpt-oss-20b",)),

    # NVIDIA sabse aakhri reserve — credits limited (1000) aur per-key 40 RPM.
    # Isliye pool-wide 30/min limiter (rate_limit=30) lagta hai.
    _p(name="nvidia", timeout=25.0, rate_limit=30,
       key=config.NVIDIA_API_KEY, base_url=config.NVIDIA_BASE_URL,
       model=config.NVIDIA_MODEL,
       models=(config.NVIDIA_MODEL, "nvidia/nemotron-3.5-lightning-30b-a3b")),
)


def by_name() -> dict:
    return {p["name"]: p for p in POOL}


def has_key(provider: dict) -> bool:
    return bool(provider["key"])


def tier_order(tier: int) -> list:
    return [p for p in POOL if p["tier"] == tier]


def all_tiers() -> list:
    return sorted(POOL, key=lambda p: p["tier"])


def pick_model(provider: dict, gone: dict = None, limit: int = None) -> str:
    """Preferred order me pehla model jo 404 (gone) nahi hua.

    - 429/402/timeout par model list khatam nahi hoti — sirf provider cool down
      hota hai. Isliye 'gone' sirf 404 ke liye.
    """
    gone = gone or {}
    limit = limit or len(provider["models"])
    for model in provider["models"][:limit]:
        if model not in gone:
            return model
    return ""


def billing_hit(text: str) -> str:
    """Response me billing/credit word hai? Free-only provider turant band."""
    low = (text or "").lower()
    for word in BILLING_WORDS:
        if word in low:
            return word
    return ""