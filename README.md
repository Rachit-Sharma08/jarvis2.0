# Jarvis

> **Ye ek local personal app hai, sirf is PC par chalta hai.** Ye web app nahi hai —
> doosre PC, phone ya internet se koi ise khol nahi sakta.

Ye ek hi AI assistant hai — **Jarvis**: Hinglish, chhote aur saaf jawab, seedha tone
("sir", pehle haalat phir salah, bakwaas nahi).

Browser me chalta hai, Windows 10/11 par, sab kuch free tools se. Mic se baat kar sakta
hai aur PC ke kaam bhi kar sakta hai (file, folder, app, command). Har call pehle
gatekeeper se guzarti hai — safe kaam seedha chalta hai, khatarnak block hota hai, aur
sab kuch `logs/actions.log` me likha jaata hai.

> **Privacy:** brain aur tools **free providers** (Groq, Gemini, OpenRouter, NVIDIA) par
> chalti hain, to message aur padhi hui file ka text unke paas jaata hai. Personal ya
> confidential file ka content mat pucho, aur private kaam ke liye tools OFF rakho.
> Poori baat [BRAIN.md](BRAIN.md) aur [TOOLS.md](TOOLS.md) me.

- Test detail ke liye → [TESTS.md](TESTS.md)
- Awaaz ke liye → [VOICE.md](VOICE.md)
- Brain (models, fallback, error) ke liye → [BRAIN.md](BRAIN.md)
- PC ke kaam ke liye → [TOOLS.md](TOOLS.md)
- Kisi bhi AI ko ye project sikhana ho → **[NEW_AGENT_BRIEF.md](NEW_AGENT_BRIEF.md)**
  (nayi Claude/agent chat me **paste karne wala self-contained prompt** — kya hai, kya use
  hua, kahan tak pahuncha, kya bacha, kaam ke niyam). Chhota handoff → **[CLAUDE.md](CLAUDE.md)**;
  poore niyam → **[AGENTS.md](AGENTS.md)**.
- Aage ka plan (Stage 02-06 status, bugs + guards, free-only stack, task order) →
  **[docs/ROADMAP_STATUS.md](docs/ROADMAP_STATUS.md)**

---

## 1. Install (ek hi baar)

PowerShell me `D:\Projects\jarvis\jarvis2.0` jao:

```powershell
cd D:\Projects\jarvis\jarvis2.0
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### API keys daalo

1. `.env.example` ko copy karke `.env` banao (agar `.env` pehle se hai to skip):

```powershell
Copy-Item .env.example .env
```

2. `.env` kholo aur keys daalo:

```
GROQ_API_KEY=apni_groq_key
GEMINI_API_KEY=apni_gemini_key
NVIDIA_API_KEY=apni_nvidia_key
OPENROUTER_API_KEY=apni_openrouter_key

