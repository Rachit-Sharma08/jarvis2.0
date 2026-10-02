# Changelog (Prabh ka pura record)

`AGENTS.md` sirf **niyam** rakhta hai; kaam ka poora record yahan hai. Ek line =
ek kaam ka group. Doc ka detail `BRAIN.md`, `TOOLS.md`, `VOICE.md`, `TESTS.md`,
`ROUND2.md` me hai.

---

## PC wale kaam + fix round 3 ka record (2 Oct 2026 raat)

Code ka poora record upar hai. Ye sirf **project ke bahar** wale kaam hain â€” detail
`AGENTS.md` section **8.1** me.

- **Purana JARVIS auto-start hata diya** â€” `HKCU\Run` se `electron.app.Electron` value
  delete, backup `D:\prabh\backup\jarvis-autostart-20261002-141601.reg` (456 byte, UTF-16LE).
  `D:\jarvis` folder/exe chhua nahi, koi electron process nahi tha. Baaki 7 Run values shaant.
- **`D:\SystemConfig` ki poori jaanch** â€” chain, file dates (14-Sep-2026 shaam), "internet par
  kuch nahi bhejta" ka proof, startup-judne ka tareeka, aur chhupaye hue secrets ka record.
  **Koi badlav nahi kiya** â€” user ke "haan" ka wait. Reversible plan bhi likha hai.
- **Tray icon na dikhne ki asli wajah** â€” pystray nahi, Windows overflow. `NotifyIconSettings`
  me 22 icon me se sirf 1 `IsPromoted=1`; baaki 21 `^` chevron me. Icon register hua tha, bas
  dikha nahi. User ko `^` â†’ right-click â†’ "Always show icons" batana hai.
- **`localhost` vs `127.0.0.1`** â€” HUD hamesha `http://127.0.0.1:8000`, `localhost` se token reject.
- **Fix round 3 live verify** â€” naya code **asli** stale PID file saaf ki:
  `15:41:21 | WARNING | single | stale pid file hata di: D:\prabh\data\prabh.pid (pid=19584)`.
  `start_prabh.bat` dobara chalane par naya saaf message + exit 3.
- **Jahan chhoda** â€” app band, port khaali, pid file saaf, lock free, git clean. Agla step
  user ka: double-click â†’ `^` me icon â†’ "Always show icons". Iske baad Phase 5 Step 1 (Vosk).

---

## Phase 5 Step 3a fix round 3 (2 Oct 2026) â€” stale-lock message + tray guard

User ne live par do shikaayat ki: (1) dobara click karne par sirf "pehle se chal raha hai
(pid=...)" aata tha, kuch samajh nahi aata tha; (2) tray icon overflow me chhupne par lagta
tha ki app shuru hi nahi hua.

**1. "Chal raha hai" ab proof par hai, sirf lock par nahi**

- `desktop/single.py` me `pid_alive(pid, probe=None)` (Windows `OpenProcess` +
  `PROCESS_QUERY_LIMITED_INFORMATION`, doosre platform par `os.kill`) aur
  `http_alive(origin, opener=None)` (`GET /` ka status 200?) â€” dono probe injectable hain.
- `Single.diagnose(pid_probe=None, http_check=None)` 4 haal alag-alag bolta hai:
  - PID zinda + `GET /` 200 â†’ "pehle se CHAL raha hai (pid=...)"
  - PID zinda par 200 nahi â†’ "app atki hai, Task Manager se band karo"
  - PID murda par 200 â†’ "port 8000 kisi aur ka hai, ye lock stale nahi"
  - dono murda â†’ "lock stale hai, ye instance apne aap lock pakad lega"
- `os.kill(pid, 0)` jaan-boojh kar **nahi** likha â€” CPython isay `TerminateProcess` bana
  sakta hai. Ye baat `AGENTS.md` me pakkaari gayi hai.
- `_clean_stale_pid()` â€” lock milne ke baad mar ke bache `.pid` file apne aap hat jaati hai.
  Windows par `msvcrt` lock marne par khud release hota hai, is liye asli stale *lock* rare
  hai, stale `.pid` file hi common hai.
