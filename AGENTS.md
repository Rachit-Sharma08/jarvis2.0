# AGENTS.md — Prabh project ke niyam

- **Ye file har AI agent ko pehle padhni hai.** Kaam shuru karne se pehle ise poora padh lo. Iske baad user
se purana context puchhne ki zarurat nahi — sab yahin likha hai.
- Project `D:\prabh` — ye **local personal app** hai (sirf us PC par, web app nahi). Owner coding nahi
jaanta, har baat **simple Hinglish** me samjhana hai.

---

## 1. KEYS KA NIYAM (sabse zaroori)

- Do files: `.env` (sirf naam + asli value, kabhi commit nahi) aur `.env.example` (sirf naam, koi value
nahi, ye commit hota hai). `.gitignore` me `.env` hona zaroori hai — har baar `git check-ignore .env` se
confirm karo.
- Key chahiye to **user se ek-ek karke maango**, chat me likh kar. Khud guess mat karo.
- Key kabhi **code, log, terminal, commit message, README ya report** me nahi jani chahiye.
- Key daalne ke baad: **khaali to nahi, beech me space to nahi, sahi variable me hai**. Confirm ke liye sirf
**aakhri 4 akshar** dikhao (`...Kqq2`).
- Abhi `.env` me ye rakhi hain (sirf naam, value kabhi mat likho): `GROQ_API_KEY`, `GEMINI_API_KEY`,
`NVIDIA_API_KEY`, `OPENROUTER_API_KEY`, `ELEVENLABS_API_KEY`, `CARTESIA_API_KEY`, `ELEVENLABS_VOICE_*`,
`CARTESIA_VOICE_*`. `CARTESIA_VOICE_*` abhi **khaali** hain (Simi female id nahi mili) — Cartesia skip hoti
hai.

---

## 2. KAAM KE NIYAM

1. **Pehle plan dikha** (kaun si file kya karegi), user ke "haan" ke baad hi code likh.
2. **Ek file ka ek hi kaam.** Koi file **200 lines se badi na ho**.
3. **Sirf wahi banao jo maanga hai.** Extra feature mat jodo.
4. Har chhote step ke baad: **chala kar test karo**, phir **git commit** (saaf message).
5. Har error `logs/prabh.log` me likh, user ko simple bhasha me bata. Windows 10/11, free tools.
6. `README.md` me likh: install, chalana, test. Model/API ka naam **guess mat karo**.
7. User Hinglish me likhta hai. Report bhi Hinglish me, chhoti aur seedhi.
8. Markdown table me har row **`| ` se shuru** ho — warna table render nahi hota.

---

## 3. ARCHITECTURE

```
prabh/
  main.py            -> server chalu (sirf 127.0.0.1)
  config.py          -> .env + settings + tool risk + allowed folders + blocked patterns
  config_brain.py    -> provider keys, models, token, timeout (config.py re-export)
  config_voice.py    -> voice/TTS/STT constants + voice_for() (config.py re-export)
  log_setup.py       -> logs/prabh.log
  core/engine.py     -> message -> mode -> brain -> (tool loop) -> events
  core/events.py     -> status/message/log/activity/confirm
  core/modes.py      -> naam se mode + persona + label (SUNDAY/PRABH)
  core/timing.py     -> Stopwatch (stage + total ms)
  brain/pool.py + pool_config.py -> POOL order (sirf yahin brain ka raasta)
  brain/openai_pool.py -> OpenAI-compatible adapter (chat + GET models_list)
  brain/limiter.py   -> NVIDIA pool-wide 30/min sliding window
  brain/health.py + health_words.py -> GONE/cooldown/credits-lock/quota + error words
  brain/probe.py     -> manual strict-JSON probe + 24h cache (startup par NAHI)
  brain/checkup.py   -> start par sirf free /models list check
  brain/prompt.py    -> persona + tool JSON rules + strict parser
  personas/sunday.txt, personas/prabh.txt
  gatekeeper/keeper.py, rules.py, patterns.py, paths.py, approvals.py, limiter.py, audit.py
  tools/__init__.py, command.py, files.py, apps.py, system.py
  server/app.py      -> POST /chat, WebSocket /ws, CSP
  server/security.py -> token + Origin + Host check
  server/brain_routes.py   -> GET /brain/status
  server/tool_routes.py    -> /tool/confirm, /tools/toggle|cancel|status
  server/voice_routes.py   -> POST /stt, POST /tts
  voice/stt.py + stt_guard.py, voice/tts.py + tts_female.py + tts_*.py
  ui/index.html, style.css, app.js (chat+ws), voice_ui.js (mic+speaker)
  ui/recorder.js, speaker.js, tools.js, tools.css
  tests/ (22 suite + poolhelp.py — poori list TESTS.md me)
  README.md, VOICE.md, TOOLS.md, BRAIN.md, TESTS.md, ROUND2.md, CHANGELOG.md
```