ELEVENLABS_API_KEY=
CARTESIA_API_KEY=
ELEVENLABS_VOICE_SUNDAY=
CARTESIA_VOICE_SUNDAY=
```

Sirf `GROQ_API_KEY` zaruri hai (chat + mic dono). Baaki sab optional hain — jitni
keys doge, utne hi providers fail hone par agle par chal jayenge.
Key kahan se milegi: Groq https://console.groq.com/keys ·
Gemini https://aistudio.google.com/apikey ·
NVIDIA https://build.nvidia.com (1000 free credits) ·
OpenRouter https://openrouter.ai/keys (sirf `:free` model use hota hai) ·
ElevenLabs https://elevenlabs.io/app/developers/api-keys ·
Cartesia https://cartesia.ai/dashboard

> Key kabhi code ya chat me mat likho. `.env` git-ignore hai, wo kabhi commit nahi hoga.

### Wake word ka model (ek hi baar, ~40 MB)

"Jarvis" bolne par sunne ke liye Vosk ka chhota English model chahiye. `models/` git me
nahi hai (40 MB), is liye ek hi baar download karna padta hai:

```powershell
New-Item -ItemType Directory -Force models | Out-Null
Invoke-WebRequest -Uri https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -OutFile "$env:TEMP\vosk.zip"
Expand-Archive "$env:TEMP\vosk.zip" -DestinationPath models -Force
```

Na ho to app chalega par wake word band rahega — startup line me wajah dikhegi.
Detail → [VOICE.md](VOICE.md).

---

## 2. Chalao

### Raasta A — Jarvis (recommended, naya)

`start_jarvis.bat` par double-click. Ye:

1. ek supervisor (launcher) chalao,
2. Jarvis app ke andar server + **tray icon** + HUD window khulta hai,
3. crash ho to supervisor dobara chala deta hai (5 baar, phir ruk jaata hai).

Tray icon (taskbar ke right side, chhupa karo tab par):

| Item | Kya karta hai |
| --- | --- |
| upar wali line | haalat (mic band / sun raha / mute / error) |
| Mic Mute | mic on-off |
| Open HUD | HUD window kholta hai |
| ya phir Ctrl+Alt+S | wahi kaam, bina mouse ke (badal sakte ho) |
| TOOLS | PC tools on-off |
| Restart | app dobara |
| Quit | band |

### Tray icon na dikhe to — ye 3 raasta hai

Windows 11 taskbar ke icon chhupa deta hai (`^` wale overflow menu me). Tab bhi
HUD kholne ke **teen** raasta hain, teeno ek hi kaam karte hain:

| Raasta | Kaise |
| --- | --- |
| Tray ka menu | `^` par click → Jarvis → **Open HUD** |
| Desktop shortcut | Desktop par **"Jarvis HUD"** par double-click |
| Global hotkey | **Ctrl + Alt + S** (poore Windows me) |

Hotkey badalna ho to `.env` me `JARVIS_HUD_HOTKEY=<ctrl+alt+shift+s>` (ek letter
ya F1–F24). Galat value ho to hotkey chalti hi nahi — app safe rehti hai.

Teeno ka ek hi raasta `desktop/open_hud.py` hai: server chalu hai to HUD khulta
hai, warna ek message box aata hai "pehle `start_jarvis.bat` chalao".

Shortcut dobara banana ho to:

```powershell
cd D:\Projects\jarvis\jarvis2.0
.\.venv\Scripts\python.exe -m desktop.shortcut install   # ya: remove / status
```

Sunke chalana **ab poora kaam karta hai** — app shuru hote hi mic khul kar
"jarvis" sunta hai. "Jarvis" bolte hi HUD khulta hai, Jarvis **"Ji, boliye"**
bolta hai, aap apni baat bolo, aur jawab **awaaz me** aa jaata hai.

```
Jarvis  ->  "Ji, boliye"  ->  aapki baat (2 s chup par band, 30 s max)
        ->  brain  ->  HUD par jawab + awaaz
