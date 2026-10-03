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
  config_desktop.py   -> tray rang, HUD size/path, crash backoff, exit codes, mic/lock helpers,
                        HUD_HOTKEY + HUD_SHORTCUT_NAME
  config_wake.py      -> wake word, VAD, command window, WhatsApp call ke constants
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
  desktop/playback.py -> Step 2 speaker: TTS bytes -> miniaudio PCM -> sounddevice
  desktop/open_hud.py -> shortcut + hotkey dono ka EK raasta (server zinda -> HUD)
  desktop/shortcut.py + hud_shortcut.ps1 -> Desktop ka "Sunday HUD" .lnk banao/hatao
  wake/worker.py     -> Step 1 ka module-level raasta (poori app me EK worker)
  wake/session.py    -> asli loop: mic -> VAD -> Vosk -> trigger (thread, cooldown, pause)
  wake/utterance.py + wake/wav.py -> Step 2a: command capture + WAV
  wake/listen.py     -> Step 2c ka mic wala hissa: drain/warmup/capture/to_text (STT)
  wake/command.py    -> Step 2c ka flow: ack -> suno -> brain -> awaaz (policy nahi)
  wake/audio.py      -> sounddevice se 16 kHz mono (mic ka EK owner) + energy Vad + PCM
  wake/model.py      -> Vosk model load + cache (khaali ya error = ModelMissing)
  wake/detect.py     -> KaldiRecognizer ka wrapper: JSON -> saaf text
  wake/phrase.py     -> "sunday" pakadna — pure functions
  start_prabh.bat    -> supervisor chalao (registry entry nahi, wo Step 3 ke aakhir me)
  ui/index.html, app.js (chat+ws glue), voice_ui.js (mic+speaker)
  ui/hud_base.css, hud_panel.css, hud_left.css, hud_center.css, hud_right.css, hud_bottom.css
  ui/hud_clock.js, hud_stats.js, hud_activity.js, hud_status.js, hud_orb.js,
  ui/hud_weather.js, hud_quick.js
  ui/hud_quick.js, hud_desktop.js (mic+wake ka sirf haalat)
  ui/recorder.js, speaker.js, tools.js (confirm card + ACTIVITY jodi)
  ui/fonts/*.woff2 + fonts.css (local, koi CDN nahi)
  tests/ (39 suite + poolhelp.py + desktophelp.py + hud_*.py + wakehelp.py + wakecmdhelp.py — poori list TESTS.md me)
  README.md, VOICE.md, TOOLS.md, BRAIN.md, TESTS.md, ROUND2.md, CHANGELOG.md
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

- **`on_wake(phrase, mic, stop)`** — `wake/session.py` ka `_fire()` teeno deta
  hai, kahin aur se mic **kabhi** mat lo. Ye **synchronous** hai (wake thread par),
  is liye command poore chal jaane tak sunna ruka rehta hai aur dobara "Sunday"
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
  `sunday` samajh kar phir uth jaata.
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

- 39 suite ki poori list, har suite ka detail aur naya test likhne ke niyam → **`TESTS.md`**.
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
  ko badal do. Asli check `python -m desktop.playback --say "..."` se.
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

---

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
- **HUD ke teen raasta ek hi function se:** `desktop/open_hud.py`. Server band ho to crash
  karne ke bajaye message box (pythonw me stdout nahi hota, is liye print kaam nahi karta).
- **PowerShell quoting JS me mat todo.** `.lnk` banane wala `.ps1` **alag file** rakho aur
  `subprocess` se `shell=False` par chalao.

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
  `python -m desktop.playback --say "Ji, boliye"` se bina app ke awaaz test ho jaati hai).
  Dono ka record `CHANGELOG.md`, detail `VOICE.md`.
- **Phase 5 Step 2c ho gaya (3 Oct 2026) — 37 suite green.** Wake ke baad poora command:
  "Ji, boliye" → mic queue drain + warm-up → capture (2.0 s khamoshi par band, max 30 s) →
  Groq STT → shared `server.state.ENGINE` → Hub/UI events + `via="voice"` → jawab ki awaaz
  (`desktop/playback.py`). Naye file `wake/listen.py` (mic wala hissa) + `wake/command.py`
  (flow), mute/lock par kuch nahi, ASK par sirf card + "confirm kijiye" (awaaz se ALLOW
  nahi). Teen naye suite: `test_wake_command.py` (flow), `test_wake_brain.py` (brain + ASK),
  `test_wake_listen.py` (mic/pause) + `tests/wakecmdhelp.py` (fakes). Record
  `CHANGELOG.md`, detail `VOICE.md`.
- **Baaqi Phase 5, isi order me:** **Step 3** auto-start (registry tabhi jab user "haan" bole).
  Face/trust/learn/maker baad me.
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