- `desktop/app.py` ab ye message **console par bhi** bolta hai (`print(..., flush=True)`),
  kyunki double-click karne wala user log nahi padhta.

Live verify (asli app ke against): `owner_pid = 19584` â†’
*"Sunday pehle se CHAL raha hai (pid=19584). Usi tray icon se Open HUD karo, ya Quit dabao."*
aur `start_prabh.bat` dobara chalane par wahi message + exit 3.

**2. Bina tray ke app ab chup-chaap nahi chalta**

- `desktop/tray.py` me `retry_start(tray, attempts=3, delay=1.5, sleep=None)` â€” alag
  function is liye ki test me `sleep` daal kar bina wait check ho jaaye.
- 3 koshish ke baad bhi icon na bane to `config.EXIT_NO_TRAY = 4` se saaf exit; launcher
  is par alag se bolta hai *"Wajah: tray icon nahi bana..."*. Bina tray ke app chalta rahe to
  usse band karne ka koi raasta hi nahi hota â€” is liye ye pehle se theek nahi tha.
- `run()` me `_start_tray()` ke baad `self._stop.is_set()` check â€” warna app server chalu
  karke aage badh jaata tha.

**3. Chhoti split**

- `desktop/actions.py` naya â€” tray ke 5 button ka faisla (`app.py` se nikaala, taaki
  `app.py` 200 line ke andar rahe).

**Test** â€” `tests/test_desktop.py` me 3 naye block: `STALE LOCK DIAGNOSE` (helper + 4
combination) Â· `STALE PID SELF-HEAL` (asli temp-dir end-to-end) Â· `TRAY GUARD` (retry count,
exit code, source check). Sab probe injectable â€” koi asli process/socket nahi chhua gaya.
**26 suite green.**

---

## Phase 5 Step 3a (2 Oct 2026) â€” desktop shell (tray + supervisor + Edge HUD)

Wake/face/trust/learn/maker ka poora plan `PLAN.md` + `PLAN-TRUST.md` me hai
(commit `081b7f7`). Abhi **sirf Step 3a** bana â€” wake sirf stub hai.

**Naye package** (`.venv` me, D: drive ke cache/temp se):
`vosk 0.3.45` Â· `sounddevice 0.5.6` Â· `numpy 2.5.3` Â· `miniaudio 1.71` Â·
`pystray 0.19.5`. Aage ka chhota plan: `wake word` â†’ `mic` â†’ `chime` â†’
`baat sunai de` (sirf Step 1-3; face se pehle).

**Vosk model** (Step 1 ke liye pehle se download): `models/vosk-model-small-en-us-0.15`
â€” 41,205,931 byte, SHA256 `30F26242C4EB449F948E42CB302DD7A686CB29A3423A8367F99FF41780942498`.
Model load + grammar smoke `MODEL OK`. `models/` git-ignore hai.

**Naye files**

- `config_desktop.py` â€” tray ke 5 rang, HUD 1200x720, crash backoff (2/5/10/20/30s),
  exit code (0 quit Â· 1 crash Â· 3 already running), Edge path, `browser_path()`.
- `desktop/launcher.py` â€” supervisor. `next_step()` **pure function** hai (test me
  crash list wapas deta hai, mutate nahi karta), `supervise()` child spawn karta hai.
  Crash par backoff, 5 crash ke baad ruk jaata aur `logs/desktop.out` ka tail log karta hai.
- `desktop/app.py` â€” server thread + tray + HUD + `micperm` + `lockwatch`, sab ek
  jagah se. Server ready hone ka wait 15s.
- `desktop/tray.py` / `trayicon.py` â€” menu: haalat / Mic Mute / Open HUD / TOOLS /
  Restart / Quit. Icon Pillow se 64x64, mic ka nishaan har state me, rang alag.
- `desktop/hud_window.py` â€” Edge `--app` primary, Chrome fallback, apna profile
  (`data/hud-profile`), `--window-size=1200,720`. Is machine par Edge mila.