```

- ❌ Suna nahi → "Main theek se sun nahi paya, dobara boliye."
- ❓ Tool chahiye → HUD par confirm card + "Screen par confirm kijiye." —
  **allow hamesha screen ke button se, awaaz se nahi.**
- 🔇 Tray ka **MUTE** ya PC lock → command bilkul nahi chalta.

Details `VOICE.md` me. Band karna ho to `.env` me `JARVIS_WAKE=0`, ya `.env` me
`JARVIS_CMD_SILENCE=2.0` se chup-hone ka wait badal sakte ho.

> Awaaz se **sirf baat** hoti hai — koi tool, koi file delete, koi setting badal
> nahi. Ye `TOOLS.md` me hai.

Band karne ke liye tray me **Quit**. Sirf window band karne se app nahi rukta.

### Windows login par khud chalu ho (auto-start)

Har login par Jarvis khud chalega — koi double-click nahi. Ye `HKCU` ki ek
value hai, is liye **admin ya UAC nahi chahiye**.

Pehle check karo (sirf padhta hai, kuch nahi badalta):

```powershell
cd D:\Projects\jarvis\jarvis2.0
.\.venv\Scripts\python.exe -m desktop.autostart status
```

On karna ho to (ye **sirf ek value** likhta hai):

```powershell
.\.venv\Scripts\python.exe -m desktop.autostart install
.\.venv\Scripts\python.exe -m desktop.autostart remove    # band karna ho
```

- Value ka naam `Jarvis` hai, aur value khud ye chalati hai:
  `D:\Projects\jarvis\jarvis2.0\.venv\Scripts\pythonw.exe D:\Projects\jarvis\jarvis2.0\desktop\launcher.py` — wahi
  supervisor jo `start_jarvis.bat` chalaata hai. `pythonw` ki wajah se login par
  koi black console nahi aata.
- Value me `-m desktop.launcher` **nahi** likha jaata: Windows Run key par cwd
  `C:\Windows\System32` hota hai aur wahan se module import hi nahi hota. File
  ka path likhne se app sahi chalti hai.
- Crash par kuch dikhta nahi hai, par `logs\desktop.out` me likha hota hai —
  wahi jagah, jahan pehle bhi tha.
- Wapas sab theek karna ho to Windows ka apna **Task Manager → Startup** tab
  me `Jarvis` ko disable kar do.
- Project folder **move** kiya ho to `install` dobara chalao. Purana path
  registry me reh jaata hai aur login par app chup-chaap nahi chalta —
  `--doctor` ise `WARN` dikhata hai.

### Raasta B — purana tarika (browser me)

```powershell
cd D:\Projects\jarvis\jarvis2.0
.\.venv\Scripts\python.exe main.py
```

Browser me kholo: **http://localhost:8000**

Band karne ke liye terminal me `Ctrl + C`.

Is raaste me bhi **"Hlo Jarvis" chalta hai** (wake worker isi process me
shuru hota hai). Dono raaste ek hi lock use karte hain, is liye ek saath do
JARVIS nahi chal sakte.

### Kuch kaam nahi kar raha? Pehle ye chalao

```powershell
.\.venv\Scripts\python.exe main.py --doctor
```

Ek-ek cheez batata hai: jawab dene wali key, sunne wala (STT), "Hlo Jarvis"
wake word, mic, port, auto-start, tools. Har line `OK` / `WARN` / `FAIL` hai
aur aakhir me saaf natija — kya theek karna hai. Ye kuch shuru nahi karta, is
liye app chalte hue bhi chala sakte ho.

---

## 3. Test

Saare 89 suites ek loop me:

```powershell
cd D:\Projects\jarvis\jarvis2.0
$fail = @()
Get-ChildItem tests\test_*.py | ForEach-Object {
  .\.venv\Scripts\python.exe $_.FullName
  if ($LASTEXITCODE -ne 0) { $fail += $_.Name }
}
if ($fail) { "FAILED: $($fail -join ', ')" } else { "SUITE GREEN" }
```

Ek-ek karke bhi: `.\.venv\Scripts\python.exe tests\test_gatekeeper.py`

Har suite ka detail (kya check karta hai, naya test kaise likhein) →
**[TESTS.md](TESTS.md)**. Test me real API call nahi hota aur koi khatarna
command nahi chalti — key ki zarurat nahi.


---

## Suraksha (sirf local)

Ye app bahar se bilkul band hai:

1. **Sirf 127.0.0.1 par suna** — `0.0.0.0` par server chalu hi nahi hoga
   (`main.py` me guard hai).
2. **Origin check** — sirf `http://localhost:8000` aur `http://127.0.0.1:8000` se aane
   wale request chalenge. Koi doosri website (`https://evil.com`) se kuch nahi hoga.
3. **Host header check** — sirf `localhost:8000` / `127.0.0.1:8000`. Isse koi fake
   domain (DNS rebinding) app ko apna nahi dikha sakta.
4. **Token** — server har baar start hone par ek naya random token banata hai.
   Token page ke `<meta name="jarvis-token">` me daal diya jaata hai, aur UI har request
   ke saath bhejta hai. Token galat ya missing ho to request 401 ho jaati hai.
5. **CORS band** — koi `access-control-allow-origin` header nahi jaata.
6. **CSP header** — page par sirf apna hi code chal sakta hai (inline script band).
7. **PC tools** — har tool gatekeeper se guzarta hai; badlav-wale kaam bina ALLOW ke
   nahi hote, aur `.env`/key files hamesha BLOCKED. Details [TOOLS.md](TOOLS.md) me.

Sabse aasan: **token har restart par badal jaata hai**, isliye server band karke dobara
chalao aur page dobara kholo — token apne aap refresh ho jaayega.

### Command line se test karna ho