- **Tool ka ek hi raasta**: `engine.run_tool()` → `keeper.review()` → `tools.execute()`. Sunday aur Prabh
dono isi se guzarte hain. Engine me doosra raasta kabhi mat banao.
- **Brain ka ek hi raasta**: `engine` → `brain.pool.ask()`. Provider list sirf `brain/pool_config.py` me
badlo, engine ya brain me hard-code order mat likho.
- **TTS provider ka ek hi raasta**: `voice/tts.py`. Naya provider wahin chain me judega.
- **Mic/speaker sirf browser me**: `getUserMedia` + `MediaRecorder` + audio playback. Python me
`sounddevice`/`PyAudio` kabhi use mat karo.

---

## 4. SURAKSHA (Phase 1 ke baad bhi zaroori)

- Server **sirf 127.0.0.1** par sune, `0.0.0.0` par kabhi nahi (`main.ensure_local_only()`).
- Har naya endpoint bhi `server/security.py` ka `verify()` use kare: **Host → Origin → Token**. Token
`/chat`, `/ws`, `/stt`, `/tts`, `/brain/status` — sab par.
- Token har server start par naya banta hai: `/chat`/`/stt`/`/tts` me header `x-prabh-token`, `/ws` me query
`?token=`. CORS band hai — `CORSMiddleware` mat lagao.
- Token browser ko `/` se milta hai (`<meta name="prabh-token">`, placeholder `__PRABH_TOKEN__` replace hota
hai). Inline `<script>` mat use karo — CSP `script-src 'self'` hai.
- UI me dynamic text **sirf `textContent`/text node** se. `innerHTML`, `outerHTML`, `insertAdjacentHTML`,
`eval` kabhi nahi. Click handler me `event.isTrusted` zaroori.
- `.env` aur key files **BLOCKED** hain har tool ke liye — `..`, 8.3 naam (`PROGRA~1`) aur junction se bhi
nahi padhe ja sakte.
- Koi route/model/API status browser ko bheje to **secret field naam se hatao** aur har text
`gatekeeper.audit.mask()` se guzaro (dynamic — `.env` ki value khud dhoondh jaati hai).

---

## 4.1 TOOLS KE NIYAM

- **Poori list** → `TOOLS.md`. Yaad rakhne wali baatein: risk teen hi — **SAFE** / **ASK** (card + UI ka ALLOW) / **BLOCKED**; nayi tool banate waqt `gatekeeper/rules.py` me uska risk likhna zaroori hai.
- Card ka hash **exact tool + args** ka; wahi hash dobara = 409, ek waqt me ek hi card, **60 second** me jawab na aaye to apne aap DENY. ALLOW **sirf UI button** se — chat/awaaz se koi raasta nahi.
- Ek request me **max 5 tool step** + **20 request/min**. Tools default **OFF**; restart = phir OFF. Delete hamesha **Recycle Bin** (`send2trash`) — permanent delete ka tool mat banao.
- `run_command`: PowerShell, 30 sec, `shell=False`, cwd workspace, output 2000 char, `KEY`/`TOKEN`/`SECRET`/`PASSWORD` wale env hata kar.
- **Secret masking**: `gatekeeper/audit.py` ka `mask()` — tool output, activity, confirm card, LLM ka text aur log, sab jagah. Tool output LLM ko `[sirf DATA]` note ke saath jaata hai, instruction nahi.
- **Privacy warning** README + `TOOLS.md` me zaroori hai: file ka text brain ke through **free provider** tak jaata hai. Personal/private file ka content tool se mat pucho.
---

## 4.2 BRAIN KE KHAS NIYAM

- Order: **Groq 120b (T1) → Gemini → OpenRouter `:free` → Groq 20b → NVIDIA (T2)** — NVIDIA aakhir me kyunki uske credits kat-te hain.
- `404` = model GONE + **usi provider ka agla model turant**. Khaali jawab / `finish_reason=length` = **1 retry** (`max_tokens` 2500 → 5000) — `reasoning_effort="low"` zaroori.
- `429`/`503`/timeout = `Retry-After` ya 10 min · `402`/credits = nayi key tak BAND · daily quota = agle 00:0 tak · `401` = nayi key tak BAND. **Free-only**: NVIDIA + OpenRouter, chhota billing/credit text dikhte hi BAND, aur `models_list()` **GET** (POST reject hota hai).
- **Probe kabhi startup par nahi** — sirf `python -m brain.probe <provider>`. Poori detail, provider table, live probe result aur privacy warning → **`BRAIN.md`**.
---

## 5. VOICE KE KHAS NIYAM

