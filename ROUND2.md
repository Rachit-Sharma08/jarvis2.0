# Round 2 — jaanch (poorī), fix abhi baaki

**Status: sirf jaanch poori. Ek bhi line code nahi likhi.**
Ye file ka ek hi kaam: kal jo karna hai uska poora record — saboot, plan, sawaal, keys.

Live test 30 Sept 2026 raat ko kiye gaye (asli API, `D:\prabh`, commit `c2c2c39` par).

---

## 1. Root cause: "Groq ne khaali jawab diya" — PAKDA GAYA

Sandeh sahi tha: `gpt-oss` ek **reasoning model** hai aur `brain/groq_client.py:38`
par `max_tokens=800` hai. Reasoning channel poora budget kha leta hai, `content`
kabhi aata hi nahi.

| Test (`max_tokens=800`) | finish_reason | reasoning | content |
|---|---|---|---|
| "test.txt bana do" | stop | 335 ch | 90 ch (JSON sahi) |
| "200 line python script" | **length** | 637 ch | 2702 ch (JSON **kat-ta**) |
| "HTML page bana do" | stop | **1074 ch** | **0 — KHAALI** |
| lambi history + script | **length** | **3227 ch** | **0 — KHAALI** |
| lambi history + script | **length** | **3396 ch** | **0 — KHAALI** |

6 me se **3 baar khaali** reproduce hua. Do failure:
1. `content` bilkul khaali (reasoning sab kuch kha gaya),
2. `finish_reason="length"` par JSON adhura (strict parser reject karega).

### Fix proof (live)
- `max_tokens=4000` → poora jawab 4200 ch, 10.2s ✅
- `reasoning_effort="low"` Groq **accept karta hai** → halka task 62→20 reasoning
  token (TPM bachta hai), par **akela kaafi nahi** (ek heavy task me phir bhi khaali)
- Isi test me asli **429 TPM** error aaya → 10 min cooldown sach me zaruri hai
- Gemini ka `max_output_tokens=800` bhi kam hai — 1600 karna hai

### Tools-prompt ka TPM par asar
`tools OFF = 364` prompt token, `tools ON = 646` → sirf **+282 token** per request.
Reasoning 300–3400 token le rahi hai, yaani tool-prompt bhaari nahi hai.
** Faisla: chhota karne ka fayda nahi, rehne do** (facts table ke liye zaroori hai).

---

## 2. Provider pool — research poori

| Provider | base_url | Bana hua? |
|---|---|---|
| Groq | `https://api.groq.com/openai/v1` | ✅ live 200 |
| Cerebras | `https://api.cerebras.ai/v1` | ✅ OpenAI-compatible (bina key 401) |
| Mistral | `https://api.mistral.ai/v1` | ✅ OpenAI-compatible (bina key 401) |
| OpenRouter | `https://openrouter.ai/api/v1` | ✅ list public (bina key 200) |
| Gemini | alag adapter | ✅ |

⚠️ **Badalna zaroori**: OpenRouter par aaj `gpt-oss-120b:free` **exist nahi karta**.
Public list me sirf paid `openai/gpt-oss-120b` ($0.037/M in) hai; free wala
`qwen/qwen3.8-27b:free`. User se poochha gaya — jawab baaki hai.

---

## 3. STT — Icelandic wala sach

- `language="hi"` lagane par aapki recording → `प्राबबाइट, आएज मासम काई साहा` (bakwaas).
  Bina hint → `Prabyte, Aaj Masam Kaisaha.` (saaf).
  **Yaani romanized Hinglish par `hi` hint nuksan-deh hai.**
- Hinglish `prompt` hint bhi khatarnak: khamoshi par whisper **prompt hi echo** karta
  hai — "Inglish. Romanized Hinglish bhi ho sakta hai." 0.5s par, "Hinglish bhi ho
  sakta hai." 0.8s par. Saath `<|hi|>` artifacts bhi aate hain.
- Khamoshi (0.3s–2s) par hamesha **"Thank you."** aata hai. Ye ASCII hai, isliye
  script-check nahi pakdega. **Asli ilaaj: duration check.**
