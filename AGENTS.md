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
  config_hud.py      -> HUD rang, weather (Delhi/15min cache), stats interval, 6 quick button
  log_setup.py       -> logs/prabh.log
  core/engine.py     -> message -> mode -> brain -> (tool loop) -> events
  core/events.py     -> status/message/log/activity/confirm
  core/modes.py      -> naam se mode + persona + label (SUNDAY/PRABH)
  core/timing.py     -> Stopwatch (stage + total ms)
  core/sysstats.py   -> psutil: CPU/RAM/battery/disk/network (1.5s cache, prime())
  brain/pool.py + pool_config.py -> POOL order (sirf yahin brain ka raasta)
  brain/openai_pool.py -> OpenAI-compatible adapter (chat + GET models_list)
  brain/limiter.py   -> NVIDIA pool-wide 30/min sliding window
  brain/health.py + health_words.py -> GONE/cooldown/credits-lock/quota + error words
  brain/probe.py     -> manual strict-JSON probe + 24h cache (startup par NAHI)
  brain/checkup.py   -> start par sirf free /models list check
  brain/prompt.py    -> persona + tool JSON rules + strict parser
  personas/sunday.txt, personas/prabh.txt
  config_desktop.py   -> tray rang, HUD size/path, crash backoff, exit codes, mic/lock helpers
  gatekeeper/keeper.py, rules.py, patterns.py, paths.py, approvals.py, limiter.py, audit.py
  tools/__init__.py, command.py, files.py, apps.py, system.py
  server/app.py      -> GET /, POST /chat, CSP headers + Referrer-Policy
  server/security.py -> token + Origin + Host check + same-origin GET ka proof
  server/state.py    -> POORA server ka ek shared Engine (sab yahin se)
  server/brain_routes.py   -> GET /brain/status
  server/tool_routes.py    -> /tool/confirm, /tools/toggle|cancel|status
  server/voice_routes.py   -> POST /stt, POST /tts
  server/hud_routes.py     -> GET /hud/stats, GET /hud/weather, POST /hud/quick
  server/ws_routes.py      -> WebSocket /ws (chat + har ~2s "stats" event)
  server/hub.py + drain.py -> thread-safe event hub + async generator drain
  server/weather.py        -> Open-Meteo fetch + 15 min cache + WMO labels
  voice/stt.py + stt_guard.py, voice/tts.py + tts_female.py + tts_*.py
  desktop/launcher.py -> supervisor: app crash ho to dobara (start_prabh.bat se chalta hai)
  desktop/app.py, tray.py, trayicon.py -> Sunday app: server thread + tray + HUD
  desktop/hud_window.py, single.py, state.py -> Edge --app, ek hi instance, ek STATE
  desktop/micperm.py, lockwatch.py -> Windows mic permission + lock ka pata
  wake/worker.py     -> abhi stub (READY=False); Step 1 me Vosk wala sunega
  start_prabh.bat    -> supervisor chalao (registry entry nahi, wo Step 3 ke aakhir me)
  ui/index.html, app.js (chat+ws glue), voice_ui.js (mic+speaker)
  ui/hud_base.css, hud_panel.css, hud_left.css, hud_center.css, hud_right.css, hud_bottom.css
  ui/hud_clock.js, hud_stats.js, hud_activity.js, hud_status.js, hud_orb.js,
  ui/hud_weather.js, hud_quick.js
  ui/hud_quick.js, hud_desktop.js (mic+wake ka sirf haalat)
  ui/recorder.js, speaker.js, tools.js (confirm card + ACTIVITY jodi)
  ui/fonts/*.woff2 + fonts.css (local, koi CDN nahi)
  tests/ (25 suite + poolhelp.py + desktophelp.py + hud_*.py — poori list TESTS.md me)
  README.md, VOICE.md, TOOLS.md, BRAIN.md, TESTS.md, ROUND2.md, CHANGELOG.md
```

### 3.3 Phase 5 desktop ke pakkaurey niyam

- **Ek hi supervisor.** App hamesha `desktop/launcher.py` se. Crash ka faisla
  `launcher.next_step()` (pure function) deta hai — usko process chala kar test karo,
  test me seedha yehi call karo. `desktop/app.py` me supervisor dobara mat banao.
- **Ek hi DesktopState.** `desktop/state.py` ka `STATE`. Tray ka rang, HUD ka DESKTOP
  pill aur wake worker teeno usi se padhein.
- **Registry me khud mat likho.** Auto-start entry (HKCU Run) sirf tab likhi jaye jab
  user ne is baar me **haan** kaha ho. Sirf script bana sakte ho. Test me startup
  entry kabhi register mat karo.
- **Duty cycle nahi.** Wake detector hamesha sunta rahega (energy gate sirf). CPU
  bachane ke liye on/off cycle mat lagao — mic har baar kholna crash ka raasta hai.
- **Mic permission check.** `desktop/micperm.py` se shuru me check karo, error ko
  `STATE.set_mic("error", reason)` me daal ke tray + HUD dono dikhao.
- **Lock pe TOOLS off, app nahi.** Locked hone par bhi wake/rendering chalta rahega.
- **Sirf Sunday.** `PRABH_SUNDAY_ONLY=1` (`config.SUNDAY_ONLY`). Prabh ka code
  maujood hai; mode switch flag se band hai. Test me flag off karke switch chalta
  hai ye bhi verify karte rahna.

### 3.1 Phase 4 HUD ke do naye pakkaurey niyam

- **Ek hi Engine.** `server/state.py` se lo. Kahin bhi naya `Engine()` mat
  banao — warna mode ek jagah lagega aur quick button doosri jagah se chalega.
- **Same-origin GET.** Browser GET par `Origin` header NAHI bhejta. Naya GET
  endpoint banao to `security.verify_request()` use karo (wo Referer ya
  `Sec-Fetch-Site: same-origin` proof maangta hai). Iske bina wo endpoint
  browser me hamesha 403 dega — jo `test_hud.py` ke `hud_check_get.py` me pakda
  gaya tha.

### 3.2 Phase 4 me live browser se pakde gaye 8 asli bug

Ye **sirf test se nahi**, asli Chrome (Playwright + system Chrome, 1366x768) khol kar
pakde gaye. Lesson: naya endpoint/UI bana kar sirf source-check mat karo — page
kholo aur `getBoundingClientRect` + computed style + network log dekho.

1. **Same-origin GET hamesha 403** — browser GET par `Origin` header bhejta hi nahi
   (sirf POST/PUT/DELETE + cross-origin par bhejta hai). Is liye `/brain/status` aur
   weather browser me **kabhi chalti hi nahi thi** (Phase 3/4 dono me chhupi hui thi).
2. **Grid overflow** — `grid-template-columns: 24% 50% 26%` + `gap` + `padding` =
   1366 viewport par 1372px (scroll bar). Ab `minmax(0, 24fr) minmax(0, 50fr) minmax(0, 26fr)`.
3. **Teen alag `Engine()`** — `app.py`, `ws_routes.py`, `hud_routes.py` — mode drift
   (`/chat` me PRABH, quick button SUNDAY). Ab ek `server/state.py`.
4. **Orb core kaali thi** — CSS `fill: radial-gradient()` SVG me valid NAHI hai.
   Ab `index.html` me `<radialGradient id="coreGrad">`.
5. **SYSTEM pill startup par OFFLINE** — `active_tier: null` (abhi koi message nahi).
   Ab ready provider (key hai + cooldown nahi) ho to ONLINE.
6. **STOP sirf awaaz** rokta tha — pending tool card nahi. Ab dono.
7. **`/hud/quick` extra fields ignore** — `{"id":"scan","tool":"run_command"}` chalti
   thi. Ab `QuickIn.model_config = ConfigDict(extra="forbid")` → 422.
8. **Chhote label bug** — network `MB` → `MB/s`, activity tag `DENY` → `DENIED`.

- Test: `tests/hud_check_get.py` (same-origin GET), `hud_check_api.py` (shared Engine).
- Tooling: Playwright/Pillow sirf verification ke liye the, venv se hata diye —
  `requirements.txt` me kuch nahi add hua. `psutil` hi naya dependency hai.
- **Reference photo ka comparison aankhon se nahi hua** (is model me image vision
  nahi). Sirf programmatic analysis + live measurements. Colour claim
  (navy/cyan/cream, amber nahi mila) ko ek naye test se dobara check karna hai —
  `tests/verify_image_assets.py` **abhi likha nahi gaya**, ye baaki kaam hai.
  Guess par bharosa na karna.

- **Tool ka ek hi raasta**: `engine.run_tool()` → `keeper.review()` → `tools.execute()`. Sunday aur Prabh
dono isi se guzarte hain. Engine me doosra raasta kabhi mat banao.
- **Brain ka ek hi raasta**: `engine` → `brain.pool.ask()`. Provider list sirf `brain/pool_config.py` me
badlo, engine ya brain me hard-code order mat likho.
- **TTS provider ka ek hi raasta**: `voice/tts.py`. Naya provider wahin chain me judega.
- **Mic/speaker browser me**: page ke andar `getUserMedia` + `MediaRecorder` + audio playback
ka raasta purana hai aur **badega nahi**. Phase 5 ke baad mic capture (wake + command) aur
speaker playback **Python** me hota hai — `wake/audio.py` (sounddevice) se input,
`desktop/playback.py` (sounddevice) se output. Sirf is **naya** raaste ke liye
`wave`/`sounddevice`/`miniaudio` allowed hain. `PyAudio`/`pyaudio` kabhi use mat karo.

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
- Ek request me **max 5 tool step** + **20 request/min**. Tools default **OFF**; restart = phir OFF. **30 minute
  baad khud ON karne par bhi apne aap OFF** (`Limiter.minutes_left()`). Delete hamesha **Recycle Bin**
  (`send2trash`) — permanent delete ka tool mat banao.
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

- 25 suite ki poori list, har suite ka detail aur naya test likhne ke niyam → **`TESTS.md`**.
- Exit code **0** hi asli "pass" hai. Kuch suite `print("FAIL:", FAILED if FAILED else "koi nahi")` likhte hain — `koi nahi` matlab **sab pass**.
- Poori suite **3–5 minute** leti hai. Terminal timeout na ho isliye `TESTS.md` me
  diye background wale tarike se chalao (Start-Job + result file).
- Pool test ke helpers `tests/poolhelp.py` me hain — naya pool test wahin se import kare.
- HUD test 4 helper me phaila hai (`hud_common`, `hud_check_ui`, `hud_check_get`,
  `hud_check_api`) — nayi assertion sahi helper me daalo, nayi file nahi.
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
- Naya HUD endpoint banao to `server/security.py` ka `verify_request()` use kar, aur Grid layout
  me `%` ki jagah `minmax(0, Nfr)` likh (gap + padding ke saath `%` overflow karta hai).
- Desktop ka koi bhi haalat (mic, mute, tools, HUD, wake) `desktop/state.py` ke `STATE`
  se padho. Naya `DesktopState()` mat banao.
- Desktop test me Edge/tray/mic/registry **kabhi chalao mat** — sirf command/path/faisla
  check karo. `launcher.next_step()` aur `gatekeeper` ke `Limiter` jaise pure helpers
  bana lo taaki test me process chane ki zarurat na pade.
- Crash/backoff/exit-code ka faisla **pure function** me rakho (`next_step(jawab, ...)`),
  taaki supervisor loop se alag test ho sake.

---

## ABHI KYA BAAKI HAI

- Round 2 poora ho gaya (1-2 Oct 2026). Plan/record `ROUND2.md` me padh sakte ho.
- **Phase 4 HUD poora ho gaya (1-2 Oct 2026).** Plan/record `CHANGELOG.md` me.
- **Phase 5 Step 3a (desktop shell) ho gaya (2 Oct 2026)** — supervisor + tray + Edge HUD +
  single instance + wake stub, 25 suite green. Plan `PLAN.md`, record `CHANGELOG.md` me.
- Baaqi Phase 5, isi order me: **Step 1** (Vosk wake word, model download ho chuka hai) →
  **Step 2** (VAD + command + Python playback) → **Step 3** auto-start (registry tabhi jab
  user "haan" bole). Face/trust/learn/maker baad me.
- Ek hi cheez aur baaki hai: **Cartesia ki female voice id** (`CARTESIA_VOICE_*`). Na mile to Cartesia skip hoti
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
- **Phase 4 (1-2 Oct 2026)** — 3-column HUD: `config_hud`/`sysstats`/`weather`, `hub`/`drain`/`ws_routes`,
  `hud_routes`, 7 naye `hud_*.js`, CSS 6 me split, local fonts (Orbitron/Rajdhani/Share Tech Mono),
  shared Engine (`server/state.py`), same-origin GET fix (Referer/`Sec-Fetch-Site`),
  grid `%` → `fr` overflow fix, SVG radialGradient, SYSTEM pill startup fix — **23 suite green**,
  live Chrome par 0 error, sab file `<200`.
- **Phase 5 Step 3a (2 Oct 2026)** — desktop shell: `config_desktop`, `desktop/`
  (launcher/app/tray/trayicon/hud_window/single/state/micperm/lockwatch), `start_prabh.bat`,
  `ui/hud_desktop.js`, wake stub, Sunday-only flag, TOOLS 30-min auto-off, Vosk model +
  pystray/sounddevice/vosk/miniaudio packages, `test_desktop*.py` + `desktophelp.py`
  — **25 suite green**. Auto-start registry entry jaan-boojh kar nahi likhi.
