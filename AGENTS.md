# AGENTS.md — Prabh project ke niyam

- **Ye file har AI agent ko pehle padhni hai.** Kaam shuru karne se pehle ise poora padh lo. Iske baad user
se purana context puchhne ki zarurat nahi — sab yahin likha hai.
- Project `D:\prabh` — ye **local personal app** hai (sirf us PC par, web app nahi). Owner coding nahi
  jaanta, har baat **simple Hinglish** me samjhana hai.
- **Nayi session me sabse pehle `NEW_AGENT_BRIEF.md`** — wo ek self-contained prompt hai jo naye
  agent ko project ka pura context deta hai (kya hai, kya use hua hai, kahan tak pahuncha, kya
  bacha hai, kaam karne ke niyam). User use nayi Claude/agent chat me paste karta hai.
- **Roadmap planning se pehle `docs/ROADMAP_STATUS.md` ke relevant section padho.** Wo file
  owner ka hai (Stage 02-06 ka status, S1 scoreboard, S5 15 bugs + guards, S7 free-only stack,
  S8 task order D-1..T-18, S11 progress log). **Ek time par sirf ek T-xx**, VERIFY wale point
  me pehle code padh kar confirm karo, aur naya package/provider bina owner se poochhe mat jodo.
  Status/plan update yahin karo — `S11 Progress log` me ek line, `docs/ROADMAP_STATUS.md` ko
  `opencode.json`/instructions me mat daalo (har request me context + free quota khatam hoga).

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
  config.py          -> .env + settings + allowed folders + blocked patterns + re-exports
  config_tools.py    -> tool risk, allowed folders, blocked patterns (config.py re-export)
  config_brain.py    -> provider keys, models, token, timeout (config.py re-export)
  config_voice.py    -> voice/TTS/STT constants + voice_for() (config.py re-export)
  config_hud.py      -> HUD rang, weather (Delhi/15min cache), stats interval, 6 quick button
  log_setup.py       -> logs/prabh.log
  core/engine.py     -> message -> mode -> brain -> (tool loop) -> events
  core/events.py     -> status/message/log/activity/confirm
  core/modes.py      -> naam se mode + persona + label (JARVIS/PRABH)
  core/timing.py     -> Stopwatch (stage + total ms)
  core/sysstats.py   -> psutil: CPU/RAM/battery/disk/network (1.5s cache, prime())
  brain/pool.py + pool_config.py -> POOL order (sirf yahin brain ka raasta)
  brain/openai_pool.py -> OpenAI-compatible adapter (chat + GET models_list)
  brain/limiter.py   -> NVIDIA pool-wide 30/min sliding window
  brain/health.py + health_words.py -> GONE/cooldown/credits-lock/quota + error words
  brain/probe.py     -> manual strict-JSON probe + 24h cache (startup par NAHI)
  brain/checkup.py   -> start par sirf free /models list check
  brain/prompt.py    -> persona + tool JSON rules + strict parser
  personas/jarvis.txt, personas/prabh.txt
  config_desktop.py   -> tray rang, HUD size/path, crash backoff, exit codes, mic/lock helpers,
                        HUD_HOTKEY + HUD_SHORTCUT_NAME
  config_wake.py      -> wake word, VAD, command window, WhatsApp call ke constants
  config_tray.py      -> tray watchdog ki timing (taskbar me icon dikhta hai ya ^ me)
  config_name.py      -> assistant ka naam (ASSISTANT_NAME/DISPLAY_NAME) + wake shabd
                         (+ purane "sunday" shabd LEGACY_WAKE_PHRASES me, default band)
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
  desktop/launcher.py -> app/tray/hud_window/single/state/micperm/lockwatch/startup.py
  desktop/actions.py  -> tray ke 5 button ka faisla (mute/HUD/TOOLS/restart/quit)
  desktop/callbacks.py -> app ke 4 callback ka matlab (lock/tools/wake/hotkey), app.py se alag
  desktop/startup.py  -> startup ki 4 line + say_hud()/say_wake() (line yahin banti hai)
  desktop/hotkey.py   -> global hotkey (Ctrl+Alt+S), sirf ctypes + RegisterHotKey
  desktop/tray_watch.py -> tray icon ka haal (taskbar me dikhta hai ya ^ me chhupa);
                           sirf registry PADHTA hai, app kabhi likhta nahi
  desktop/playback.py -> Step 2 speaker: TTS bytes -> miniaudio PCM -> sounddevice
  desktop/open_hud.py -> shortcut + hotkey dono ka EK raasta (server zinda -> HUD)
  desktop/autostart.py -> Windows login par chalu (HKCU Run, pythonw desktop/launcher.py);
                           sirf main() likhta hai, module me koi registry call nahi
  desktop/shortcut.py + hud_shortcut.ps1 -> Desktop ka "Jarvis HUD" .lnk banao/hatao
  wake/worker.py     -> Step 1 ka module-level raasta (poori app me EK worker)
  wake/session.py    -> mic + loop: chunk -> VAD/gate -> Vosk (thread, pause, mic retry)
  wake/trigger.py    -> trigger ka faisla: cooldown + final/partial/flush -> on_wake
  wake/lifecycle.py  -> Session ka zindagi hissa: mic band, state, crash-safe callbacks
  wake/gate.py       -> "Vosk ko ye chunk chahiye?" + silence par flush (battery)
  wake/utterance.py + wake/wav.py -> Step 2a: command capture + WAV
  wake/listen.py     -> Step 2c ka mic wala hissa: drain/warmup/capture/to_text (STT)
  wake/command.py    -> Step 2c ka flow: ack -> suno -> brain -> awaaz (policy nahi)
  wake/audio.py      -> sounddevice se 16 kHz mono (mic ka EK owner) + energy Vad + PCM
  wake/model.py      -> Vosk model load + cache (khaali ya error = ModelMissing)
  wake/detect.py     -> KaldiRecognizer ka wrapper: JSON -> saaf text
  wake/phrase.py     -> "jarvis" pakadna — pure functions
  start_prabh.bat    -> supervisor chalao (registry entry nahi, wo Step 3 ke aakhir me)
  ui/index.html, app.js (chat+ws glue), voice_ui.js (mic+speaker)
  ui/hud_base.css, hud_panel.css, hud_left.css, hud_center.css, hud_right.css, hud_bottom.css
  ui/hud_clock.js, hud_stats.js, hud_activity.js, hud_status.js, hud_orb.js,
  ui/hud_weather.js, hud_quick.js
  ui/hud_quick.js, hud_desktop.js (mic+wake ka sirf haalat)
  ui/recorder.js, speaker.js, tools.js (confirm card + ACTIVITY jodi)
  ui/fonts/*.woff2 + fonts.css (local, koi CDN nahi)
  tests/ (52 suite + poolhelp.py + desktophelp.py + hud_*.py + wakehelp.py + wakecmdhelp.py — poori list TESTS.md me)
  README.md, VOICE.md, TOOLS.md, BRAIN.md, TESTS.md, ROUND2.md, CHANGELOG.md
  docs/ROADMAP_STATUS.md  → OWNER ka roadmap-vs-reality + free-only plan (S1..S11). Roadmap
                            planning se pehle iska relevant section padho; naya task bhi wahin likho.
```

### 3.5 Voice privacy ke pakkaurey niyam

- **Wake word detection poori tarah local; wake ke baad command ki recording memory
  me bante hi Groq STT ko network par jaati hai, disk par kabhi save nahi hoti.**
  (Vosk offline hai — koi recording provider ko nahi jaati. Sirf command jaati
  hai, aur woh bhi byte buffer — koi file likhi jaati hi nahi.)
- **Wake flow ka recording kabhi file me mat likho** (debug bhi nahi). `wav.to_wav`
  sirf `io.BytesIO` me hai — wahi sahi tareeka hai.
- **Awaaz se ALLOW kabhi nahi.** `wake/command.py` me `keeper.approve/deny/wait`
  ka koi bhi reference nahi hai; card sirf dikhta hai, faisla screen ke button se.
  Test me ye **AST** se check hota hai — docstring me likha text count nahi hota.

### 3.6 Step 2c (wake command) ke pakkaurey niyam

- **`on_wake(phrase, mic, stop)`** — `wake/trigger.py` teeno deta
  hai, kahin aur se mic **kabhi** mat lo. Ye **synchronous** hai (wake thread par),
  is liye command poore chal jaane tak sunna ruka rehta hai aur dobara "Jarvis"
  trigger nahi hoga.
- **Mic ke chaar kaam `wake/listen.py` me** (`drain`/`warmup`/`capture`/`to_text`),
  flow `wake/command.py` me. `listen` ko brain/policy ki knowledge mat do — mute
  aur lock ka faisla `desktop/callbacks.py` ka `allowed()` callback deta hai (taaki
  `wake/` ko `desktop/` ka import na karna pade).
- **Pause ke do alag kaam hain:** `set_paused()` = tray ka MUTE (user ka faisla,
  hamesha), `hold_for_command()` = command ka temporary hold. Beech me MUTE aaye
  to `_HELD` clear ho jaata hai — **MUTE haar nahi maarta**.
- **Bole hue to aawaaz dobara trigger na ho:** `run()` ke `finally` me mic queue
  `drain()` hoti hai *tabhi* hold chhoda jaata hai. Warna `Session._loop` TTS ko
  `jarvis` samajh kar phir uth jaata.
- **`via="voice"`** — wake se aaye har engine event par ye lagta hai aur
  `ui/app.js` us par **browser TTS skip** karta hai (warna do awaaz). Likh kar
  bheja hua message ka raasta badalta nahi — wo waise hi bolega.
- **Stage time** `core/timing.py` ke `Stopwatch` se ek line me:
  `ack / warmup / capture / stt / brain / speak`. `tts` aur `play` ka apna time
  `voice/tts.py` aur `desktop/playback.py` alag log karte hain — `playback.say()`
  ek hi raasta hai, is liye usko do hisson me mat todo.
- **Mute ya PC lock par command bilkul nahi chalta** — na record, na koi awaaz,
  na brain. Sirf `logs/prabh.log` me ek line.

### 3.4 Bat file aur log ke pakkaurey niyam

- **`.bat` me raw `(` / `)` kabhi mat likho** (echo ya comment me bhi nahi) —
  `cmd` ka `if not exist (...)` block beech me toot jaata hai aur baaki ki
  line HAMESHA chalu ho jaati hai. Isi wajah se Phase 5 me python launch hi
  nahi hua tha. Block chahiye to `goto :label` use karo. Test: `tests/test_bat.py`.
- **`.bat` hamesha CRLF** (LF nahi) aur ASCII only. Windows LF-only batch file
  ko ajeeb se parse karta hai.
- **Log ASCII.** `log_setup.ascii_text()` + `AsciiFormatter` — console `cp1252`
  hai, is liye em-dash/Devanagari log me `??` ban jaate hain. Naya log text
  likhte waqt ASCII hi rakho.
- **Crash kabhi chup mat ho.** `desktop/launcher.py` ka `_console()` console
  par bhi bolta hai; `_tee()` child ka output console + `logs/desktop.out`
  dono me bhejta hai. Naya crash chup-chaap nahi rehna chahiye.
- **Startup ki 4 line ek jagah**: shabd `config_desktop.STARTUP_*` me, bolta
  sirf `desktop/app.py` (`desktop/startup.py` ka `say()`). Koi dusra module
  "HUD ready" ya "server up" na bole.

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
- **Sirf Jarvis.** `PRABH_SUNDAY_ONLY=1` (`config.SUNDAY_ONLY`). Prabh ka code
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
   (`/chat` me PRABH, quick button JARVIS). Ab ek `server/state.py`.
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

- **Tool ka ek hi raasta**: `engine.run_tool()` → `keeper.review()` → `tools.execute()`. Jarvis aur Prabh
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
- **Dono** mode ki awaaz **female** (Jarvis bhi). Male id, male default fallback aur dead male constant sab hata diye gaye hain. Female id `voice/tts_female.py` ki allowlist me honi chahiye — nahi to wo provider skip.
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

- 52 suite ki poori list, har suite ka detail aur naya test likhne ke niyam → **`TESTS.md`**.
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
- Yahi Desktop shortcut ke liye bhi: `shortcut.command()` ki list check karo,
  `shortcut.install()/remove()` **kabhi mat bulao** (warna asli Desktop ka `.lnk`
  bigad jaata hai).
- **`RegisterHotKey` bhi asli mat chalao** — `Hotkey(api=StubApi())` se. Aur stub me
  `threading.get_ident()` record karwao: register aur pump **ek hi thread** par hone
  chahiye. (2-Oct ka asli bug yahi tha.)
- Crash/backoff/exit-code ka faisla **pure function** me rakho (`next_step(jawab, ...)`),
  taaki supervisor loop se alag test ho sake.
- **"Pehle se chal raha hai" jaisa koi bhi message `pid_alive()` + `GET /` 200 — dono check
  karne ke baad hi bolna hai.** Sirf lock dekhna kaafi nahi. Ek hi raasta:
  `desktop/single.py` ka `diagnose(pid_probe=None, http_check=None)` (test me dono probe
  daalte hain, asli process/socket nahi chhua jaata).
- **PID probe me `os.kill(pid, 0)` bilkul mat likhna** — CPython isay `TerminateProcess`
  bana sakta hai. Safe raasta `pid_alive()` ka `_PROC_QUERY` + `OpenProcess`.
- **App bina tray ke chalte mat rehne do.** `tray.retry_start()` 3 koshish; phir bhi icon na
  bane to `config.EXIT_NO_TRAY` (4) se saaf exit. `run()` me `_start_tray()` ke baad
  `self._stop.is_set()` check zaroori hai, warna app aage badh jaata hai.
- **Stale PID file lock milne par apne aap hatni chahiye** (`_clean_stale_pid()`). Windows par
  `msvcrt` lock marne par khud release ho jaata hai — asli stale **lock** rare hai, stale
  `.pid` file common hai.
- **Cache sirf `speak_cached()` me, `speak()` me bilkul nahi.** `voice/tts.py` ka
  `speak()` sirf `_speak_uncached()` ka `return await` wrapper hai. `await` bhool
  gaye to caller ko nested coroutine milta hai aur test me
  `cannot unpack non-iterable coroutine object` aata hai — asli me TTS chup ho
  jaata hai. Cache **fail par store na kare** (warna app hamesha "nahi bola"
  repeat karegi, recovery nahi hogi) aur **bounded** rahe (`CACHE_MAX`).
- **"Time lag raha hai" par pehle log padho, brain ko mat shak karo.** Wake path
  ka ek line pura hisaab deta hai: `TIME wake_command: TOTAL ... | ack=... warmup=...
  capture=... stt=... brain=...`. Brain alag `TIME tts`/`brain` me hai. 3-Oct ko
  brain 1.1 s tha aur der wake path me thi — `settled_by` (ack se pehle) + cache +
  `COMMAND_END_SILENCE` se fix hui.
- **Deadline pattern: jo kaam peeche chal raha hai, uska time pehle se `settled_by`
  bana do.** `wake/command.py` me ack `speak()` ke **pehle** `settled_by =
  stage() + COMMAND_WARMUP_SECONDS` banta hai, phir `listen.warmup(...,
  deadline=settled_by)`. Is liye 2 s ki ack ke dauraan 1 s ka warm-up apne aap poora
  ho jata hai. Deadline nahi de rahe to `warmup` poora wait karega (test raasta).
- **Purana process chal raha ho to code badalne ka koi matlab nahi.** 3-Oct ko
  `GET /` raw `__PRABH_ASSISTANT_NAME__` de raha tha jabki `fill_html()` code me
  theek tha — sirf woh **purana launcher/app** chal raha tha. Code badalne ke baad
  app **restart** karna ya rehne dena, dono me se ek jaan-boojh kar chuno.
- **200 lines cross karte hi split karo, aur test ke fake bhi usi raaste pe
  shift karo.** `desktop/playback.py` 205 hua to `desktop/playback_cli.py`
  (`--list`/`--say` + `devices()`) bana. Sirf file nahi — do test me bhi
  `playback.main(...)` aur `playback.devices()` references badalne pade. Naya
  module bana kar sirf production file copy karna **chup-chaap fail** kar deta hai.
- **Wake worker ka ek hi raasta** `wake/worker.py`. Kahin bhi `wake.session.Session()`
  mat banao — poori app me **ek** worker. `desktop/app.py` sirf `start/stop/state`,
  tray ka MUTE sirf `worker.set_paused()`.
- **Mic ka ek hi owner `wake/audio.py`.** Naya `sounddevice.InputStream` kahin aur mat
  banao (`wake/session.py` bhi wahin se chunk leta hai). VAD + `chunk_to_rms()` bhi usi
  file me — pure hain, is liye test me bina mic ke chal jaate hain.
- **Speaker ka ek hi raasta `desktop/playback.py`.** Naya `sd.play` / `OutputStream`
  kahin aur mat likho, aur koi provider wahan mat chuno — awaaz hamesha
  `voice/tts.py` se (`say()` sirf bajata hai).
- **`miniaudio.decode` likhna, `decode_file` nahi.** `decode_file` sirf filename
  leta hai; bytes dene par wo poora audio buffer apne `FileNotFoundError` message
  me daal deta hai (terminal par MB ka dump). Isi wajah se probe/output kabhi
  kabhi binary se flood ho jaata hai — **bade output ko file me likho**, console
  par mat pheko.
- **`sd.query_devices(kind="output")` list NAHI deta** — sirf default output device
  ka ek dict deta hai (sounddevice 0.5.6). List ke liye `sd.query_devices()`
  (bina argument) + `max_output_channels > 0` filter. `playback.devices()` me yahi.
- **`decoded.samples` me `bytes()` mat lagao** — miniaudio ka array int16 se seedha
  padha ja sakta hai: `np.asarray(samples, dtype="<i2")`. `bytes()` par wapas raw
  bytes bante hain jo int16 me galat padhe jaate hain.
- **Playback test me asli speaker kabhi na baja.** `miniaudio` + `sounddevice` ke
  fake `tests/desktophelp.py` me `install_audio()` se `sys.modules` me daalo
  (playback late import karta hai, is liye bas yahi kaafi hai) aur `voice/tts.speak`
  ko badal do. Asli check `python -m desktop.playback_cli --say "..."` se.
- **Test file 200+ ho to theme ke hisaab se todo**, aur **helper class/function ko
  module level par rakh** — use hone wali function me chhod diya to doosri me
  `NameError` se **silent fail** ho jaata hai (aisa hi hua: `Ok`/`boom` split ke
  baad local reh gaye, 2 check chup-chaap False hue). Naya file banakar
  `TESTS.md` ki table me row zaroor daalo. `test_desktop.py` ka hygiene check
  ab **har** `tests/test_*.py` par `<=200` lines lagata hai — is liye split ke
  baad koi badi file chup-chaap nahi reh sakti.
- **Callback ka signature badle to saare caller fake update karo — aur chup-chaap
  fail hone mat do.** Step 2c ne `on_wake(phrase)` badal kar `on_wake(phrase, mic,
  stop)` kiya; test ka `heard.append` ek-arg wala tha → `TypeError` → `Session._fire()`
  ke `except Exception` ne pakad liya → **koi crash log nahi, trigger hi nahi**. Isi
  tarah `worker.start()` jaisa koi bhi cheez `stop.is_set()` se guard ho to us par
  depend mat karo. Naya fake callback hamesha **saare args** signature me rakho.
- **Test ko app ke **chal raha hai** ya na chal raha par depend mat karo.** Ye
  `desktop/single.py` ke test me hua: `acquire()` → `diagnose()` → **asli** HTTP se
  8000 par poochta hai, aur "CHAL raha hai" shabd tabhi aata hai jab server sach me
  chalu ho — app band ho to fail. Fake probe daalne ka raasta na ho to sirf wo
  **guarantee** check karo jo asli state se depend nahi karta (jaise "stale" shabd
  kabhi nahi aayega), aur wording fake-probe test me rakho.
- **Wake test me asli mic / Vosk model / sounddevice kabhi mat chalao.** Fakes
  `tests/wakehelp.py` me hain; `Session.start()` sirf **do** cheez maangta hai —
  `wake.session.detect.build` aur `wake.session.audio_mod.MicSource` (wahi patch karo).
  Model ke sirf **error** raaste check karo, `load()` chala kar 1s + RAM mat lagao.
- **`worker.wakes()` poore app ka count hai** (reset nahi hota). Test me do baar
  compare karna ho to pehle `before = worker.wakes()` pakad lo.
- **Startup ki nayi line `desktop/startup.py` me banti hai** (`say_hud()` /
  `say_wake()`); `app.py` sirf `ok/reason` ka faisla deta hai. Warna shabd 2 jagah
  chala jaata hai aur source-check wala test fail hota hai.
- **Git push ka token remote URL me kabhi nahi.** Push ke liye ek-kaam ka **temp
  askpass** (repo ke bahar, `%TEMP%`) + `git -c credential.helper=`, phir turant
  delete. `.git/config` me token nahi jaana chahiye — wahan sirf token-free URL.
- **PowerShell se repo ki text file mat badlo.** `Get-Content -Raw` + `Set-Content`
  UTF-8 file ko **double-encode** kar deta hai — poora diff bikhre hue `â` jaise
  akshar se bhara ho jaata hai. File badalni hai to `edit` tool ya Python
  (`encoding="utf-8"`) use karo.
- **Assistant ka naam ek hi jagah se: `config_name.py`.** UI/tray/shortcut/docs me
  "Jarvis" **hard-code mat karo**. Saccha raasta: `config_name.ASSISTANT_NAME` /
  `DISPLAY_NAME`. UI me `index.html` placeholder rakho (`__PRABH_ASSISTANT_NAME__` /
  `__PRABH_DISPLAY_NAME__`), `server/app.py` ke `fill_html()` se bharo, aur JS me
  `meta[name="prabh-name"]` se padho. `config_desktop.py` me `HUD_SHORTCUT_NAME` /
  `TRAY_TITLE` / `TRAY_NAME` f-string se bante hain.
- **Mode id `"sunday"` jaan-boojh kar mat badlo.** Step 1 me naam badla, **id nahi**
  — `config.SUNDAY_ONLY`, `PRABH_SUNDAY_ONLY`, `ELEVENLABS_VOICE_SUNDAY`,
  `CARTESIA_VOICE_SUNDAY` abhi bhi `sunday` hi hain. Ye internal hai (screen par
  nahi aata); rename karne se env keys aur voice id toot jaayengi.
- **`currentMode` JS me lowercase mode **id** rakho, label nahi.** `ui/app.js` me
  `ev.data.mode.toUpperCase()` ki wajah se wahi value `voice.speak()` me jaati thi —
  `voice_for(provider, "SUNDAY")` match hi nahi karta, provider chhoot jaata hai.
  Display ke liye meta se padha hua `LABEL` alag rakho.
- **UI grep test me teen exception jaan-boojh kar:** comment line, quoted mode id
  `"sunday"`, aur `hud_clock.js` ka `DAYS` array (calendar ka din, assistant ka naam
  nahi). `tests/test_name_jarvis.py` ye teen chhodta hai, baaki har "Sunday" FAIL
  hota hai. Ye test khud bhi pakadta hai — ek baar `hud_stats.js` me `"Sunday"`
  daal ke FAIL dekh liya tha.
- **Naam badalne par test bhi badalna mat bhoolna.** Sirf UI nahi — `test_wake.py`,
  `test_wake_loop.py`, `test_wake_worker.py` ke fake bhi naye shabd bolte hain, aur
  `test_desktop_tray.py` / `test_desktop_shortcut.py` tooltip/shortcut naam check
  karte hain. Purana test chup-chaap fail ho sakta hai kyunki fake listener naye
  shabd par trigger hi nahi karta.
- **Test asli `data/` ko kabhi nahi chhoo sakta (E-1b) — `tests/datasafe.py` ka
  `isolated_data()` (plain test) ya `DataSafeCase` (unittest setUp/tearDown).**
  Helper test ke dauran `config.DATA_DIR`, `config.ACTION_LOG`,
  `core.memory` (DATA_DIR/MEM_FILE/SUM_FILE), `core.summarizer`, aur
  `tools/` ke `todo/reminders/notes/rss/pomodoro/kb` path ek **tmp** folder par
  daalta hai, `MEM._items` khaali karta hai (asli file ko chhue bina), aur tearDown
  par sab wapas. Guard: koi path asli `data/` me gir gaya to **AssertionError**.
  Naya test agar `engine.handle()` / asli `/chat` route / `MEM.clear()` /
  `config.DATA_DIR` chhue to **pehle yehi helper lagega**. `grep` se dhoondhna
  kaafi nahi — `test_security.py`/`test_tool_routes.py` asli `/chat` se memory
  likhte the aur grep me nahi dikhe the; pakadne ka pakka tareeka: har test file
  chalane se pehle/baad me `data\memory.json` ka SHA256 compare karo.

### 8.1.1 BATTERY AUR TIMING KE PAKKAUREY NIYAM (4 Oct 2026)

- **Vosk ko HAR chunk mat do — `wake/gate.py` ka faisla suno.** Purana loop har 30 ms
  chunk recognizer ko deta tha, is liye khamoshi me bhi **~4.8% core** chalu tha (RAM
  154 MB). Ab VAD se "bol rahe ho?" puchha jaata hai; `False` par chunk recognizer tak
  **jaata hi nahi**. Mic ka stream kabhi band nahi hota (duty-cycle niyam mehfooz) — sirf
  inference rukti hai, is liye "Hlo Jarvis" har waqt chalta hai. `.env` ke
  `PRABH_VOSK_GATE=0` se purana behaviour wapas (debug). Napi napa: **4.8% → 0.9%**.
- **`InputStream.read()` blocking hai — uske baad `sd.sleep()` mat lagao.** Purane
  `_pump` me `read()` + `sd.sleep(30ms)` dono the, is liye chunk asli me **~43 ms** me
  aata tha. Do nuksan: CPU dobara jaagna, aur `utterance.capture()` chunk **ginti** par
  chalti hai — to "0.9 s chuppi" asli me 1.4 s thi (jawab late) aur log ka ms jhootha
  (`82 chunk = 2460ms` jabki asli 3.5 s lage). Ab cadence sach me 30 ms hai.
- **App ka core (server/tray/psutil) idle me bhi ~1.4% core leta hai** — `psutil`
  `interval=None` hai (blocking nahi), 3 `time.sleep()` loop hain (`app.py` 0.6 s,
  `lockwatch` 2 s, `startup` 0.4 s). Wake band karke baseline measure kar sakte ho
  (`PRABH_WAKE=0` + launch, phir 30 s CPU sample) — **app ko blame karne se pehle
  number nikaalo**.
- **Doosra InputStream se mic ki RMS mat naapo — sabse pehla `InputStream` zeros deta
  hai** (device already app ke paas busy). Asli level ke liye app band karo, phir
  `sounddevice` se direct probe chalao (probe likhna ho to `%TEMP%\opencode` me,
  repo me nahi).
- **200 lines cross karte hi split karo — gate ka seam `wake/gate.py` hai.**
  `session.py` 200 par tha; VAD + khamoshi ka hisaab + "feed karun?" ka faisla nayi
  pure file me gaya (mic/thread/Vosk chahiye hi nahi — `tests/test_wake_gate.py` seedha
  usi par chalta hai). `Session._fire()` ab sirf `text` leta hai (`_fire(text, vad)`
  nahi) — reset `self._gate.reset()` khud karta hai.
- **`config.describe()` me naya field = uska test bhi update.** Ab 5 hisse
  (`... stt=groq-whisper gate=on`); `tests/test_wake.py` me "5 hisse" check hai.
- **PowerShell me apne hi process ko `Stop-Process` mat karo.** `Get-CimInstance
  Win32_Process | Where CommandLine -like "*desktop.*"` me **apna powershell bhi**
  aata hai (uske `-Command` me wahi shabd hota hai) — pura shell mar jaata hai aur
  aage ka output khatam. Hamesha `$_.Name -like "python*"` se filter karo.

---

### 8.1.2 BATTERY / SPEED KE PAKKAUREY NIYAM (4 Oct 2026) — Step 2 se 5

- **"So jao" ka guard do jagah hai, dono ek jaisa honge** — `desktop/sleep.py`
  ka `matches()` (pure) aur `wake/command.py` ka `_is_sleep()`. `wake/` ko
  `desktop/` ka import nahi karwana (niyam), is liye code duplicate hai:
  `tests/test_desktop_sleep.py` har `config.SLEEP_WORDS` shabd **dono** guard me
  check karta hai. Ek jagah shabd add karke doosri chup nahi kar sakte.
- **Chhota-text guard zaroori hai** (4 shabd se kam). "Band ho jao kya matlab
  hai" jaisa vaakya sun kar app galti se so na jaye. Ye guard hi sleep ka asal
  nuksan rokta hai.
- **`sleep_mod.enter()` ka try/except crash ko so jane se nahi rokta** — HUD band
  na bhi ho to `asleep=True` set hona chahiye (test me `hud.close` crash karke
  check karta hai). Aise hi `wake_up()` sirf flag hatata hai; HUD/command ka kaam
  `callbacks.on_wake()` karta hai — **jaagne ka ek hi raasta**.
- **Sleep = mic band nahi.** Puri band sirf tray ke Quit se (CPU 0), aur uske baad
  "Jarvis" **kaam nahi** karega. Ye user ko bata-na zaroori hai (VOICE.md me likha
  hai) — warna "band karo" bolke phir "Hlo Jarvis" kaam na kare to bug samajh
  nahi aayega.
- **`drain()` peek se PEHLE chalta hai, aur peek ke baad `warmup()` nahi.**
  Isi liye wake shabd ki goonj chhoot jaati hai. Galat order me user ki "Hlo Jarvis
  ke saath boli hui" awaaz drain ho jayegi — `tests/test_wake_ack.py` isi liye
  `drain_six` (6 chunk) fake use karta hai; poora `drain()` (400 chunk) hone se
  test chup-chaap galat pass hota hai.
- **`peek_speech()` chunk phenkta nahi, wapas daalta hai.** `queue.put_nowait`
  full ho to break — pura data chala gaya behne se behtar hai, par ise chup-chaap
  mat karo (test me queue full wala raasta add kar lo).
- **Awaaz ki limit sirf awaaz par hai, HUD par nahi** (`tts.clip_answer` +
  `VOICE_ANSWER_MAX_CHARS=220`). Brain ka poora text `HUB` events me jaata hai —
  kati hui copy sirf `speak()` ko.
- **`clip_answer()` vaakya ke end par katta hai**, beech se nahi; ek hi lambe
  vaakya me `clip()` par hafta. Chhoti lineen bhi rakho (ACK, sleep ack, confirm) —
  TTS + playback me hi seconds lagte hain.
- **Tools ka default aur auto-off alag-alag switch hain.** `TOOLS_ENABLED_DEFAULT`
  (`PRABH_TOOLS_ON`) = shuru me ON/OFF; `TOOLS_AUTO_OFF_MINUTES`
  (`PRABH_TOOLS_AUTOOFF`) = timer, `0` matlab **kabhi nahi**. `Limiter._expire()`
  `auto_off <= 0` par khud early-return karta hai — alag code mat likho. Ye setting
  `config_tools.py` me hai (tools ke constants ka ghar), `config.py` se hi
  re-export hota hai.
- **`config.py` me naya constant bhoolna sabse aam galti hai.** Har nayi
  `config_*.py` me jo cheez bani wahan **aur** `config.py` ke import list me bhi
  joga, warna `AttributeError` test me hi pakda jaata hai (Step 5 me 3 suite isi
  wajah se palat gaye the).
- **`wake/` file 200 cross kare to seam `ask.py` hai** — `listen.py` mic ka hissa,
  `ask.py` brain + speaker ka. `command.py` sirf flow rahega. Split ke baad
  `tests/wakecmdhelp.py` ke helpers check karo: `talk()` ko dono `HUB` patch karwane
  do, aur `gatekeeper_uses()` **dono** file scan kare (warna AST wala safety check
  khud chup ho jaata hai).

### 8.1.3 WAKE KE TEEN RAASTE + SPLIT KE PAKKAUREY NIYAM (5 Oct 2026)

- **200 lines cross karte hi split karo — seam `trigger.py` hai.** `session.py`
  235 par tha. Ab teen file: `session.py` (mic + loop, 175) · `trigger.py`
  (trigger ka faisla + cooldown) · `lifecycle.py` (`_end`/`_fail`/`_close`/`_say`).
  Sirf production file copy karna chup-chaap fail karta hai — test ke fake bhi
  naye module ka naam lete hain (`session_mod.detect`, `worker.wakes()`).
- **`Listener.reset()` se PEHLE `flush()` karo.** Purana gate silence par sirf
  `reset()` karta tha, jisse Vosk ka pending partial chhoot jata tha — "ek command
  ke baad doosra nahi chalta" ka asli bug. Ab teen raaste: `final` (purana),
  `partial` (naya, tez), `flush` (`FinalResult()` se wapas). Trigger ka faisla
  **ek** jagah: `wake/trigger.py`.
- **Vosk grammar me poori phrase mat likho — shabd likho.** Kaldi multi-word
  phrase apne lexicon se map nahi kar pata; live me `"hello jarvis"` do tukde me
  toot gaya (`'hello'`, phir `'yo'`). `config_name.grammar_words()` har shabd
  alag deta hai + `[unk]` **aakhri** (beech me test `words[-1]` par fail hota hai).
- **`Trigger` ek hi instance hai** (`Session.__init__` me, `set_callbacks()` se
  callbacks badalte hain). Har `start()` par naya banao to `worker.wakes()` ka
  app-lifetime count reset ho jata hai — AGENTS ka "count reset nahi hota" niyam.
- **Naye `start()` par cooldown saaf karo** (`Trigger.reset_cooldown()`), warna
  restart ke baad pehla "Jarvis" 1.5 s tak pakda hi nahi jata — test bhi isi
  wajah se chup-chaap fail hota hai.
- **`stop()` me join timeout ke baad `_close()` mat karo.** Loop abhi bhi
  `self._listener`/`self._mic` use kar raha hai; `_thread = None` karne se agla
  `start()` **doosra** loop chala deta hai (ek Session, do loop). Zinda thread par
  `return` + warning.
- **Mic busy par retry, crash par nahi.** `Session._open_mic()` sirf
  `MicUnavailable` par `MIC_OPEN_ATTEMPTS` (3) koshish; constructor/model ka
  crash turant upar jaata hai (warna asli bug chup ho jayega). Naye env key
  `.env` + `.env.example` + `config.py` export teenon me daalo.
- **Vosk debug line hamesha band.** `PRABH_WAKE_DEBUG=0` — `.env` me chhod ke mat
  bhoolna (`logs/prabh.log` me har 3 s ek line).
- **Guard sirf route me mat rakho — library me bhi rakho.** 10 MB ki limit
  sirf `server/voice_routes.py` par thi, is liye `test_voice.py` 11 MB ka blob
  **asli Groq par upload** kar raha tha (suite 3+ min atki, quota bhi gaya).
  Ab size guard `voice/stt.py` me hai — har caller (HTTP + wake path) ke liye.
  **Test me provider API kabhi sach me call na ho:** agar test direct library
  call karta hai to pehle guard check karo, warna suite chup-chaap hang ho jayega.

## 8.1.4 HUD WINDOW KE PAKKAUREY NIYAM (13 Oct 2026 — R-2)

- **"Pehle se khuli hai" check ka return value ZAROOR propagate karo.** Yahi asli
  bug tha: `hud_window._focus_existing()` `EnumWindows` se window dhoondta tha, par
  aakhir me `return False` likha tha — matlab "window mili" ka faisla **lapiset** ho
  jaata tha. `open()` is liye har baar naya browser chala deta tha: 4 wake = 4
  window. **Dhoondhne wala koi bhi hissa (EnumWindows / list scan / grep) chahe
  `nonlocal` flag se ho ya return se — caller ko sach milna chahiye, warna har call
  naya kaam karta rahega.** Test me iska pakkaura: `focus_existing()` window
  maujood hone par `True` return kare (`test_desktop_hud_single.py`).
- **Browser window ka pakka signal TITLE hai, process nahi.** Edge `--user-data-dir`
  wale launch par `Popen` ka process window bane se **pehle** hi mar sakta hai (kaam
  dusre browser process ko bhej deta hai) — `self._proc.poll()` se "khuli hai" ka
  faisla galat hota hai. `is_open()` ab bhi **window** se puchhta hai.
- **`--app` window me title page ka hota hai, URL ka nahi.** `ui/index.html` ka
  `<title>__PRABH_ASSISTANT_NAME__ HUD</title>` → `server/app.py` ke `fill_html()`
  bhar deta hai → asli title `Jarvis HUD`. `win_find.is_hud_title()` exact title +
  URL + `config.DISPLAY_NAME` pakde; **sirf `'Jarvis'` se nahi** (warna user ka
  apna "Jarvis - Wikipedia" tab bhi pakad lete).
- **"Dheere khulne wali" window ka bhi ek hi raasta ho.** Edge window 1-2 s me
  banata hai — usi der me dobara spawn = 2 window. `SPAWN_GRACE_SECONDS` (8 s)
  isi ke liye hai: abhi spawn kiya par window nahi dikhi to intezaar, naya spawn
  nahi. Grace ki **hadd ke baad** dobara koshish hogi (Edge mar gaya to app
  chup-chup na baith jaaye).
- **HUD file 200 cross kare to split karo — seam `win_find.py` hai.** Sirf
  `ctypes` (`EnumWindows`) wala hissa `desktop/win_find.py` me gaya; `hud_window.py`
  me sirf `command()` + `HudWindow` class. Naya `win_find` ko `test_desktop.py` ke
  `SOURCE_FILES` list me daalna mat bhoolna (warna uska hygiene check chup ho
  jaata hai).
- **Browser wala test = `finder`/`spawner` inject karo, asli Edge nahi.**
  `HudWindow(exe=..., finder=..., spawner=...)` — `available()` sirf
  `Path(exe).is_file()` dekhti hai, is liye `sys.executable` kaafi hai. Asli taskkill
  (`subprocess.run`) bhi fake do — `tests/hudhelp.py` ke fakes yahi hain. Wake
  simulate karne ke liye `callbacks.on_wake()` **asli** call karo aur sirf
  `wake/command.run` nakli rakho (HUD wala hissa sach chalta rahe).
- **Live pakkaura throwaway script se karo** (`%TEMP%\opencode`, repo me nahi):
  `open_hud.main()` 3 baar bula kar `EnumWindows` se "Jarvis HUD" windows gin lo.
  Fix se pehle 3 call = 4 window, fix ke baad = **1**. Running app ko chheda
  nahi — `open_hud` alag process hai.

## 8.1.5 STT/TTS KE PAKKAUREY NIYAM (13 Oct 2026 — S-2)

- **STT ka apna timeout, brain ka NAHI.** `voice/stt.py` pehle
  `BRAIN_TIMEOUT_GROQ` (10 s) uthata tha + SDK 2 baar khud retry karta tha →
  3.5 s ki audio par call **43 s** tak atka (S-1 audit). Ab
  `config.STT_TIMEOUT_SECONDS` (6 s) + `STT_MAX_RETRIES` (1) + ceiling
  `config.stt_deadline()` (16 s). **Naya knob bana kar usi file me use mat karo**
  — `config_voice.py` me daal, `config.py` ke import list me bhi (warna
  `AttributeError` test me hi pakda jaata hai).
- **`asyncio.wait_for`/`to_thread` se "hang" pakka nahi hota.** `wake/listen.py`
  ke `asyncio.run()` band hote waqt executor ka **join** wait karta hai
  (`shutdown_default_executor`, 300 s) — SDK atka to caller bhi atkta, chahe
  ceiling laga di ho. Sahi raasta: **daemon thread + `join(timeout)`**
  (`voice/stt.py` ka `_run_bounded`), phir `to_thread` sirf event loop free
  rakhne ke liye. Test me `time.sleep(3)` fake + chhota ceiling daal kar
  **waqt hi measure** karo — warna test khud 3 s lega aur chup ho jaayega.
- **`health.classify()` ka naya category mat bhoolo.** 401 ka pattern hi nahi
  tha, is liye wo `"other"` banta tha; aur `classify_and_skip()` sirf
  `busy/billing/auth/empty` par kuch karta hai — yaani **kuch nahi** hota tha.
  Naya category jodte waqt teen jagah dekh: `classify()` (word/pattern),
  `health.fail()` (cooldown ka rule), aur `classify_and_skip()` ki **allow-list**.
  `auth` pehle se likha tha par **koi use hi nahi karta tha** — dead code.
  Order bhi soch: `auth` ko `busy` se **pehle**, warna 403 + "rate limit"
  wala message retry bekaar ban jayega.
- **Key khaali hai to provider chhedna hi nahi hai.** Voice id
  (`config.voice_for`) aur key (`config.has_elevenlabs`) **do alag** check hain;
  pehle sirf voice id dekha jaata tha. `voice/tts.py` ka `missing_key()` ab
  alag gate hai — `tts.PROVIDERS` fake se badal kar assert karo ki provider
  **0 baar** bula (sirf "sahi provider mila" se ye prove nahi hota).
- **Har command ka level log karo — sirf number.** `wake/pcm.py` ka
  `quality()` → `(peak_rms, clip_pct)`, `wake/utterance.py` ki capture line me.
  S-1 me pata chala tha ki asli nuksan yahi tha (RMS median 0.107, 7% cases
  0.5+ = clipping). **Audio kabhi save/scribe mat karo** (privacy) — sirf do
  float. Test me `logging.Handler` laga kar asli log line padho; source grep
  se ye nahi pakda jaata.
- **`test_wakehelp.loud()` ka RMS exactly 0.129 hai** (`sin()*6000` int16), aur
  kuch fakes ka **0.5**. Ye `logs/prabh.log` me bhi likhte hain — matlab log ka
  RMS analysis karte waqt **test ke entry hatao**, warna asli mic ka nateeja
  galat nikalta hai. Maine pehle isi galti se "mic bahut tez hai" bola tha.
- **`.env` wala value badalta waqt purana wapas rakh.** Test me
  `os.environ.pop("ELEVENLABS_VOICE_SUNDAY")` ne `.env` ki **asli** value mita
  di, aur bade test chup-chaap fail ho gaye. `saved = os.environ.get(...)` →
  `finally` me wapas (ya `pop` sirf tab jab `saved is None` tha).
- **Chuppi/timeout badalne par purana test bhi badalna padta hai.** Ek test
  default **pakadta** hai (`test_speed_fix.py` me 0.9 s). Value badal ke us
  test ko update karna **hisab me aata hai**, naya fail nahi — warna "6 purane
  fail waise hi" wali baat galat ho jaati hai.

### 8.1.6 OVERNIGHT (13 Oct 2026) — TEST LOG, DEFAULT-OFF, TAIL GUARD, INJECTION

Ye chaar niyam raat ke kaam se aaye. Chaaron ka ek hi kaaran hai: **kuch
chhupa kar chalne wala code ya test chup-chaap galat faisla de deta hai.**

- **⚠️ TEST `logs/prabh.log` ME NAHI LIKHE — `tests/logsafe.py`.** Ye file
  `PRABH_LOG_DIR` env **import ke time** set karti hai, is liye har `tests/test_*.py`
  me `from tests import logsafe` **pehla repo-touching import** hona chahiye.
  Woh `config` **import nahi** karta — warna env set hone se pehle hi
  `config.LOG_FILE` ban jayega aur poora kaam bekaar. Anchoring ka pakka tareeka:
  `^sys\.path\.insert\(` (column 0, **asli call** — string literal me bhi
  `"sys.path.insert"` ho sakta hai aur wahin line ghus jaati hai → `IndentationError`),
  warna pehla `^\s*(import|from)\s+config\b`, warna pehla `from tests.X import`.
  `logsafe` ko `import config` ke baad rakhna **kaam nahi karta** —
  `tests/wakecmdhelp.py` `desktop.playback` laata hai jo `config` le aata hai.
- **⚠️ DEFAULT-OFF ka ek hi raasta: `tools/__init__.py` ka `visible()`.**
  `brain/prompt.py` pehle `TOOL_SUMMARY` se **khud** spec banata tha, is liye
  `tools.spec()` ka `_on()` filter **bekaar** tha aur band tool LLM ko dikhai
  de raha tha (aur prompt size limit tod raha tha). Ab `brain/prompt.py` bhi
  `tools.visible()` use karta hai. **Naya default-off feature bana rahe ho to
  `visible()` ka test likhna zaroori hai** — warna flag set karne se pehle hi
  pata hi nahi chalega ki tool jaanta hai ya nahi.
- **⚠️ `PLAYBACK_MUTE_MIC` DEAD CODE hai (verified 13-Oct).** Sirf
  `config_wake.py` me define + `config.py` se re-export; production me koi file
  nahi padhti. Asli rok `wake/worker.py` ka `hold_for_command()` /
  `release_from_command()` hai. Par sirf `drain()` **kaafi nahi** — wo
  `MAX_QUEUE_BLOCKS` (400 chunk ≈ 12 s) tak bounded hai jabki jawab 18 s tak
  chalta hai, aur purana `take_fresh()` sirf **ek** chunk bachata tha. Isi liye
  **tail guard** (`PLAYBACK_TAIL_GUARD_SECONDS`, 0.4 s) zaroori tha. Aur
  `maybe()` me bhi `suppressing()` check hona chahiye — `gate.on_flush()`
  **gate thread** se `maybe()` bulata hai, aur wahan `_loop` ka check nahi lagta
  (tail guard flush se bypass ho jaata tha).
- **⚠️ Risk sirf ARGS se nikalti hai — isi liye injection nahi hota.**
  `gatekeeper/rules.py` ka `_escalate()` `decide()` ke shuru me **saare args**
  ka joined text dekhta hai; source ka koi hissa nahi. Is liye page/file/message
  me likha "sab allow kar do" kuch nahi badalta. **Naya guard likhte waqt source
  mat dhoondo** — args dekhna hi sahi hai, aur yahi testable hai. Dhyan rahe:
  word-boundary (`discord` me "card" hai) aur query-param form alag rakhna
  padta hai, warna normal URL galat ASK ho jaate hain.
- **Split ka 200-line niyam JS par bhi lagta hai** (`tests/hud_check_ui.py`
  `ui/app.js` ka `<200` check karta hai) — naya JS hissa `ui/hud_*.js` me
  banao, `app.js` ko na badaao. Aur **split ke baad `if __name__ ==
  "__main__"` runner check karo**: ek baar split script ne runner hata diya
  tha aur test chup-chaap *chalta hi nahi* tha (exit 0, koi check nahi).

## 8.2 WINDOWS TRAY / REGISTRY KE PAKKAUREY NIYAM (2 Oct 2026)

- **Tray list me app ka naam nahi, EXE ka naam dikhta hai.** Venv ka `python.exe` sirf
  redirector hai — asli process `D:\Python312\python.exe` chalata hai, aur Windows usi ka
  naam dikhata hai. Is liye Sunday kholne par bhi list me `python` likha hota hai.
  Asli exe nikaalne ka tareeka: `Get-CimInstance Win32_Process` me `-m desktop.app`
  dhoondo, phir us PID ka `Path` padho.
- **Tray entry ka key hash hai — hard-code mat karo.**
  `HKCU\Control Panel\NotifyIconSettings\<hash>` me har icon ki alag entry hai, aur
  **ek hi exe ki do entry ho sakti hai**. Pehchaan `ExecutablePath` +
  `InitialTooltip` se karo (purana stale tooltip — jaise `MyJarvis.Desktop` — batata hai
  ki entry kitni purani hai), ya live process se.
- **Har registry change se pehle `reg export`.** Poori subkey `D:\prabh\backup\` me
  (`backup/` gitignored hai). Phir **sirf ek** value badlo aur pehle/bad me entry count
  compare kar ke proof rakh lo. Baaki icon (Teams, Hermes, OneDrive) **kabhi mat chhed**.
  Wapas chahiye to usi `.reg` ko `reg import` — `.env` ki tarah `.reg` commit mat karo.
- **Register hona aur dikhna alag baat hai.** Icon `Register` ho sakta hai aur phir bhi
  overflow `^` me chhupa rahe (`IsPromoted` missing). Register hone ka proof: `EnumWindows`
  se window class (Sunday ka class PID ke saath). Dikhne ke liye `IsPromoted=1` +
  `SHChangeNotify(SHCNE_ASSOCCHANGED)` — sign-out ki zarurat nahi.
- **Global hotkey sirf `desktop/hotkey.py` me.** `RegisterHotKey` + `PeekMessageW` (GetMessage
  block karta hai, `stop()` turant nahi maanta). `PeekMessageW` ka `argtypes` zaroori hai —
  64-bit par `lParam` kat jaata hai. `MOD_NOREPEAT` mat lagao (kuch build me fail).
  `hWnd=NULL` hone ki wajah se `RegisterHotKey` aur message pump **ek hi thread** par
  hone chahiye — warna `WM_HOTKEY` kisi aur thread ki queue me chala jaata hai.
- **⚠️ `Shell_NotifyIconGetRect` is PC par KAAM NAHI KARTA — 4-Oct ko live proof.**
  Sahi hwnd + sahi uid ke saath bhi `E_INVALIDARG (0x80070057)` deta hai, doosre
  process se bhi. Throwaway probe se pata chala: naya pystray icon bana kar shell ne
  uski registry entry **bana di** (icon accept hua) par GetRect phir bhi fail raha.
  Is liye GetRect par koi faisla (watchdog/retry/promote) **mat likho** — galat warning
  aati hai aur asli kaam chhoot jaata hai. **Sahi source: `HKCU\Control Panel\
  NotifyIconSettings`** — shell sirf wahi entry banata hai jab icon uske paas ho.
  Entry apni `InitialTooltip` se pehchan (`Jarvis - ...` shuru hota hai), aur
  `IsPromoted` sirf tab hota hai jab icon **taskbar me dikhta** hai. Yehi check
  `desktop/tray_watch.py` karta hai — **sirf padhta hai, kabhi likhta nahi**
  (`IsPromoted=1` likhna owner ke confirm + `reg export` ke baad, jaise 8.2).
  ⚠️ Registry entry **stale** bhi rehti hai (`Stop-Process -Force` par shell icon
  hata nahi) — is liye sirf entry dekhna "icon abhi hai" ka proof nahi, `IsPromoted`
  + owner ki aankh asli hai.
- **⚠️⚠️ 4-Oct ko ASLI BUG mila — pehle 3 din hum galat source dekh rahe the.**
  `desktop/tray.py` me `run_detached(setup=self._on_setup)` tha. **pystray tabhi
  `visible = True` khud karta hai jab `setup` callback na mile** (`_base.py:395` —
  `setup` diya to sirf `setup(icon)` chalta hai). `_on_setup` sirf
  `log.info("tray ready")` karta tha → icon **kabhi visible nahi hua** → `NIM_ADD`
  chala tha (registry entry banti thi, `tray_watch` "dikh raha hai" bolta tha) par
  shell use **render hi nahi** karta tha. Fix: `_on_setup` me `icon.visible = True`.
  **Niyam:** `setup=` diye to us callback me `icon.visible = True` likhna
  **zaroori** hai — warna pystray chup-chaap invisible icon chhod deta hai.
- **⚠️ Registry entry "visible" ka PROOF nahi hai — `desktop/tray_watch.py` ka log
  guess hai.** Entry banna matlab shell ne icon **register** kiya (`NIM_ADD` chal
  chuka), yehi invisible icon par bhi hota hai. `IsPromoted=1` likhwane se bhi
  koi fark nahi pada (backup ke saath likha, phir bhi icon invisible raha). Asli
  sach **owner ki aankh** hai; program se verify karna ho to **UIA** se taskbar
  padho (`Shell_TrayWnd` ka `Shell_TrayWnd`/`TopLevelWindowForOverflowXamlIsland`
  window, `AutomationElement` ke `Name` = tooltip). Yehi method se 4-Oct ko bug
  pakda gaya — `probe_overflow2.ps1` (`%TEMP%\opencode`) me hai.
- **Live debug ka asli tareeka (3-step, isi bug ke liye):** (1) raw Win32 probe
  (pystray nahi) se `NIM_ADD` ka **BOOL return** dekho — `1` matlab shell ne maan
  liya; (2) UIA se overflow flyout khol kar naam padho — icon dikhta hai ya nahi;
  (3) bare pystray alag chala kar same check — agar woh dikhe par hamara na dikhe,
  to galti **hamare app ke setup** me hai. Ye teen step isi bug ko 3 step me pakad
  gaye the (`probe_raw_tray.py`, `probe_pystray.py`, `probe_ourtray.py`).
- **Probe me `ctypes` ka dtype chhootna mat bhoolna** (throwaway scripts me 4 baar
  laga): `GetModuleHandleW.restype` `c_void_p` (default `c_int` → `CreateWindowExW`
  ka hInstance overflow), `CreateWindowExW`/`DefWindowProcW` ke saare `argtypes`
  (warna `WNDPROC` callback me `NameError`/`OverflowError` aata hai), `WS_POPUP`
  `ctypes.wintypes` me **nahi** hai (`0x80000000` likh do).
- **HUD ke teen raasta ek hi function se:** `desktop/open_hud.py`. Server band ho to crash
  karne ke bajaye message box (pythonw me stdout nahi hota, is liye print kaam nahi karta).
- **PowerShell quoting JS me mat todo.** `.lnk` banane wala `.ps1` **alag file** rakho aur
  `subprocess` se `shell=False` par chalao.
- **Auto-start sirf `desktop/autostart.py` likhta hai, aur sirf `main()` se**
  (`python -m desktop.autostart install`). Module me koi module-level registry call
  **nahi** — test me har function ka `reg` fake (`FakeReg`) deta hai, asli registry kabhi
  nahi chhooti. Quote ka kaam `subprocess.list2cmdline` karta hai, haath se `"` mat lagao.
- **⚠️ Run key ka cwd `C:\Windows\System32` hota hai — auto-start me `-m module` KABHI
  mat likho.** Wahan se `import config` fail hota hai (ModuleNotFoundError) aur app har
  login par **chup-chaap** mar jaati hai (pythonw me stdout hota hi nahi, is liye crash
  bhi nahi dikhta). Sahi raasta: value me **file ka path** (`pythonw desktop/launcher.py`),
  aur `desktop/launcher.py` khud `BASE_DIR` `sys.path` me daalta hai + `main()` me
  `os.chdir(config.BASE_DIR)` karta hai (child `desktop.app` ko bhi sahi cwd chahiye).
  Test: `tests/test_desktop_login.py` launcher ko System32 par load karke prove karta hai.
  Value `pythonw desktop/launcher.py` hai (black console nahi); crash `logs/desktop.out`
  me bachta hai, is liye "crash chup mat ho" wala niyam bhaala jaata hai.

---

## 9. NAMING (sirf Jarvis)

- User ko dikhta/sunai naam **Jarvis** hai (`config_name.ASSISTANT_NAME`); UI me hard-code nahi, placeholder se aata hai.
- Andar ka mode id `"sunday"` **legacy** hai — `DEFAULT_MODE`, `MODE_ALIASES`, `PERSONA_FILES`, voice keys (`*_VOICE_SUNDAY`) aur `data/` lock isi se bandhe. **Rename mat karo.**
- `PRABH_*` sirf app ka prefix hai (env keys / JS globals / HTML ids) — mode nahi.
- `hud_clock.js` ka `"Sunday"` calendar ka din hai, assistant ka naam nahi.
- Prabh mode dormant hai (`PRABH_SUNDAY_ONLY=1`), jaldi hatega.

---

## 11. ABHI KA SACH (14 Oct 2026 subah — overnight raat ke baad)

**Poora record: `docs/OVERNIGHT_REPORT.md`.** Neeche sirf taar (teeno ek
chain me hain, merge/push **nahi** kiya gaya).

| Branch | Kaam | Commit | Suite |
|---|---|---|---|
| `fix/stt-speed` | S-2 (pehle se) + **KAAM 0** test ka log alag | `695e5c5` | 58/64 |
| `feat/wake-alarm` | **KAAM 1** subah 7 baje ka alarm + 2 Task Scheduler task | `84842a0` | 61/67 |
| `fix/self-hearing` | **KAAM 2** tail guard (apni awaaz se WAKE HIT nahi) | `5bb76cc` | 63/69 |
| `fix/permissions-v2` | **KAAM 3** allowed apps + hamesha-card + injection | `f6e28f8` | 65/71 |
| `fix/speed-replies` | **KAAM 4** awaaz 1-2 vaakya + time jawab ka cache | `9223b86` | 66/72 |
| `fix/hot-window` | **KAAM 5** follow-up bina "Jarvis" (**DEFAULT OFF**) | `1f970eb` | 67/73 |
| `fix/hud-polish` | **KAAM 6** SYSTEM panel `--` fix + JS split | `0e446d5` | 69/75 |

- **KAAM 7 (naya Arc Reactor HUD theme) SHURU HI NAHI HUA** — Playwright is
  machine par nahi hai, naya package lagana mana tha. Reason + plan
  `docs/OVERNIGHT_REPORT.md` me. Purana neela HUD jaisa hai waisa hi hai.
- **PUSH nahi hua** — repo private hai ✅ (bina login `ls-remote` fail hua),
  history saaf hai ✅ (13 hit par sab nakli test key), par git ka saved
  credential **alag account** (`rachithunyawrr`) ka hai aur target repo
  `Rachit-Sharma08` ka. Owner se push karna hoga — command report me.
- **Suite ab: 75 total = 69 pass + 6 jaane-pehchane fail** (naya fail nahi):
  `test_desktop.py` + `test_desktop_shortcut.py` (`desktop/app.py` 207 — 200-line
  niyam), `test_wake_ack` / `test_wake_command` / `test_desktop_sleep`
  (ack ka text), `test_wake_resample` (gain).
- **Alarm task ACTIVE hai**: `JarvisWakeAlarm` 14-10-2026 07:00:00 +
  `JarvisWakeAlarmBackup` 07:10:00, dono `Ready`/`Enabled`, `WakeToRun=True`,
  `LogonType=Interactive`, user `fvcvv`. Hataane ka tareeka report me.
- **`PRABH_NO_CARDS` default 1** (`config_tools.py`) — card nahi, code faisla
  karta hai; `PRABH_NO_CARDS=0` par purana card raasta.
- **Naye DEFAULT-OFF flags** (koi bhi abhi **ON** nahi):
  `PRABH_ALARM_TOOL` (0) · `PRABH_HOT_WINDOW` (0) ·
  `PRABH_TAIL_GUARD` (0.4 s) · `PRABH_VOICE_SENTENCES` (2).
- **Test ab asli `data/` ko nahi chhoo sakta** (`tests/datasafe.py`) **aur
  `logs/prabh.log` bhi nahi** (`tests/logsafe.py`). Details section 8.1.6 me.
- Parked branches — **merge MAT karo**: `wip/tools-pcm-2026-10-10`,
  `docs/agents-md-pending`.
- Agla kaam: KAAM 7 (Arc theme, Playwright ke saath) + push + owner ke
  live test.

---


## ABHI KYA BAAKI HAI

- Round 2 poora ho gaya (1-2 Oct 2026). Plan/record `ROUND2.md` me padh sakte ho.
- **Phase 4 HUD poora ho gaya (1-2 Oct 2026).** Plan/record `CHANGELOG.md` me.
- **Phase 5 Step 3a (desktop shell) ho gaya (2 Oct 2026)** — supervisor + tray + Edge HUD +
  single instance + wake stub, 25 suite green. Plan `PLAN.md`, record `CHANGELOG.md` me.
- **Phase 5 Step 1 (Vosk wake word) ho gaya (2 Oct 2026)** — mic hamesha sunta hai, "Sunday" par
  HUD khulta hai, tray MUTE sunna rokta hai, **30 suite green**. Detail `VOICE.md`,
  record `CHANGELOG.md`.
- **Phase 5 Step 2 ke do hisse ho gaye (3 Oct 2026) — 32 suite green.** **2a** command
  capture (`wake/utterance.py` + `wake/wav.py`), **2b** speaker (`desktop/playback.py`,
  `python -m desktop.playback_cli --say "Ji, boliye"` se bina app ke awaaz test ho jaati hai).
  Dono ka record `CHANGELOG.md`, detail `VOICE.md`.
- **Phase 5 Step 2c ho gaya (3 Oct 2026) — 37 suite green.** Wake ke baad poora command:
  "Ji, boliye" → mic queue drain + warm-up → capture (2.0 s khamoshi par band, max 30 s) →
  Groq STT → shared `server.state.ENGINE` → Hub/UI events + `via="voice"` → jawab ki awaaz
  (`desktop/playback.py`). Naye file `wake/listen.py` (mic wala hissa) + `wake/command.py`
  (flow), mute/lock par kuch nahi, ASK par sirf card + "confirm kijiye" (awaaz se ALLOW
  nahi). Teen naye suite: `test_wake_command.py` (flow), `test_wake_brain.py` (brain + ASK),
  `test_wake_listen.py` (mic/pause) + `tests/wakecmdhelp.py` (fakes). Record
  `CHANGELOG.md`, detail `VOICE.md`.
- **Phase 5 Step 3 POORA ho gaya + entry chalu (4 Oct 2026) — 44 suite green.** Naya
  `desktop/autostart.py` (`python -m desktop.autostart install|remove|status`), value
  `pythonw desktop\launcher.py`, `AUTOSTART_NAME` ab `ASSISTANT_NAME` se banta hai.
  Registry me `Jarvis` value likhi gayi (`reg export` backup
  `backup\run-key-20261004-083516.reg`, Run key 6 → 7 value, baaki shaant).
  **Asli bug pakda:** Run key ka cwd `C:\Windows\System32` hai, wahan se `-m module`
  ModuleNotFound mar jaata tha — app chup-chaap marta. Ab value me file ka path +
  `launcher.py` khud `BASE_DIR` `sys.path` me daalta hai aur `main()` me `os.chdir`
  karta hai (child ko bhi chahiye). Proof: `Start-Process ... -WorkingDirectory
  C:\Windows\System32` se asli launch → `GET /` 200, startup ki 4 line, tray register.
  Test `tests/test_desktop_login.py`. Face/trust/learn/maker baad me.
- **Battery fix + Step 2-6 ka kaam shuru (4 Oct 2026) — 45 suite green.** User ki 3
  shikayat: (1) mic hamesha on = battery, (2) tray icon me button nahi + TOOLS default
  ON chahiye, (3) "sun nahi pa rha", jawab late (11.5 s). **Battery ka asli wajah code
  mila** — `wake/session.py` Vosk ko har chunk deta tha. Naya `wake/gate.py` (VAD +
  khamoshi ka hisaab + "feed karun?" ka faisla) + `_pump` se redundant `sd.sleep()`
  hata (chunk 43 ms → sach me 30 ms, is liye chuppi ki window aur timing dono theek).
  **Asli probe (app band, `%TEMP%\opencode` me): 4.8% → 0.9% core**; app total
  3.9% → 2.3% (app core 1.46%, mic+gate 0.9%). Naya suite `test_wake_gate.py`
  (pure, battery ka fix bina mic ke pakadta hai) + `describe()` ab 5 hisse.
- **Fix round 4 ho gaya (2 Oct 2026)** — tray entry `IsPromoted=1` (backup ke saath), Desktop
  `Sunday HUD` shortcut + global hotkey `Ctrl+Alt+S`, dono ka ek raasta
  (`desktop/open_hud.py`). Record `CHANGELOG.md` me.
- **GitHub repo bana (2 Oct 2026)** — private `github.com/rachithunyawrr/jarvis2.0`, remote URL
  me token **nahi**. Push ke liye ek-kaam ka temp askpass (repo ke bahar) + turant delete.
- Ek hi cheez aur baaki hai: **Cartesia ki female voice id** (`CARTESIA_VOICE_*`). Na mile to Cartesia skip hoti
hai — koi problem nahi, Edge Swara chalti hai.
- Aage ka kaam user se pucho; koi chhupi hui task nahi hai.

---

## 8.1 PC WALE KAAM (2 Oct 2026) — ye project ke code se alag hain

Ye sab **`D:\prabh` ke bahar** ka kaam tha. Ek baar record hai; dobara mat karo.

### 1. Purana JARVIS auto-start — **HATA DIYA GAYA** (backup ke saath)

- `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` se value `electron.app.Electron`
  **delete** kar di gayi thi (`reg query` me ab nahi hai — proof log me hai).
- Backup: `D:\prabh\backup\jarvis-autostart-20261002-141601.reg` — 456 byte, UTF-16LE + BOM
  + CRLF, path `D:\jarvis\desktop`. **Wapas chahiye to `.reg` file `reg import` karo.**
- `backup/` folder `.gitignore` me hai — system backup kabhi commit mat karo.
- `D:\jarvis` folder aur `electron.exe` **chhue nahi gaye**, koi `electron.exe` process
  bhi nahi tha. Baaki 7 Run values (OneDrive, Teams, Hermes x2, Chrome, Microsoft.Lists, Edge) shaant.

### 2. `D:\SystemConfig` — JAANCH POORI, Koi BADLAV NAHI (user ke "haan" ka wait)

Chain (ek hi raasta): Startup folder `SystemConfig.bat` (4 line, sirf `run-all.ps1` chalaati hai)
→ `run-all.ps1` → `apply-settings.ps1` (har login) + `backup.ps1` (12h+ purana ho to).
Source `D:\SystemConfig\Startup-helper\SystemConfig.bat` se byte-identical
(SHA256 `5A128FDDE2D354C242CC2BF5DA74F9E5868B20CDA37A6A89FD341DE04ABC0FCB`).

- **Kab bana:** 14-Sep-2026 21:08 → 22:55, ek hi session me (`PARTNER_CHAT_LOG.txt` ke hisaab se
  opencode ke saath). Aakhri chal: 2-Oct-2026 08:24:54, "Sab kuch OK".
- **Internet: kuch nahi bhejta, kuch nahi download karta.** Poore folder me sirf ek URL:
  `cdp-helper.ps1` ka `http://localhost:9222/json` — wo bhi **startup chain me nahi**, kabhi
  nahi bulta.
- Judne ka tareeka: **sirf Startup folder**. Registry `Run`/`RunOnce` me koi entry nahi, koi
  scheduled task nahi. `StartupApproved\StartupFolder\SystemConfig.bat = 02000...` (enabled).
- **Secrets (kabhi mat likh):** plaintext password 3 jagah —
  `Fix-Password-Prompt.ps1:6`, `PARTNER_CHAT_LOG.txt:54-55`. Koi API key/token nahi.
- Folder me hai par **startup chain me nahi**: `DisableUAC.bat` (UAC band karne ki koshish —
  **kaam nahi ki**, `EnableLUA=1` aaj bhi), `Add-Me-To-Admins.bat`, `FixAdmins2.bat`,
  `elevate*.bat`, `After-Account-Change.bat`, `cdp-helper.ps1`. User **abhi admin nahi**.
- **Reversible plan (user ke "haan" par):** Startup folder se sirf `SystemConfig.bat` ka entry
  hatao. `D:\SystemConfig` ki koi file delete mat karo. Backup `backup\` me rakh lo.

### 3. Tray icon na dikhna — asli wajah **Windows overflow** hai, pystray nahi

- `HKCU\Control Panel\NotifyIconSettings`: 22 icon entries, sirf **1** par `IsPromoted=1`
  (direct taskbar me), baaki **21** par key hi nahi = Windows ne sabko overflow `^` me
  chhupa diya hai (normal Windows 10/11 behaviour).
- Pichli baar bhi icon **register hua tha** (log `tray ready` + window class
  `Sunday1944541326960SystemTrayIcon` maujood) — bas dikha nahi.
- **User ko batao:** taskbar ke `^` (chevron) par click → Sunday icon → right-click →
  **"Always show icons"**. Isse wo permanent dikhta rahega.
- Debug ke liye: `tests/` me nahi, ek throwaway `EnumWindows` script se process ki window
  class dekho + `NotifyIconSettings` count nikalo. Script har baar naya bana sakte ho.
- ⚠️ `Get-Process` se `CommandLine` **nahi** milta — Edge HUD check me `Get-Process msedge |
  Where CommandLine` galat tha aur "HUD nahi khuli" galat bataya. Hamesha
  `Get-CimInstance Win32_Process` use karo.

### 4. HUD `localhost` vs `127.0.0.1` — ek Chrome tab chalu hai galat URL par

- Log me `token reject (origin=http://localhost:8000)` — browser GET par `Origin`
  nahi bhejta aur security `127.0.0.1` maangti hai. **HUD hamesha `http://127.0.0.1:8000` kholo.**
  `localhost` se kuch bhi nahi chalega (Phase 4 me ye hi chhupi hui bug thi).
- Pakda gaya: **ek Chrome tab `http://localhost:8000` par khula hai aur har ~6 second me
  poll kar raha hai** (client = Chrome network-service PID 7940, parent Chrome PID 16836).
  196 reject, jabki `127.0.0.1` se sirf 4. User ko ye tab band karna hai — warna log
  bharta rahega aur us tab me HUD kabhi nahi khulega.

### 5. Jahan chhoda tha (2-Oct raat, user sone gaya tha) — 19:48 par update hua

- User ne double-click kar diya — app **live chal raha hai** (PID 17260). Ye verify hua:
  - startup ki 4 line sahi: `server up: http://127.0.0.1:8000` · `tray started: Sunday` ·
    `HUD ready` · `wake: stub`
  - `GET /` = **200** ✓
  - tray icon **register hua** — window class `Sunday1977541771184SystemTrayIcon` PID 17260
    par maujood ✓ (pystray theek chal raha hai)
  - `NotifyIconSettings`: 21 icon, sirf 1 promoted, 20 overflow `^` me
  - Explorer ka overflow window maujood hai → `^` click karne se khulega
- **User ke confirm ka wait:** taskbar ke `^` par click → Sunday icon → right-click →
  **"Always show icons"**. Phir batana ki dikha ya nahi.
- Ek kaam bacha hai user ke haath: **`localhost:8000` wala Chrome tab band karna**
  (section 4) — warna log bharta rahega.
- Iske baad hi Phase 5 **Step 1** (Vosk wake word) shuru karna hai.

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
- **Phase 5 Step 3a fix round 2 (2 Oct 2026)** — `start_prabh.bat` me ek `echo`
  line par raw `( )` ki wajah se `cmd` ka `if` block toota aur python launch hi
  nahi hua (na tray, na process). Fix: `goto` label + CRLF + ASCII, launcher
  crash console par bole + child output tee, startup ki 4 line ek jagah
  (`desktop/startup.py`, `config_desktop.STARTUP_*`), `log_setup.ascii_text()`,
  naya `tests/test_bat.py` — **26 suite green**. Purana JARVIS auto-start
  (`HKCU\Run` me `electron.app.Electron`) sirf bataya, chhua nahi.
- **Fix round 3 (2 Oct 2026)** — "pehle se chal raha hai" ab proof par: `pid_alive()`
  (`OpenProcess`, `os.kill` nahi) + `GET /` 200 dono check, chaar alag message;
  `_clean_stale_pid()` stale `.pid` hata deta hai; message console par bhi;
  tray `retry_start()` 3 koshish ke baad `EXIT_NO_TRAY` (4) se saaf exit +
  `run()` me `_stop.is_set()` check; `desktop/actions.py` naya split
  (`app.py` 189 lines) — **26 suite green**. Purana JARVIS auto-start
  (`HKCU\Run` me `electron.app.Electron`) **backup ke saath hata diya**; `D:\SystemConfig`
  ki jaanch poori par **kuch nahi badla** (user ke "haan" ka wait) — dono ka record
  section **8.1** me.
- **Fix round 4 (2 Oct 2026)** — user ka andaza sahi tha: Windows 11 ki tray list me
  `Sunday` **kabhi nahi** dikhega, wo **exe** ka naam dikhati hai aur venv ka python
  redirector hai (asli `D:\Python312\python.exe`). Live proof — tray window class
  `Sunday2587022232368SystemTrayIcon` base python ke PID par. Sirf **Prabh wali** entry
  (`13638010186279013602`, tooltip khali) me `IsPromoted=1`, backup
  `backup/notifyicon-python-20261002-194804.reg`, baaki 20 icon chhed nahi gaye — nayi
  niyam section **8.2**. Tray na dikhe to **3 raasta**: tray menu / Desktop shortcut
  (`Sunday HUD.lnk`) / global hotkey `Ctrl+Alt+S`, teeno ka ek raasta
  `desktop/open_hud.py`. Naye `desktop/hotkey.py` (sirf ctypes, koi naya package nahi),
  `desktop/shortcut.py` + `hud_shortcut.ps1`, `.env` se badalne wala `PRABH_HUD_HOTKEY`,
  `tests/test_desktop_hotkey.py` + `tests/test_desktop_shortcut.py` (test file
  200+ lines thi to split ki) — **28 suite green**.
- **Step 2 speed fix (3 Oct 2026)** — wake 18.5 s tha, brain sirf 1.1 s tha
  (log: `TIME wake_command: TOTAL 18450ms | ack=3520ms warmup=1036ms capture=8088ms`).
  Teen fix: (1) `voice/tts.py` me `speak_cached()` + `_CACHE` (max 8) — ack ki
  "Ji, boliye" ka TTS ab dusri baar 0 ms; (2) `listen.warmup(deadline=)` +
  `command.py` me ack se **pehle** `settled_by` — 1 s ka dead wait gaya;
  (3) `COMMAND_END_SILENCE` 2.0 → 1.2 s. `desktop/playback.py` 205 → split
  (`desktop/playback_cli.py`, CLI ab `-m desktop.playback_cli`). Naye suite
  `test_tts_cache.py` + `test_speed_fix.py` — **42 suite green**, sab file `<=200`.
  Do asli galti: `speak()` me `return await` bhool gaye (nested coroutine), aur
  split karte waqt do test ke references update nahi hue.
- **Phase 5 Step 1 (2 Oct 2026)** — Vosk wake word **asli**: `config_wake.py` (constants) +
  `wake/` ka 6 file (`audio` = mic ka ek owner + VAD, `model`, `detect`, `phrase`,
  `session` = loop, `worker` = module-level ek hi worker), grammar me sirf 5 shabd,
  cooldown 1.5s, tray MUTE → `set_paused`, startup line `wake: sun raha hai (sunday)`.
  200-line niyam ke liye `worker.py` → `session.py`, `desktop/app.py` → naya
  `callbacks.py` + `startup.say_hud/say_wake`. Naye 7 niyam bullet (worker/mic/
  wakes/startup-line/askpass/PowerShell). `tests/wakehelp.py` + `test_wake.py` +
  `test_wake_loop.py` — **30 suite green**. Do asli bug pakde: `FILLER` me `"[unk]"`
  bekaar tha, aur purana `test_desktop.py` **asli mic** khol raha tha. GitHub private
  repo `rachithunyawrr/jarvis2.0` bana + poora history push.
- **Phase 5 Step 2 (3 Oct 2026)** — wake ke baad ka command + speaker. **2a** (`5e9a2fc`)
  `wake/utterance.py` (pre-roll 0.4 s, VAD end 0.9 s, max 8 s, wait 5 s) + `wake/wav.py`
  (PCM → WAV). Do asli bug: khaali queue par **infinite wait**, aur min-duration
  aakhir ki khamoshi gin raha tha. **2b** (`d3a5f7a`) naya `desktop/playback.py`
  (TTS bytes → `miniaudio` PCM → `sounddevice`), `OUTPUT_DEVICE`/`OUTPUT_RATE`/
  `PLAYBACK_TIMEOUT_SECONDS`. Do asli galti pakdi: `miniaudio.decode_file` bytes par
  MB ka dump (sirf `decode()` chahiye) aur `sd.query_devices(kind="output")` list nahi
  deta (`query_devices()` + `max_output_channels` filter). Naye fake
  `desktophelp.install_audio()` + 2 naye suite — **32 suite green**. Naye 6 niyam
  bullet (playback/akhi-raasta/decode/query_devices/np.asarray/test-fake).
  `tests/test_wake.py` ka `WAKE_MODEL_ALT_DIR` leak fix + `wake/__init__.py` docstring.
- **Test split (3 Oct 2026)** — `tests/test_desktop.py` 390 lines tha (niyam tod
  raha tha, pehle se). 4 file me toda: `test_desktop.py` (160, shell + hygiene),
  `test_desktop_single.py` (163, single instance + stale PID/lock),
  `test_desktop_guard.py` (96, TOOLS auto-off + tray guard), aur naya
  `test_wake_worker.py` (49, wake wiring — pehle `test_desktop.py` me tha).
  Ek asli galti: split karte hi `Ok`/`boom` helper **local** reh gaye the, to
  `diagnose()` ke 2 check chup-chaap False hue — isi liye ab module level par
  rakhne ka niyam. Hygiene check `<200` se **`<=200`** hua aur ab har
  `tests/test_*.py` par lagta hai. **36 suite green**. Teeno commit push ho chuke
  hain — remote `3c6f151` (temp askpass, repo ke bahar, turant delete; `.git/config`
  me token nahi gaya). `CLAUDE.md` bhi 3 Oct ke haal par sync kiya: usme Step 1
  abhi tak "stub" likha tha, brain ke model ke naam hard-code the (wo
  `config_brain.py` se aate hain — **guess kabhi mat likho**), aur roadmap Step 1
  par atka tha.
- **Phase 5 Step 2c (3 Oct 2026)** — wake ke baad **poora command**. Naye
  `wake/listen.py` (drain/warmup/capture/to_text, module-level `_STOP`) +
  `wake/command.py` (ack → suno → brain → awaaz), `Session._fire()` ab
  `on_wake(phrase, mic, stop)` **synchronously** deta hai (mic/stop ka sirf
  wahi raasta), `worker.hold_for_command()`/`release_from_command()` +
  `paused()` (MUTE hold ko absorb karta hai), `worker.stop()` → `listen.stop()`.
  Silent capture **2.0 s** (`PRABH_CMD_SILENCE`) par, max **30 s**.
  `desktop/callbacks.py` ka `allowed()` mute/lock par command rokta hai; ASK par
  sirf HUD + "confirm kijiye" — awaaz se ALLOW nahi (test **AST** se check karta
  hai). `via="voice"` se browser TTS sirf wake-origin event par skip.
  Teen naye suite (`test_wake_command` flow, `test_wake_brain` brain + ASK, `test_wake_listen`
  mic/pause) + `tests/wakecmdhelp.py` fakes — **39 suite green**. **Paanch** asli galti
  pakdi: (1) source-scan docstring ke `keeper.approve` text se false positive de raha tha —
  ab AST; (2) `FakeMic` ki queue 400 chunk tak hi hai, is liye 30 s wala test 1.5 s window
  se chala; (3) test me worker shuru nahi tha is liye `state()` "off" tha — ab `paused()`
  se pause check hota hai; (4) **ASK par "confirm kijiye" 60 s BAAD boli jaati thi** (engine
  `keeper.wait()` par rukta hai) — ab generator aage badhne se pehle bolta hai, ordering
  test prove karta hai; (5) **brain fail par awaaz saare provider reasons padh leti thi** —
  ab engine log event ka `data.brain` se `BRAIN_FAILED` bolta hai (HUD par reasons waise
  hi). Naye niyam section **3.5** (voice privacy) aur **3.6** (Step 2c).
- **Step 2c suite fix (3 Oct 2026)** — poori 39-file suite pehli baar chalao to
  **do** purane suite fail hue. (1) `test_wake_loop.py`: naya `on_wake(phrase, mic,
  stop)` teen-arg signature keagainst fake `heard.append` (ek arg) → `TypeError` →
  `Session._fire()` ka `except Exception` → **trigger chup-chaap gaya, koi crash log
  nahi**; pehla fix bhi galat tha (module level helper local `heard` ko nahi
  dekh sakta), ab closure test ke andar. (2) `test_desktop_single.py`: `acquire()`
  → `diagnose()` → **asli** HTTP 8000 par, is liye "CHAL raha hai" shabd tabhi
  aata jab app sach me chalu ho (app band = fail) — ab sirf guarantee wali baat
  check hoti hai ("stale" kabhi nahi + apna PID). Do **nayi niyam** bullet:
  callback signature badle to saare fake update karo, aur test ko app ke
  "chal raha hai / nahi" par depend mat karo. **39 suite green**, sab file `<=200`.
- **Phase 5 Step 3 (4 Oct 2026)** — Windows login par auto-start. Naya
  `desktop/autostart.py` (`install|remove|status`), value
  `pythonw desktop/launcher.py` (login par koi black console nahi; crash
  `logs/desktop.out` me bachta hai). **Ek asli bhooli hui baat pakdi:** Step 1 me
  naam "Prabh" → "Jarvis" karte waqt `config_desktop.AUTOSTART_NAME = "Prabh"`
  hard-code reh gaya tha — ab `ASSISTANT_NAME` se banta hai. Doosra: launcher ka
  `_NO_WINDOW` constant **dead** tha (defined, use nahi) — ab `Popen` ke
  `creationflags` me lag gaya hai, warna pythonw ke baad child par console chhoot
  jaata. Test me `FakeReg` (dict-based nakli `winreg`) + `main()` ka CLI dispatch
  patch karke check — **asli registry kabhi nahi chhoti**. **43 suite green**.
- **Step 3 ka asli bug + entry (4 Oct 2026)** — value pehle `-m desktop.launcher` thi,
  jo **chalti hi nahi**: Run key ka cwd `C:\Windows\System32` hota hai aur wahan se
  `import config` fail hota hai (ModuleNotFoundError) — har login par app chup-chaap
  mar jaati, pythonw me crash dikhta hi nahi. Do fix: value me **file ka path**, aur
  `desktop/launcher.py` me `BASE_DIR` → `sys.path` + `main()` me `os.chdir` (child
  `desktop.app` ko bhi sahi cwd chahiye). Proof **asli** launch se liya —
  `Start-Process -WorkingDirectory C:\Windows\System32` → `GET /` 200, startup ki 4
  line, tray register. Registry me `Jarvis` value likhi (`reg export` backup
  `backup\run-key-20261004-083516.reg`, 6 → 7 value). Suite 222 lines cross karke
  `tests/test_desktop_login.py` me split hua. **44 suite green**, app **chalte hue**
  bhi poori suite pass (test app-state par depend nahi karti).
- **Step 2-5 (4 Oct 2026)** - user ke 4 faisle ek round me: (1) **"so jao"
  sleep mode** - naya `desktop/sleep.py` (pure `matches` + `enter/wake_up/toggle`),
  `STATE.asleep`, tray me `SO JAAO` item (menu 5 -> 6), aur `command.run` me
  `on_sleep` (sleep word par brain/ASK **chalta hi nahi**); jaagna sirf wake word
  se - `callbacks.on_wake` pehle flag hatata hai. (2) **TOOLS default ON +
  auto-off hata** (`TOOLS_AUTO_OFF_MINUTES=0`, setting `config_tools.py` me gayi
  kyunki `config_desktop.py` 202 cross kar raha tha). (3) **"Hlo/Helo/Hi/Yo Jarvis"**
  grammar me + VAD `0.012 -> 0.010` + pre-roll `0.4 -> 0.6` (trigger faisla waise
  bhi `WAKE_WORDS` se). (4) **Tez jawab** - `listen.peek_speech()` (0.18 s me
  awaaz hai to "Ji, boliye" **skip**, wahi 0.18 s warm-up bhi), chuppi
  `1.2 -> 0.9 s`, awaaz `tts.clip_answer()` se **220 char** (HUD par poora jawab).
  `wake/command.py` 219 lines cross karne par brain wala hissa `wake/ask.py` me
  gaya (command 178). **Do asli galti:** split ke baad `wakecmdhelp.talk()`
  sirf `command.HUB` patch kar raha tha (brain events chhoot gaye) aur
  `gatekeeper_uses()` sirf `command.py` scan karta tha (AST safety check khud
  chup ho gaya) - dono reference ek saath update karo. Naye suite
  `test_desktop_sleep.py` + `test_wake_ack.py`, **47 suite green**. Docs:
  `CHANGELOG.md` + `VOICE.md` + `TOOLS.md` + `TESTS.md` + naya rules section
  **8.1.2**.
- **Wake do-command + mic busy fix (5 Oct 2026)** - user ki do shikayat: "ek
  command ke baad doosra command nahi leta" + app par `wake: nahi chala`.
  **Asli bug:** `wake/gate.py` silence par sirf `listener.reset()` karta tha, jisse
  Vosk ka pending partial **chhoot** jata tha (debug log: chunks aa rahe the,
  `finals=0`; `sun liya: 'hello'` phir `'yo'` - trigger nahi). Fix: **teen raaste,
  ek faisla** naye `wake/trigger.py` me - `final` (purana), `partial` (naya, tez),
  `flush` (`FinalResult()` se pending text wapas). **Asli bug 2:** grammar me
  poori phrase thi (`"hello jarvis"`) - Kaldi multi-word phrase map nahi karta;
  ab `config_name.grammar_words()` har shabd alag + `[unk]` aakhri. **Asli bug 3:**
  mic busy (`MME error 1`) par ek hi koshish - ab `_open_mic()` 3 koshish
  (`PRABH_MIC_ATTEMPTS`/`PRABH_MIC_RETRY`). **Do bonus bug split me pakde:**
  `stop()` ke baad **double loop** (zinda thread par `_close()` nahi), aur
  `worker.wakes()` ka **reset** (`Trigger` ek hi instance). Split ka seam
  `trigger.py` + `lifecycle.py` (`session.py` 235 -> 175). Naye suite
  `test_wake_trigger.py` + `test_wake_phrases.py` (`test_name_jarvis.py` 200 cross
  kar gaya tha), **51 suite green**. Naya rules section **8.1.3**.
- **Suite hang fix + ek asli bug (5 Oct 2026)** - doosri poori run me `test_voice.py`
  3+ min atka. Wajah: `voice/stt.py` me **size guard kahin nahi tha** (10 MB ki
  limit sirf HTTP route par thi), to test ka 11 MB blob **asli Groq par upload** ho
  raha tha. Guard ab library me hai (har caller ke liye, HTTP + wake path) -
  `test_voice.py` ab **network-free** aur 2 s me pass; poori suite **63 s** me
  green. Test ko live network par fail hone se bachane ka naya bullet section
  **8.1.3** me.
- **E-1b: test isolation (11 Oct 2026)** - E-1 ki suite run me tests ne **asli
  `data/memory.json` mita diya** (`test_persona_nocards.py` ka `MEM.clear()`) aur
  usi me apni entries likhi. Naya `tests/datasafe.py` (59 lines): `isolated_data()`
  context manager + `DataSafeCase` mixin — data-folder + memory/audit/todos/
  reminders/kb/notes/rss/pomodoro ke path ek tmp folder par, tearDown par wapas,
  guard: path asli `data/` me -> AssertionError. **10 test file** me sirf helper
  lagaya (koi assertion nahi badla): test_persona_nocards, test_basic,
  test_engine_dedup, test_engine_detail, test_engine_tools, test_fixes_r1_brain2,
  test_fixes_r1_ui, test_desktop_single, **test_security + test_tool_routes**.
  Aakhri do **grep me nahi dikhe the** — wo asli `/chat` (real engine + real
  brain) maarte the: pakadne ke liye har test file ke around `data\memory.json`
  ka SHA256 compare kiya. Suite: **56 = 50 pass + 6 purane fail**, aur
  `data\*.json` **426/426 pehle jaisa**. `fix/tool-loop` (E-1 + E-1b) main me
  **ff merge** (`60fcaac`), push nahi.
- **R-2: HUD ek hi window (13 Oct 2026)** — har "Jarvis" par nayi window (taskbar
  me 4). **Asli wajah VERIFIED:** `desktop/hud_window.py` ka `_focus_existing()`
  `EnumWindows` se window dhoondta tha par aakhir me `return False` likha tha —
  "window mili" ka faisla **lapiset**, is liye `open()` hamesha naya browser chala
  deta tha. Live probe (throwaway, `%TEMP%\opencode`): window `Jarvis HUD` maujood
  thi (hwnd 198372), `_focus_existing()` ne `False` kaha, 3 `open()` → **4 window**.
  Fix: (1) nayi `desktop/win_find.py` — sirf ctypes (`EnumWindows` + **argtypes**,
  64-bit ka pakkaura), `find_hud_window()`/`still_open()`/`bring_front()` +
  pure `is_hud_title()`; (2) `focus_existing()` ab sach return karta hai (pehle
  `_known()` = cached hwnd `IsWindow`, phir `finder()`); (3) `is_open()` ab **window**
  se puchhta hai, process se nahi (Edge `--app` launch par `Popen` ka process window
  se pehle mar sakta hai); (4) `SPAWN_GRACE_SECONDS = 8.0` — Edge dheere khulta
  hai, usi der me dobara spawn = 2 window. **Title ka pakka signal**, sirf `'Jarvis'`
  nahi (warna user ka "Jarvis - Wikipedia" tab pakad lete). Naye test
  `test_desktop_hud_single.py` (94) + `test_desktop_hud_win.py` (130) + fakes
  `tests/hudhelp.py` (152), sab `<=200`; split ke baad **dono** test me bug
  wapas daal ke check kiya — fail hote hain (sirf production file badalne se test
  chup ho jaata). **Live pakkaura:** nayi code se `open_hud.main()` 3 baar → **1**
  window (pehle 3 → 4). Suite: **60 = 54 pass + 6 purane fail** (naya nahi).
  Branch `fix/hud-single` par commit — **push/merge nahi**. Naye rules section
  **8.1.4**.
- **S-2: STT/TTS tez + pakka (13 Oct 2026)** — branch `fix/stt-speed` (S-1 audit
  se). 4 badlav: (1) `voice/stt.py` brain wala 10 s + SDK 2 retry hata kar **STT
  ka apna 6 s + `max_retries=1`** + ceiling `config.stt_deadline()` 16 s. Ceiling
  ke liye **daemon thread + `join(timeout)`** — `asyncio.to_thread`/`wait_for`
  se kaam nahi chalta, kyunki `wake/listen.py` ke `asyncio.run()` ka shutdown
  executor ka join **wait** karta hai (pehle ka `wait_for` version test me hi
  3 s lag raha tha, yani ceiling chhoot hi gayi thi). (2) **401/403 pattern hi
  nahi tha** `brain/health_words.py` me — `classify()` `"other"` deta tha aur
  `classify_and_skip()` sirf `busy/billing/auth/empty` par karta hai, yaani
  ElevenLabs ka 401 **har jawab me dobara** poochha jaata tha. Ab `AUTH_RE` +
  `auth` → `lock_auth()` → session me BAND → seedha Edge; saath me
  `voice/tts.py` ka `missing_key()` (voice id check alag) taaki key khaali ho
  to provider 0 baar chale. (3) `COMMAND_END_SILENCE_SECONDS` **0.9 → 0.7**
  (`.env` ka `PRABH_CMD_SILENCE` raasta waisa). (4) naya `wake/pcm.py` ka
  `quality()` → `(peak_rms, clip_pct)` + `wake/utterance.py` ki capture log line
  me dono number (sirf number, audio save nahi). **Split:** `voice/tts.py` 202
  par ja raha tha → naya `voice/tts_text.py` (clean/clip/clip_answer + regex),
  `tts.py` se re-export taaki callers na toote. Naye test `test_stt_speed.py`,
  `test_tts_auth.py`, `test_wake_levels.py`; `test_speed_fix.py` ka 0.9 ka pakkaura
  update. Suite **63 = 57 pass + 6 purane fail** (naya nahi). **Live:** naye
  path se 3/3 sahi transcription (1.4-3.0 s). Rules section **8.1.5**.
