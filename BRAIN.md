# Brain (sochne wala)

Brain ab ek **do-tier pool** hai. Ek hi provider par depend nahi karta.

| Tier | Provider | Model (pehle) | Timeout |
|---|---|---|---|
| **1** | Groq | `openai/gpt-oss-120b` | 10s |
| **2** | Gemini | `gemini-3.5-flash` | 15s |
| **2** | OpenRouter (`:free` sirf) | `nvidia/nemotron-3-super-120b-a12b:free` | 45s |
| **2** | Groq (dusra) | `openai/gpt-oss-20b` | 20s |
| **2** | NVIDIA NIM | `nvidia/nemotron-3-super-120b-a12b` | 25s |

Tier 1 tez aur reliable hai. Tier 2 sirf tab chalta hai jab Tier 1 ke sab fail ya
cooldown par hon. Har fail par agla provider **turant** try hota hai — wait nahi.

Poori list ek jagah: `brain/pool_config.py` → `POOL`. Nayi model yahan add hoti hai,
code me nahi. Models `config_brain.py` me hain.

## Fail par kya hota hai

| Kya mila | Kya hoga |
|---|---|
| `404` / `model_not_found` | Wo model **is session me hamesha ke liye hat** jaata hai, aur **usi provider ka agla model turant** try hota hai. Sab 404 ho to agla provider. |
| Khaali jawab ya `finish_reason=length` | 1 retry, `max_tokens` 2500 → 5000. Phir bhi khaali to agla provider. |
| (kyu?) | `reasoning_effort="low"` hamesha bhejna zaroori — warna reasoning model `max_tokens` ke andar sirf sochne me kharch kar deta hai aur content khaali aa jaata hai. |
| `429` / `503` / timeout | `Retry-After` header utha lo, warna **10 minute rest**. |
| `402` / "cloud credits expired" / "insufficient credits" | **Nayi key tak band** — "credits khatam — nayi key chahiye". Agle din tak nahi khulta. |
| Daily / monthly quota | **Agle 00:00 tak band** (credits se alag rule). |
| `401` | Key galat — nayi key tak band. |

Credits aur quota me jaan-boojhkar fark hai: quota apne aap theek ho jaata hai,
credits nahi. Word/pattern `brain/health_words.py` me, cooldown `brain/health.py` me.

## Free-only rule

NVIDIA aur OpenRouter **free-only** hain. Inke response me chhota billing/credit text
(`payment required`, `insufficient credits`, ...) aaya to provider turant band ho
jaata hai — paid model par jaane se pehle hi rok diya jaata hai. OpenRouter ki list
me sirf `:free` model hain; runtime par bhi check hota hai.

## NVIDIA: credits aur speed

- Key `nvapi-` se shuru hoti hai, `https://build.nvidia.com` se milti hai.
- Free trial **1000 credits**. Har probe call credit kharch karta hai.
- Credits khatam = HTTP **402 "Cloud credits expired"**. Public balance endpoint
  nahi hai — exact balance dashboard me dikhta hai.
- Per-key limit 40 RPM. Isliye `brain/limiter.py` me **pool-wide 30/min** sliding
  window hai — saare NVIDIA models milake.
- Credits khatam hone tak ye **sabse aakhri reserve** hai (Tier 2, list ke ant me),
  isliye tez providers pehle use hon.

## Model probe (credits kharo hain — soch ke chalao)

`brain/probe.py` strict JSON check karta hai: model se sirf
`{"text":...,"n":...,"ok":...}` maangta hai aur timing note karta hai.

- **Startup par probe NAHI chalta** — sirf free `GET /models` list check hoti hai.
- Har model par **max 2 call**. 8 second se zyada lage to wo model sirf Tier 2 me
  rahega (winner nahi banega).
- Result 24 ghante cache hota hai (`logs/probe_cache.json`) — dobara chalane par
  koi call nahi jayegi.