- `desktop/single.py` â€” `msvcrt.locking` se ek hi instance; doosra exit code 3.
- `desktop/state.py` â€” ek `STATE`: mic/mute/tools/HUD/wake + version, WebSocket par
  `{"type":"desktop"}`.
- `desktop/micperm.py` â€” `HKCU\...\ConsentStore\microphone` (master `Allow` +
  `NonPackaged\<exe>`). Is machine par master `Allow`, python ki entry abhi nahi â€”
  matlab pehli baar Windows poochega.
- `desktop/lockwatch.py` â€” `OpenInputDesktop(DESKTOP_SWITCHDESKTOP)` heuristic;
  locked + tools ON ho to tools OFF. Locked hone par bhi **rukta nahi** (per soch).
- `wake/worker.py` â€” sirf stub (`start()` -> False, `READY=False`), Step 1 me bharega.
- `ui/hud_desktop.js` â€” top bar ka DESKTOP pill (mic + wake). Sirf dikhata hai.
- `start_prabh.bat` â€” supervisor chalao, crash ka log batao.

**Badhle hue**

- `config.py` â€” `config_desktop` re-export, `DEFAULT_MODE="sunday"`,
  `SUNDAY_ONLY` (`PRABH_SUNDAY_ONLY`, default `1`). Prabh ka code **hataya nahi**,
  sirf switch band hai.
- `core/modes.py` â€” `SUNDAY_ONLY` on par Prabh prefix mode nahi badalta, text waise
  jaata hai.
- `gatekeeper/limiter.py` â€” TOOLS **30 minute** baad apne aap OFF (`minutes_left()`
  bhi). `0` minute = auto-off band.
- `tests/test_basic.py`, `test_voice.py` â€” Sunday-only ke hisaab se theek kiya
  (flag off karke switch chalta hai ye bhi check hota hai).
- `.gitignore` â€” `data/`, `models/`, `.cache/`, `.tmp/`. `.env.example` me
  `PRABH_SUNDAY_ONLY`, `PRABH_TOOLS_ON`, `PRABH_HUD_AT_START`.

**Test** â€” `tests/test_desktop.py` + `tests/test_desktop_tray.py` (naya helper
`tests/desktophelp.py`). Koi asli Edge/tray/registry/mic nahi chalti. **25 suite green.**

**Asli app chala kar 4 bug pakde** (sirf test se nahi):

1. `app.py` me `NameError: open_hud_at_start` â€” app shuru hi hote hue gir raha tha
   (supervisor 5 baar restart kar raha tha). Test ise miss karta tha kyunki koi
   test `run()` tak nahi jaata tha.
2. `single.py` PID hamesha `0` dikha raha tha â€” lock wali file ka pehla byte locked
   hone par dusra process use **padh hi nahi sakta** (`ERROR_SHARING_VIOLATION`).
   Ab PID alag `data/prabh.pid` me.
3. HUD ka DESKTOP pill `DESKTOP â€¦` hi reh raha tha â€” state WebSocket se pehle set
   ho chuki thi, is liye `publish()` ka event kisi ko nahi mila. Ab `Hub.welcome()`
   hook: naye client ko turant snapshot milta hai.
4. TOOLS toggle HUD se karne par tray icon nahi badalta tha (`/tools/toggle` seedha
   `keeper` ko bulata tha). Ab `Limiter.set_on_change()` hook hai â€” TOOLS kahin se
   bhi badle, `STATE` ek hi raaste se update hota hai (auto-off timer bhi).

**Manual check (asli app):** `GET /` 200 Â· token meta + DESKTOP pill present Â·
`/hud/stats` bina token 401 Â· doosra instance exit 3 (PID sahit) Â·
Edge `--app` sach me khula Â· tray ready Â· koi crash nahi (`logs/desktop.out` khali).

**Abhi nahi hua (jaan-boojh kar)** â€” wake word (Step 1), VAD/command flow (Step 2),
aur **auto-start**. Registry me koi entry nahi likhi gayi hai.