```powershell
cd D:\Projects\jarvis\jarvis2.0
$page = Invoke-WebRequest http://localhost:8000 -UseBasicParsing
$token = [regex]::Match($page.Content, 'name="jarvis-token" content="([^"]+)"').Groups[1].Value
Invoke-RestMethod http://localhost:8000/chat -Method Post `
  -Headers @{ Origin = "http://localhost:8000"; "x-jarvis-token" = $token } `
  -ContentType "application/json" -Body '{"text":"Jarvis, hi"}'
```

---

## Kaise use karna hai

Command box me likho aur **SEND** dabao (ya Enter).

Assistant ek hi hai — **Jarvis**. Mode badalne ke liye kuch likhna nahi padta
(Prabh mode dormant hai aur jaldi hatega — upar padho).

Beeche me gol orb aur uske neeche status dikhta hai: `IDLE` -> `THINKING` -> `SPEAKING` -> `IDLE`.
Dayin taraf poori baat-chit rehti hai, neeche **ACTIVITY** box me har tool ka hisaab.

**Jarvis aapko pehchanta hai.** Naam, sheher, pasand — jo aap bol kar batate ho
("yaad rakho mujhe chai pasand hai") wo `data/profile.json` me rehta hai aur
agle jawab me khud use hota hai. Bhulaana ho to "bhula do chai" bolo. Detail
`TOOLS.md` ke "Personal memory" section me.

**Reminder bolta hai:** "remind me in 10 minutes to call home" — time aane par
Jarvis khud awaaz me yaad dilata hai (app chalu hona chahiye).

---

## Kaun si file kya karti hai