```powershell
cd D:\prabh
.\.venv\Scripts\python.exe -m brain.probe nvidia
.\.venv\Scripts\python.exe -m brain.probe openrouter --limit 3 --force
```

`--force` cache hata kar nahi probe karta — credits jayenge. Bina `--force` ke
24 ghante purana cache wahin se uth jaata hai, koi call nahi jayegi.

Sept/Oct 2026 ka live probe result (2 call/model):

| Provider | Model | Latency | Strict JSON |
|---|---|---|---|
| NVIDIA | `nvidia/nemotron-3-super-120b-a12b` | ~1.0s | **PASS** (winner) |
| NVIDIA | `nvidia/nemotron-3.5-lightning-30b-a3b` | 60s+ timeout | FAIL |
| NVIDIA | `nvidia/nemotron-nano-3-30b-a3b` | — | FAIL (404) |
| OpenRouter | `nvidia/nemotron-3-super-120b-a12b:free` | ~1.2s | **PASS** |
| OpenRouter | `qwen/qwen3.8-27b:free` | — | FAIL (429) |
| OpenRouter | `thinkingmachines/inkling:free` | — | FAIL |

Isi liye `:free` list me nemotron-super sabse upar hai, aur qwen/inkling sirf
backup me — wo aksar 429 dete hain.

## Server start par check

`brain/checkup.py` start par **sirf `GET /models`** dekhta hai (Groq, Gemini,
NVIDIA, OpenRouter). Koi chat ya generation call nahi — isliye credits nahi lagte.

- Model list me mila → theek. Nahi mila → wo model hata diya jaata hai.
- List hi nahi mili (network) → kuch nahi hata, sirf log. Server chalu rehta hai.

## `/brain/status` — pool ka live haal

```
GET /brain/status        (token + Host + Origin lagta hai)
```

```
{"active_tier": 1, "provider": "groq", "model": "openai/gpt-oss-120b",
 "cooldowns": {"gemini": "12 min baad", "nvidia": "credits khatam — nayi key chahiye"},
 "last_fail_reasons": {"openrouter": "429 rate limit"},
 "gone_models": {"qwen/qwen3.8-27b:free": "404"}, "providers": [...]}
```

Key/token jaisa koi field yahan **kabhi nahi** jata (naam se hata diya jaata hai),
aur har text `gatekeeper.audit.mask()` se guzarta hai.

## Sab fail hon to

Ek hi message, har provider ka ek kaaran — duplicate nahi:

```
Abhi koi brain jawab nahi de paya. Ye reasons mila:
- groq: 401 invalid api key
- gemini: 503 The model is overloaded
- nvidia: 402 Cloud credits expired
```

## Tools band ho to

Tools ON par poora tool JSON spec prompt me jaata hai. OFF par sirf persona + ek
chhoti line — token bachta hai. Server par `/tools/status` se badalta hai.

## Timing log

Har call `logs/prabh.log` me:

```
TIME groq: openai/gpt-oss-120b 1402ms | 412 chars
TIME pool: T1 groq openai/gpt-oss-120b total 1451ms
```

## Privacy warning (zaroori padho)

Ye app **free providers** par chalti hai (Groq, Gemini, OpenRouter, NVIDIA NIM) aur
**OpenAI-compatible** unke endpoints hain. Matlab:

- Jo bhi message ya file ka text prompt me gaya hai, wo us provider tak pahunch
  chuka hai. Gemini aur kai free providers apni training me istemal kar sakte hain.
- `read_file` se koi bhi text (resume, notes, ID proof, password wali file) brain
  tak ja sakta hai aur wahan save ho sakta hai.
- Isliye **personal ya private file ka content tool se mat pucho** — aur `.env`
  jaise secret files to hamesha BLOCKED hain hi.
- Koi bhi chat history server ke andar nahi bachti, par provider ke paas ja chuki
  hoti hai. Private baat rakhni ho to tools OFF rakho.

Ye warning sirf formality nahi — free tier ka asli hissa yahi hai.