## Fix round 2 â€” `start_prabh.bat` launch hi nahi ho raha tha (2 Oct 2026)

User ne bataya: double-click par na tray icon, na python process â€” sirf
"Press any key to continue". Ye **test se nahi, bilkul fresh shuruat se** pakda
gaya (purane code par koi test nahi tha).

**Asli wajah â€” ek `echo` line par raw bracket.** `cmd` ka `if not exist (...)`
block, kisi bhi uske andar ki line par `( )` milte hi beech me toot jaata hai:

```
if not exist ".venv\Scripts\python.exe" (
  echo .venv nahi mila...
  echo Download: https://www.python.org/downloads/  (Python 3.12)   <-- block KHATAM
)
pause          <-- ab ye HAMESHA chalta hai
exit /b 1      <-- aur ye bhi HAMESHA -> python KABHI launch nahi hua
```

Proof `cmd /c` ke `@echo on` trace se. Isiliye echo lines bhi kabhi print nahi
huyin â€” `exit /b 1` unse pehle chala gaya.

**5 fix:**

1. `start_prabh.bat` â€” bracket block hata kar `goto novenv` label; poori file
   **CRLF** (pehle 19 LF / 0 CRLF â€” Windows `.bat` ko CRLF chahiye); ASCII only.
2. `desktop/launcher.py` â€” child ka stdout ab **console + `logs/desktop.out`
   dono** me jaata hai (`_tee`). Har crash par console par `CRASH #n/limit`,
   exit code, backoff aur crash ki **wajah** bhi print hoti hai (`_console`).
   Pehle crash sirf `log.error` me thi â€” user ko console par kuch nahi dikhta
   tha, matlab app "chup-chaap mar" sakta tha.
3. **Startup ki 4 line ek jagah** â€” `server up` / `tray started` /
   `HUD ready` / `wake: stub`. Shabd `config_desktop.STARTUP_*` me, bolta sirf
   `desktop/app.py` (naya `desktop/startup.py` helper: `say()` + `await_http()`).
   Console par **aur** `logs/prabh.log` dono me. `HUD ready` ab sach me
   `GET /` ka 200 check karta hai â€” nahi mila to `HUD ready: FAILED - <wajah>`,
   chup-chaap nahi. `server/app.py` ka duplicate log hata diya.
4. `log_setup.py` â€” `ascii_text()` + `AsciiFormatter`; file `encoding="ascii"`.
   Pehle `wake word ... â€” mic nahi khula` log me `??` ban kar aata tha (console
   `cp1252` hai). Ab em-dash `-`, arrow `->`, baaki Unicode hata deta hai.
5. `tests/test_bat.py` (naya) â€” CRLF check, ASCII check, **raw bracket rule**
   (bracket sirf `if`/`for`/`else` line par), aur asli pakka test: file ki copy
   me python line ki jagah `echo` daal kar `cmd` se chala kar dekho ki line
   sach me pahunchti hai ya nahi. Buggy file par ye test fail hota hai
   (sirf "Press any key to continue" aata hai) â€” manually confirm kiya.

**Live (asli double-click jaisa, `cmd /c start_prabh.bat`):**

```
server up: http://127.0.0.1:8000
tray started: Sunday
HUD ready: stats pump + 6 quick buttons
wake: stub: Step 1 me aayega - mic nahi khula
```

Tray icon window mila (`Sunday...SystemTrayIcon`, pid 13668), `GET /` = 200.

**Purana JARVIS auto-start (sirf bataya, chhua nahi):**
`HKCU\...\Run` me `electron.app.Electron` â†’
`D:\jarvis\desktop\node_modules\electron\dist\electron.exe D:\jarvis\desktop --hidden`.
`D:\jarvis` abhi bhi maujood hai. Startup folder me Jarvis nahi â€” sirf
`start_local_hidden.vbs` (VoiceMemories AI ka `node local_host.js`) aur
`SystemConfig.bat` (`D:\SystemConfig\run-all.ps1`). Koi scheduled task nahi.

