"""Brain ke provider constants — keys, models, tokens, timeouts.

`config.py` inhe re-export karta hai, isliye code me `config.GROQ_API_KEY`
hi likhna hai (seedha is file ka import mat karo).
"""

import config_env  # noqa: F401  (purane env naam pehle alias hote hain)
import os

# ---- Keys (asli values sirf .env se, kabhi code me nahi) ----

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# NVIDIA NIM — OpenAI-compatible. Key 'nvapi-' se shuru hoti hai.
# Free trial: 1000 credits (5000 business email se). Per-key 40 RPM.
# Credits khatam -> HTTP 402 "Cloud credits expired" (balance endpoint public nahi).
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "nvidia/nemotron-3-super-120b-a12b"
# Probe-verified Sept 2026 (har par 2 call). Pehla winner (1.0s, strict JSON pass).
NVIDIA_MODELS = (NVIDIA_MODEL, "nvidia/nemotron-3.5-lightning-30b-a3b")
# Pool-wide limiter: saare NVIDIA models milake 30/min (40 RPM limit se safe).
NVIDIA_MAX_CALLS_PER_MINUTE = 30

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Sirf :free. qwen/gemma aksar 429 dete hain — backup list rakhi hai.
OPENROUTER_MODELS = (
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3.8-27b:free",
    "thinkingmachines/inkling:free",
    "google/gemma-4-31b-it:free",
)

# ---- Ollama (offline last resort) ----
# Local model — internet band ho to bhi jawab. Models D:\ollama\models par
# (`OLLAMA_MODELS`), is liye C: bharata nahi. Key nahi maangta; `OLLAMA_KEY`
# sirf pool ke "key hai?" check ke liye hai.
OLLAMA_ENABLED = os.getenv("JARVIS_OLLAMA", "1") == "1"
OLLAMA_BASE_URL = os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434/v1")
OLLAMA_MODEL = os.getenv("JARVIS_OLLAMA_MODEL", "qwen2.5:3b-instruct")
OLLAMA_KEY = "local"

# ---- Models ----

# Live /models list par verify hua (Sept 2026). Purane naam 404 de rahe the.
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_MODELS = (GROQ_MODEL, "openai/gpt-oss-20b")
GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_MODELS = (GEMINI_MODEL, "gemini-flash-latest")

# ---- Timeouts + tokens ----

# Kitni der wait: Groq 10s, Gemini 15s. 402/429/503 par 10 min araam.
BRAIN_TIMEOUT_GROQ = 10.0
BRAIN_TIMEOUT_GEMINI = 15.0
GEMINI_RETRY_WAIT = 2.5
PROVIDER_SKIP_SECONDS = 600

# Round 2: pehle 800 tha. Reasoning model (gpt-oss) me reasoning tokens sab
# kha jate the aur content empty aata tha. Ab 2500, retry par 5000.
BRAIN_MAX_TOKENS = 2500
BRAIN_MAX_TOKENS_RETRY = 5000
BRAIN_REASONING_EFFORT = "low"


def has_groq() -> bool:
    return bool(GROQ_API_KEY)


def has_gemini() -> bool:
    return bool(GEMINI_API_KEY)


def has_nvidia() -> bool:
    return bool(NVIDIA_API_KEY)


def has_openrouter() -> bool:
    return bool(OPENROUTER_API_KEY)

MAX_MEM_TURNS = 12

