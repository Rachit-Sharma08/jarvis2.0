# Changelog (Prabh ka pura record)

`AGENTS.md` sirf **niyam** rakhta hai; kaam ka poora record yahan hai. Ek line =
ek kaam ka group. Doc ka detail `BRAIN.md`, `TOOLS.md`, `VOICE.md`, `TESTS.md`,
`ROUND2.md` me hai.

---

## Phase 5 Step 3a (2 Oct 2026) — desktop shell (tray + supervisor + Edge HUD)

Wake/face/trust/learn/maker ka poora plan `PLAN.md` + `PLAN-TRUST.md` me hai
(commit `081b7f7`). Abhi **sirf Step 3a** bana — wake sirf stub hai.

**Naye package** (`.venv` me, D: drive ke cache/temp se):
`vosk 0.3.45` · `sounddevice 0.5.6` · `numpy 2.5.3` · `miniaudio 1.71` ·
`pystray 0.19.5`. Aage ka chhota plan: `wake word` → `mic` → `chime` →
`baat sunai de` (sirf Step 1-3; face se pehle).

**Vosk model** (Step 1 ke liye pehle se download): `models/vosk-model-small-en-us-0.15`
— 41,205,931 byte, SHA256 `30F26242C4EB449F948E42CB302DD7A686CB29A3423A8367F99FF41780942498`.
Model load + grammar smoke `MODEL OK`. `models/` git-ignore hai.

**Naye files**

- `config_desktop.py` — tray ke 5 rang, HUD 1200x720, crash backoff (2/5/10/20/30s),
  exit code (0 quit · 1 crash · 3 already running), Edge path, `browser_path()`.
- `desktop/launcher.py` — supervisor. `next_step()` **pure function** hai (test me
  crash list wapas deta hai, mutate nahi karta), `supervise()` child spawn karta hai.
  Crash par backoff, 5 crash ke baad ruk jaata aur `logs/desktop.out` ka tail log karta hai.
- `desktop/app.py` — server thread + tray + HUD + `micperm` + `lockwatch`, sab ek
  jagah se. Server ready hone ka wait 15s.
- `desktop/tray.py` / `trayicon.py` — menu: haalat / Mic Mute / Open HUD / TOOLS /
  Restart / Quit. Icon Pillow se 64x64, mic ka nishaan har state me, rang alag.
- `desktop/hud_window.py` — Edge `--app` primary, Chrome fallback, apna profile
  (`data/hud-profile`), `--window-size=1200,720`. Is machine par Edge mila.
- `desktop/single.py` — `msvcrt.locking` se ek hi instance; doosra exit code 3.
- `desktop/state.py` — ek `STATE`: mic/mute/tools/HUD/wake + version, WebSocket par
  `{"type":"desktop"}`.
- `desktop/micperm.py` — `HKCU\...\ConsentStore\microphone` (master `Allow` +
  `NonPackaged\<exe>`). Is machine par master `Allow`, python ki entry abhi nahi —
  matlab pehli baar Windows poochega.
- `desktop/lockwatch.py` — `OpenInputDesktop(DESKTOP_SWITCHDESKTOP)` heuristic;
  locked + tools ON ho to tools OFF. Locked hone par bhi **rukta nahi** (per soch).
- `wake/worker.py` — sirf stub (`start()` -> False, `READY=False`), Step 1 me bharega.
- `ui/hud_desktop.js` — top bar ka DESKTOP pill (mic + wake). Sirf dikhata hai.
- `start_prabh.bat` — supervisor chalao, crash ka log batao.

**Badhle hue**

- `config.py` — `config_desktop` re-export, `DEFAULT_MODE="sunday"`,
  `SUNDAY_ONLY` (`PRABH_SUNDAY_ONLY`, default `1`). Prabh ka code **hataya nahi**,
  sirf switch band hai.
- `core/modes.py` — `SUNDAY_ONLY` on par Prabh prefix mode nahi badalta, text waise
  jaata hai.
- `gatekeeper/limiter.py` — TOOLS **30 minute** baad apne aap OFF (`minutes_left()`
  bhi). `0` minute = auto-off band.
- `tests/test_basic.py`, `test_voice.py` — Sunday-only ke hisaab se theek kiya
  (flag off karke switch chalta hai ye bhi check hota hai).
- `.gitignore` — `data/`, `models/`, `.cache/`, `.tmp/`. `.env.example` me
  `PRABH_SUNDAY_ONLY`, `PRABH_TOOLS_ON`, `PRABH_HUD_AT_START`.

**Test** — `tests/test_desktop.py` + `tests/test_desktop_tray.py` (naya helper
`tests/desktophelp.py`). Koi asli Edge/tray/registry/mic nahi chalti. **25 suite green.**

**Abhi nahi hua (jaan-boojh kar)** — wake word (Step 1), VAD/command flow (Step 2),
aur **auto-start**. Registry me koi entry nahi likhi gayi hai.

---

## Phase 4 (1-2 Oct 2026) — 3-column HUD

**Reference photo** — `D:\Pictures\sunday.jpg` se `design/reference.png` copy ki.
4080x2416, gehra navy, beech me bright cyan orb, cream-white bright text. Programmatic
analysis se mila (is model me image vision nahi). Amber (`#f5a623`) reference me nahi
mila, wo sirf listening-state ke liye rakha gaya.

**Server (commit `5536a6d`)**
- `config_hud.py` — HUD rang, Delhi coords, 15 min weather cache, WMO labels, 6 quick button.
- `core/sysstats.py` — `psutil` se CPU/RAM/battery/disk/network, 1.5s cache + `prime()`.
  `requirements.txt` me `psutil` add.