**26 suite green.**

---

## Phase 4 (1-2 Oct 2026) â€” 3-column HUD

**Reference photo** â€” `D:\Pictures\sunday.jpg` se `design/reference.png` copy ki.
4080x2416, gehra navy, beech me bright cyan orb, cream-white bright text. Programmatic
analysis se mila (is model me image vision nahi). Amber (`#f5a623`) reference me nahi
mila, wo sirf listening-state ke liye rakha gaya.

**Server (commit `5536a6d`)**
- `config_hud.py` â€” HUD rang, Delhi coords, 15 min weather cache, WMO labels, 6 quick button.
- `core/sysstats.py` â€” `psutil` se CPU/RAM/battery/disk/network, 1.5s cache + `prime()`.
  `requirements.txt` me `psutil` add.
- `server/weather.py` â€” Open-Meteo fetch, 15 min cache, crash-safe parse, `"No data"`.
- `server/hub.py` + `server/drain.py` â€” thread-safe event hub + async engine drain.
- `server/ws_routes.py` â€” `/ws` chat + har ~2s `"stats"` WebSocket event.
- `server/hud_routes.py` â€” `GET /hud/stats`, `GET /hud/weather`, `POST /hud/quick`.

**UI (commit `65fbf53`)**
- `ui/index.html` â€” 3-column HUD: LEFT (chronometer + SYSTEM + ACTIVITY),
  CENTER (orb + conversation), RIGHT (weather + chat log). Quick buttons bottom me.
- CSS 6 file me split: `hud_base.css`, `hud_panel.css`, `hud_left.css`,
  `hud_center.css`, `hud_right.css`, `hud_bottom.css`.
  Purane `style.css` + `tools.css` delete.
- 7 naye JS: `hud_clock`, `hud_stats`, `hud_activity`, `hud_status`, `hud_orb`,
  `hud_weather`, `hud_quick`. `app.js` sirf chat + WebSocket glue raha.
- Local fonts (Orbitron / Rajdhani / Share Tech Mono) `ui/fonts/` me + OFL license.

**Live browser me pakde gaye asli bug**
1. **Same-origin GET 403** â€” browser GET par `Origin` header bhejta hi nahi, to
   `/brain/status` aur `/hud/weather` browser me kabhi chalti hi nahi thi. Ab
   `security.same_origin_proof()` Referer ya `Sec-Fetch-Site: same-origin` maangta
   hai, aur `Referrer-Policy` `no-referrer` se `same-origin` kiya gaya (warna
   Referer aata hi nahi). Test: `hud_check_get.py`.
2. **Grid overflow** â€” `24% 50% 26%` + `gap` + padding = 1366 par 1372px (scroll bar).
   Ab `minmax(0, 24fr) minmax(0, 50fr) minmax(0, 26fr)`.
3. **Teen alag Engine** â€” `app.py`, `ws_routes.py`, `hud_routes.py` teenon apna
   `Engine()` bana rahe the (mode drift). Ab `server/state.py` me ek.
4. **Orb core** â€” CSS `fill: radial-gradient()` SVG me invalid hai, circle kaali thi.
   Ab index.html me `<radialGradient id="coreGrad">`.
5. **SYSTEM pill** â€” startup par `active_tier: null` se OFFLINE dikhta tha. Ab ready
   provider (key + cooldown nahi) hone par ONLINE.
6. **STOP button** â€” sirf awaaz rokta tha, pending tool card nahi. Ab dono.
7. `/hud/quick` ka `QuickIn` extra fields ignore kar raha tha â†’ ab `extra="forbid"`.
8. Network `MB` â†’ `MB/s`, activity tag `DENY` â†’ `DENIED`.

**Verify**
- 23/23 suite green, sab file `<200` lines.
- Live Chrome 1366x768: 0 failed request, 0 page error, koi scroll nahi,
  teenon column apni jagah, teen fonts loaded, weather + stats + brain reply live.