- Duration ke liye browser se `ms` bhejna hoga. `ui/recorder.js` me abhi timer nahi
  hai — `began = Date.now()` + `onDone(blob, ms)`, phir `/stt?ms=`.
- Script guard kaam karta hai: `Hvað er þetta?` → reject ✅ · `प्रभु आज मौसम कैसा है`
  → pass ✅ · `Prabhu, aaj mausam kaisa hai` → pass ✅
- Venv me `mutagen`/`soundfile`/`pydub`/`av` koi nahi hai — webm duration ke liye
  library nahi jodenge, browser ka `ms` hi source of truth rahega.

---

## 4. Awaazein (live)

- **Jessica** `cgSgspJ2msm6clMCkdW9` (Sunday) → 200, 77 KB ✅
- **Matilda** `XrExE9yKIg1WjnnlVkGX` (Prabh) → 200, 84 KB ✅
- **Edge `en-IN-NeerjaNeural`** → 48 KB bana ✅ · `hi-IN-SwaraNeural` → 35 KB ✅
  Sunne ke liye: `%TEMP%\opencode\edge_neerja.mp3`, `edge_swara.mp3` (agent sun nahi sakta)
- **Cartesia** `GET https://api.cartesia.ai/voices` → 200 par **0 voices** (free tier me
  library nahi milti). Gender check API se nahi hoga. Simi voice female hai.
- Dono mode female-only: `FEMALE_ONLY_MODES` me **Sunday bhi** add, George
  (`JBFqnCBsd6RMkjVDRZzb`) hata dena hai.

---

## 5. Fix plan (user ke "haan" ka wait)

**Naye file:** `brain/openai_pool.py` (ek adapter: base_url + key + model),
`brain/pool.py` (ordered pool + retry + health), `brain/pool_config.py` (provider table
— `config.py` 199 lines par hai, isliye naya file), `server/brain_routes.py`
(`GET /brain/status`, token ke saath).

**Pool order:** groq/gpt-oss-120b → cerebras/gpt-oss-120b → groq/gpt-oss-20b →
mistral → gemini-3.5-flash → gemini-flash-latest → openrouter/free.
Jis ki key `.env` me na ho → chhoot jayega.

**Brain:** `reasoning_effort=low` + `max_tokens` 800→1600 (retry par 3200) ·
khaali / `finish_reason=length` / ghalat JSON = failure → 1 retry → agla provider ·
success par cooldown reset · start par har provider ki `/models` se check, configured
naam na mile to us provider ki list ka pehla valid model · sab fail par ek saaf message
me har provider ka chhota reason.

**STT:** `ms` bhejo, <600ms par "Kuch sunai nahi diya" · `<|hi|>` artifacts hatayo ·
script check (ASCII + Devanagari allowed) · `STT_LANGUAGE` config, default **khali**
(auto) — kyunki `hi` tera Hinglish bigaadta hai.

**Baaki:** label mode ke hisaab se (SUNDAY/PRABH) · dono mode female-only ·
Sunday chain = Jessica → Simi (Cartesia) → Neerja/Swara.

**Tests (naye, sab fake):** `test_pool.py`, `test_stt_guard.py`, `test_voices_female.py`,
`test_brain_status.py`. 15 suite + 4 naye = 19.

**Report me chahiye:** root cause + live result, aur `test.txt` wala task asli mein —
card aana chahiye, ALLOW dabane par file banna chahiye.

---

## 6. Abhi tak ke sawaal (user se poochhe, jawab nahi mila)

1. OpenRouter: `qwen/qwen3.8-27b:free` theek hai, ya paid `openai/gpt-oss-120b`?
2. Edge: Sunday ke liye **Neerja** ya **Swara**? (MP3 sunke batao)
3. Cartesia ki **Simi** voice Sunday ke liye bhi rakhu? (female hai, mid fallback)

## 7. Keys baaki (optional, ek-ek karke maangni hain)

`CEREBRAS_API_KEY` → `MISTRAL_API_KEY` → `OPENROUTER_API_KEY`
Teenon ke bina bhi pool Groq+Gemini se chalega. `.env.example` me sirf naam likhna hai.