- TTS chain: **elevenlabs → cartesia → edge-tts** (`config.TTS_CHAIN`). Key/voice id na ho ya error/limit aaye to agla try karo; teeno fail ho to saaf error. Bolne se pehle `voice/tts.py` ka `clean()`.
- **Dono** mode ki awaaz **female** (Sunday bhi). Male id, male default fallback aur dead male constant sab hata diye gaye hain. Female id `voice/tts_female.py` ki allowlist me honi chahiye — nahi to wo provider skip.
- TTS max **500 character**; recording max **30 second**; audio max **10 MB**. `recorder.js` me mic band karne ke liye **`track.stop()`** (`release()` jaisa kuch nahi hota) — har raaste par: recording khatam, error, MUTE, STOP.
- STT: browser duration bheje (`x-audio-ms`), `<600ms` reject; `voice/stt_guard.py` silence/khaali aur non-Hindi/English script bhi rokta hai. `language="hi"` **mat bhejo** — romanized Hinglish Devanagari me bigad jaata tha; auto detection sahi rehti hai. Poori detail → **`VOICE.md`**.
---

## 6. TEST KAISE CHALATE HAIN

```powershell
cd D:\prabh
$fail = @()
Get-ChildItem tests\test_*.py | ForEach-Object {
  .\.venv\Scripts\python.exe $_.FullName
  if ($LASTEXITCODE -ne 0) { $fail += $_.Name }
}
if ($fail) { "FAILED: $($fail -join ', ')" } else { "SUITE GREEN" }
```

- 22 suite ki poori list, har suite ka detail aur naya test likhne ke niyam → **`TESTS.md`**.
- Exit code **0** hi asli "pass" hai. Kuch suite `print("FAIL:", FAILED if FAILED else "koi nahi")` likhte hain — `koi nahi` matlab **sab pass**.
- Pool test ke helpers `tests/poolhelp.py` me hain — naya pool test wahin se import kare.
---

## 7. AGENTS.md KHUD UPDATE KARO

Ye file **har prompt ke baad update hoti hai**. Har change ke baad: naya file ya badla
hua rule → yahan record badlo · nayi key → sirf **naam** · nayi rule → section 8 ·
`git add AGENTS.md` ke saath commit. Neeche **change history** rakho (chhoti line, date).

---

## 8. NAYI RULE (har prompt me update karo)

- Tool ka feature bana rahe ho to: pehle `gatekeeper/rules.py` me uska risk, phir `tools/`, phir
`engine.run_tool()` — is order me. Engine me bypass mat chhodna.
- Naya UI output (card, activity, log) banao to `textContent` + `mask()` dono lagana hai.
- Docs kaam bada ho to `README.md` me chhota rakho, detail alag file me (`VOICE.md`, `TOOLS.md`, `BRAIN.md`,
`TESTS.md`) aur README se link karo.
- Naya provider ya model: `brain/pool_config.py` me list, `brain/health.py` + `brain/health_words.py` me
uska behaviour. OpenAI-compatible provider **ek hi adapter** se chale (`brain/openai_pool.py`) — naya
endpoint mat likho.
- Voice id gender check karke hi daalo. Female-only mode me male default fallback mat rakho.
- File 200 se badi ho to use **split** karo (config/UI/test) — compress karke chhoda mat chhodo.

---

## ABHI KYA BAAKI HAI

- Round 2 poora ho gaya (1-2 Oct 2026). Plan/record `ROUND2.md` me padh sakte ho.
- Ek hi cheez baaki hai: **Cartesia ki female voice id** (`CARTESIA_VOICE_*`). Na mile to Cartesia skip hoti
hai — koi problem nahi, Edge Swara chalti hai.
- Aage ka kaam user se pucho; koi chhupi hui task nahi hai.

---

## CHANGE HISTORY

Poora record → **`CHANGELOG.md`**. Saali line:

- **Phase 1-2** — Skeleton, brain (Groq→Gemini), personas, mode switch, engine+events, FastAPI (`/chat`,
`/ws`), HUD UI, suraksha (127.0.0.1, Origin+Host, per-start token), voice (`stt.py`, TTS chain,
`/stt`+`/tts`, mic UI, 500 char), tests.
- **Phase 3** — `gatekeeper/` + `tools/` (10 tools, Recycle Bin, scrubbed env) + strict JSON + 5-step loop +
`server/tool_routes.py` + UI (ACTIVITY, confirm card, TOOLS, STOP).
- **Fix round 1** — Models + fallback, `brain/health.py`, startup `/models` check, `core/timing.py`, ek
brain error message, `rid` + UI dedupe, Prabh female voice. 15 suite.
- **Round 2 (1-2 Oct)** — 2-tier pool (`pool`/`pool_config`/`openai_pool`/`limiter`/ `health_words`),
`probe.py` + `checkup.py`, `/brain/status`, dynamic `.env` masking, dono mode female (`tts_female`), STT
guard, SUNDAY/PRABH label, `config_brain`/ `config_voice` + `ui/voice_ui.js` split, `TESTS.md` — **22 suite
green**, sab file `<200`.