---

## Round 2 (1-2 Oct 2026) â€” brain pool, suraksha, voice

| Kya bana | File |
|---|---|
| Do-tier brain pool + provider order | `brain/pool.py`, `brain/pool_config.py` |
| OpenAI-compatible adapter (chat + GET models) | `brain/openai_pool.py` |
| NVIDIA pool-wide 30/min sliding window | `brain/limiter.py` |
| Cooldown/lock/quota + error-word categories | `brain/health.py`, `brain/health_words.py` |
| Manual strict-JSON probe + 24h cache | `brain/probe.py` |
| Startup par sirf free `/models` check | `brain/checkup.py` |
| `GET /brain/status` (masked) | `server/brain_routes.py` |
| Dynamic `.env` masking + `nvapi_` pattern | `gatekeeper/audit.py` |
| Dono mode female-only + female allowlist | `voice/tts_female.py`, `config_voice.py` |
| STT guard (duration/silence/script) | `voice/stt_guard.py`, `voice/stt.py` |
| `SUNDAY` / `PRABH` answer label | `core/events.py`, `core/modes.py`, `core/engine.py`, `ui/app.js` |
| Config split | `config_brain.py`, `config_voice.py` |
| UI split | `ui/voice_ui.js` |
| Docs | `TESTS.md` + BRAIN/VOICE/TOOLS/README/AGENTS update |

**Live probe (Sept-Oct 2026):**

- NVIDIA `nemotron-3-super-120b-a12b` â€” strict JSON **pass**, ~1.0s â†’ winner.
- NVIDIA `nemotron-3.5-lightning-30b-a3b` â€” 60s+ timeout â†’ fail.
- NVIDIA `nemotron-nano-3-30b-a3b` â€” **404** â†’ pool se bahar.
- OpenRouter `nemotron-3-super-120b-a12b:free` â€” strict JSON **pass**, ~1.2s.
- OpenRouter `qwen3.8-27b:free` â€” **429**.
- NVIDIA free trial = 1000 credits; credits khatam par HTTP **402**.

**Result:** 22 suite green (`SUITE GREEN`), sab file `<200` lines.

---

## Fix round 1

- Models fix + fallback (Groq 10s / Gemini 15s, 503 par 1 retry).
- `brain/health.py` â€” 404 â†’ model GONE, 402/429/503/timeout â†’ 10 min rest.
- Startup `/models` check + warning banner.
- `core/timing.py` â€” stage + total timing.
- Dono brain provider fail ho to **ek hi** message.
- `rid` + UI message dedupe.
- Prabh ki awaaz female, Cartesia ka Hindi payload fix.
- `BRAIN.md` bana. 15 suite.

**Root cause (jaanch):** khaali jawab `max_tokens=800` + reasoning model â€” content
token me hi khatam ho jata tha. Fix: `max_tokens` 1600/3200, `reasoning_effort=low`,
aur khaali/length/ghalat JSON = failure count.

---

## Phase 3 (PC tools)

- `gatekeeper/` + `tools/` â€” 10 tools, Recycle Bin delete, scrubbed env.
- Strict tool JSON + duplicate-key reject.
- 5-step tool loop.
- `server/tool_routes.py` + UI (ACTIVITY panel, confirm card, `TOOLS`, `STOP`).
- Confirm card ki detail me secret masking.
- 4 badi file split.
- Docs: `TOOLS.md`, `VOICE.md`.

---

## Phase 1-2 (skeleton)

- Skeleton, brain (Groq â†’ Gemini), personas, mode switch.
- Engine + events, FastAPI (`/chat`, `/ws`), HUD UI.
- Suraksha: 127.0.0.1 only, Origin + Host check, per-start token, CORS band.
- Voice: `stt.py`, TTS chain, `/stt` + `/tts`, mic UI, 500 char limit.
- Tests.

---

## Keys

- `.env` me 6 brain/voice keys + voice ids (values kabhi commit nahi).
- `.env.example` me sirf naam.
- `.env` git-ignored.