| File | Kaam |
|---|---|
| `main.py` | Server chalu karta hai |
| `config.py` | `.env`, settings, tool risk, allowed folders, blocked patterns |
| `config_brain.py`, `config_voice.py` | Brain aur voice constants (`config.py` re-export karta hai) |
| `config_desktop.py` | Desktop constants: tray rang, HUD size, crash backoff, exit code, mic/lock helpers, `HUD_HOTKEY` |
| `log_setup.py` | `logs/jarvis.log` banata hai |
| `core/events.py`, `core/modes.py` | Chat events + naam se mode, persona, label |
| `core/engine.py` | Poora chat flow + tool loop (**sirf** `run_tool` raasta) |
| `brain/pool.py`, `pool_config.py` | Do-tier brain pool + uski order (pool hi Groq/Gemini/NVIDIA/OpenRouter chala hai) |
| `brain/openai_pool.py`, `brain/limiter.py` | OpenAI-compatible calls + NVIDIA 30/min limiter |
| `brain/health.py`, `health_words.py` | Cooldown/lock + error-text categories |
| `brain/probe.py`, `checkup.py` | Manual strict-JSON probe + startup `/models` check |
| `brain/prompt.py` | Persona + tool JSON rules + strict parser |
| `gatekeeper/keeper.py` | Har tool ka faisla + card ka intezaar |
| `gatekeeper/rules.py`, `patterns.py`, `paths.py` | Risk, khatarna command regex, traversal/8.3/junction jaanch |
| `gatekeeper/approvals.py`, `limiter.py`, `audit.py` | Card hash, kill switch, masked log |
| `tools/*.py` | 10 tools ka asal kaam |
| `config_hud.py` | HUD ke rang, weather ki jagah/timeout, stats interval, 6 quick button ki list |
| `server/app.py` | `POST /chat` + `WebSocket /ws` + CSP + `GET /` |
| `server/security.py` | Host → Origin → token (aur same-origin GET ka proof) |
| `server/state.py` | Poore server ka **ek** shared Engine |
| `server/brain_routes.py` | `GET /brain/status` (pool ka live haal) |
| `server/hud_routes.py` | `GET /hud/stats`, `GET /hud/weather`, `POST /hud/quick` |
| `server/ws_routes.py` | `/ws` chat + har 2s `"stats"` WebSocket event |
| `server/hub.py`, `drain.py` | Thread-safe event hub + async engine generator |
| `core/sysstats.py` | `psutil` se CPU/RAM/battery/disk/network |
| `server/weather.py` | Open-Meteo fetch + 15 minute cache |
| `server/tool_routes.py`, `server/voice_routes.py` | `/tool/confirm`, `/tools/*`, `POST /stt`, `POST /tts` |
| `voice/*.py` | STT/TTS providers (details [VOICE.md](VOICE.md)) |
| `ui/index.html`, `ui/app.js` | 3-column HUD markup + chat/WebSocket glue |
| `ui/hud_base.css`, `hud_left.css`, `hud_center.css`, `hud_right.css`, `hud_bottom.css` | HUD ka look, har file ka ek kaam |
| `ui/hud_panel.css` | Panel ka common border + tab (`.ptab`) |
| `ui/hud_clock.js`, `hud_stats.js` | Chronometer + CPU/RAM/battery gauge, disk/network bar |
| `ui/hud_orb.js` | Orb SVG, tick-marks, state animation |
| `ui/hud_weather.js` | Weather panel (sirf `/hud/weather` se) |
| `ui/hud_activity.js`, `hud_status.js` | ACTIVITY list + SYSTEM/provider pill |
| `ui/hud_quick.js` | 6 quick button (TOOLS OFF par disabled) |
| `ui/hud_desktop.js` | Top bar ka DESKTOP pill (mic + wake ka haalat, sirf dikhata hai) |
| `ui/tools.js`, `ui/recorder.js`, `ui/speaker.js` | Confirm card, ACTIVITY jodi, mic record, audio play |
| `ui/fonts/` | Local woff2 fonts + OFL license |
| `personas/jarvis.txt`, `personas/prabh.txt` | Dono ka character |
| `desktop/launcher.py` | Supervisor: app crash ho to dobara (pehle `start_jarvis.bat` se chalta hai) |
| `desktop/app.py` | Jarvis app: server thread + tray + HUD + mic permission + lock watcher |
| `desktop/tray.py`, `trayicon.py` | Tray menu (Mute / Open HUD / TOOLS / Restart / Quit) + rang se bana icon |
| `desktop/hud_window.py` | Edge `--app` me HUD window (apna profile, 1200x720) |
| `desktop/hotkey.py` | Global hotkey (default Ctrl+Alt+S) — sirf `ctypes`, koi naya package nahi |
| `desktop/open_hud.py` | Shortcut **aur** hotkey dono ka ek hi raasta: server zinda hai to HUD khulo |
| `desktop/shortcut.py`, `hud_shortcut.ps1` | Desktop ka "Jarvis HUD" `.lnk` banao / hatao (`WScript.Shell`) |
| `desktop/single.py` | Ek hi instance (doosra `"already running"` band ho jaata hai) |
| `desktop/autostart.py` | Login par khud chalna (`HKCU\...\Run`, `pythonw desktop\launcher.py`) |
| `desktop/launcher.py`, `playback.py`, `playback_cli.py` | Supervisor (crash par restart) + speaker (TTS bytes → sounddevice) |
| `desktop/state.py`, `micperm.py`, `lockwatch.py` | Ek shared haalat, Windows mic permission check, lock ka pata |
| `wake/worker.py`, `session.py` | Wake word: module ka ek raasta + uska asli loop (thread, cooldown, mute) |
| `wake/audio.py`, `detect.py`, `phrase.py`, `model.py` | Mic + energy VAD, Vosk recognizer, "jarvis" pakadna, model load |
| `config_wake.py` | Wake/VAD/command-window constants (`config.py` se re-export) |

---

## Error kahan dekhein?

Sab kuch `logs/jarvis.log` me likha jaata hai — har brain call ka timing bhi (`pool: T1 groq 1402ms | total 1451ms`). Har tool ka hisaab `logs/actions.log` me.

```powershell
Get-Content D:\Projects\jarvis\jarvis2.0\logs\jarvis.log -Tail 20
Get-Content D:\Projects\jarvis\jarvis2.0\logs\actions.log -Tail 20
```

Agar `start_jarvis.bat` se chalaya tha aur app khud band ho gayi, to supervisor ka
alag log hai:

```powershell
Get-Content D:\Projects\jarvis\jarvis2.0\logs\desktop.out -Tail 30
```

Isme teen numbers matlab rakhte hain: `0` = saaf band (Quit), `1` = crash,
`3` = app pehle se chal raha hai. 5 crash ke baad supervisor khud ruk jaata hai.

Agar browser me sirf "Abhi koi brain jawab nahi de paya" dikh raha hai, to `.env` me key
sahi hai ya nahi check karo — live check aur pool detail [BRAIN.md](BRAIN.md) me hai.