- `server/weather.py` — Open-Meteo fetch, 15 min cache, crash-safe parse, `"No data"`.
- `server/hub.py` + `server/drain.py` — thread-safe event hub + async engine drain.
- `server/ws_routes.py` — `/ws` chat + har ~2s `"stats"` WebSocket event.
- `server/hud_routes.py` — `GET /hud/stats`, `GET /hud/weather`, `POST /hud/quick`.

**UI (commit `65fbf53`)**
- `ui/index.html` — 3-column HUD: LEFT (chronometer + SYSTEM + ACTIVITY),
  CENTER (orb + conversation), RIGHT (weather + chat log). Quick buttons bottom me.
- CSS 6 file me split: `hud_base.css`, `hud_panel.css`, `hud_left.css`,
  `hud_center.css`, `hud_right.css`, `hud_bottom.css`.
  Purane `style.css` + `tools.css` delete.
- 7 naye JS: `hud_clock`, `hud_stats`, `hud_activity`, `hud_status`, `hud_orb`,
  `hud_weather`, `hud_quick`. `app.js` sirf chat + WebSocket glue raha.
- Local fonts (Orbitron / Rajdhani / Share Tech Mono) `ui/fonts/` me + OFL license.

**Live browser me pakde gaye asli bug**
1. **Same-origin GET 403** — browser GET par `Origin` header bhejta hi nahi, to
   `/brain/status` aur `/hud/weather` browser me kabhi chalti hi nahi thi. Ab
   `security.same_origin_proof()` Referer ya `Sec-Fetch-Site: same-origin` maangta
   hai, aur `Referrer-Policy` `no-referrer` se `same-origin` kiya gaya (warna
   Referer aata hi nahi). Test: `hud_check_get.py`.
2. **Grid overflow** — `24% 50% 26%` + `gap` + padding = 1366 par 1372px (scroll bar).
   Ab `minmax(0, 24fr) minmax(0, 50fr) minmax(0, 26fr)`.
3. **Teen alag Engine** — `app.py`, `ws_routes.py`, `hud_routes.py` teenon apna
   `Engine()` bana rahe the (mode drift). Ab `server/state.py` me ek.
4. **Orb core** — CSS `fill: radial-gradient()` SVG me invalid hai, circle kaali thi.
   Ab index.html me `<radialGradient id="coreGrad">`.
5. **SYSTEM pill** — startup par `active_tier: null` se OFFLINE dikhta tha. Ab ready
   provider (key + cooldown nahi) hone par ONLINE.
6. **STOP button** — sirf awaaz rokta tha, pending tool card nahi. Ab dono.
7. `/hud/quick` ka `QuickIn` extra fields ignore kar raha tha → ab `extra="forbid"`.
8. Network `MB` → `MB/s`, activity tag `DENY` → `DENIED`.

**Verify**
- 23/23 suite green, sab file `<200` lines.
- Live Chrome 1366x768: 0 failed request, 0 page error, koi scroll nahi,
  teenon column apni jagah, teen fonts loaded, weather + stats + brain reply live.

---

## Round 2 (1-2 Oct 2026) — brain pool, suraksha, voice

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

- NVIDIA `nemotron-3-super-120b-a12b` — strict JSON **pass**, ~1.0s → winner.
- NVIDIA `nemotron-3.5-lightning-30b-a3b` — 60s+ timeout → fail.
- NVIDIA `nemotron-nano-3-30b-a3b` — **404** → pool se bahar.
- OpenRouter `nemotron-3-super-120b-a12b:free` — strict JSON **pass**, ~1.2s.
- OpenRouter `qwen3.8-27b:free` — **429**.
- NVIDIA free trial = 1000 credits; credits khatam par HTTP **402**.

**Result:** 22 suite green (`SUITE GREEN`), sab file `<200` lines.

---

## Fix round 1

- Models fix + fallback (Groq 10s / Gemini 15s, 503 par 1 retry).
- `brain/health.py` — 404 → model GONE, 402/429/503/timeout → 10 min rest.
- Startup `/models` check + warning banner.
- `core/timing.py` — stage + total timing.
- Dono brain provider fail ho to **ek hi** message.
- `rid` + UI message dedupe.
- Prabh ki awaaz female, Cartesia ka Hindi payload fix.
- `BRAIN.md` bana. 15 suite.

**Root cause (jaanch):** khaali jawab `max_tokens=800` + reasoning model — content
token me hi khatam ho jata tha. Fix: `max_tokens` 1600/3200, `reasoning_effort=low`,
aur khaali/length/ghalat JSON = failure count.

---

## Phase 3 (PC tools)

- `gatekeeper/` + `tools/` — 10 tools, Recycle Bin delete, scrubbed env.
- Strict tool JSON + duplicate-key reject.
- 5-step tool loop.
- `server/tool_routes.py` + UI (ACTIVITY panel, confirm card, `TOOLS`, `STOP`).
- Confirm card ki detail me secret masking.
- 4 badi file split.
- Docs: `TOOLS.md`, `VOICE.md`.

---

## Phase 1-2 (skeleton)

- Skeleton, brain (Groq → Gemini), personas, mode switch.
- Engine + events, FastAPI (`/chat`, `/ws`), HUD UI.
- Suraksha: 127.0.0.1 only, Origin + Host check, per-start token, CORS band.
- Voice: `stt.py`, TTS chain, `/stt` + `/tts`, mic UI, 500 char limit.
- Tests.

---

## Keys

- `.env` me 6 brain/voice keys + voice ids (values kabhi commit nahi).
- `.env.example` me sirf naam.
- `.env` git-ignored.
