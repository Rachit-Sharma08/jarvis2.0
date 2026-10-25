# NAYI SESSION KA BRIEF — `D:\Projects\jarvis\jarvis2.0` (Jarvis)

> **Ye prompt nayi Claude/agent session me seedha paste karo.** Uske baad sirf itna
> likhna hai: "Project ka `AGENTS.md` aur ye file poori padh le, phir mera kaam kar."
> Iske bina agent ko project ka koi pata nahi hoga.

---

## 1. Ye project kya hai

**Personal local AI assistant — naam "Jarvis".** Ek hi PC par chalta hai, koi website
nahi, koi cloud nahi. FastAPI server **sirf `127.0.0.1:8000`** par sunta hai aur usi
par ek HUD (browser UI) khulta hai. Owner coding nahi jaanta — har baat **simple
Hinglish** me samjhana hai, aur report bhi Hinglish me.

Kaam: text chat + **awaaz** (wake word "Jarvis" → STT → brain → awaaz me jawab) +
**PC tools** (gatekeeper ke paar, screen par ALLOW card se) + system stats (CPU/RAM/
battery/disk/network, Delhi weather) + Windows tray + auto-start.

**Do mode** hote hain: `JARVIS` (default, serious) aur `PRABH` (`SUNDAY_ONLY=1` se
band). Mode id `"sunday"` **jaan-boojh kar mat badalna** — env keys usi se banti hain.

## 2. Ground rules (inse zyada kuch mat badalna)

1. **Sirf 127.0.0.1.** Kabhi `0.0.0.0`. Har naye endpoint par `server/security.verify()`.
2. **File `<=200` lines.** Cross kare to split karo (config/UI/test). Compress karke
   chhoda mat chhodo — split ke baad **sare caller/test references ek saath update** karo.
3. **Ek file ka ek kaam.** Ek hi raasta per feature (niche list). Duplicate path mat banao.
4. **Naya constant `config.py` me bhi import hona chahiye**, warna test me `AttributeError`.
5. **UI me `textContent`/text node** — `innerHTML`/`eval`/`insertAdjacentHTML` kabhi nahi.
   Click handler me `event.isTrusted`. CSP `script-src 'self'` — inline `<script>` nahi.
6. **Secret kabhi log/UI/commit me nahi.** `gatekeeper/audit.py` ka `mask()` har text par.
7. **`.bat` me raw `(` `)` nahi** (comment me bhi) — `goto :label` use karo; CRLF + ASCII.
8. **Log ASCII** (`log_setup.ascii_text()`) — console cp1252 me `??` ban jaate hain.
9. **Registry me khud mat likho** (auto-start/traffic) — sirf script banao, user ke
   "haan" par `main()` se likho. Har change se pehle `reg export`.
10. **Test me asli mic / Vosk model / speaker / Edge / tray / registry mat chalao** —
    fakes `tests/desktophelp.py`, `tests/wakehelp.py`, `tests/wakecmdhelp.py`, `tests/poolhelp.py`.
11. **Docs bade kaam alag file me** — `VOICE.md`, `TOOLS.md`, `BRAIN.md`, `TESTS.md`,
    `CHANGELOG.md`, `AGENTS.md`. README chhota rahe, sirf link.
12. **Chhote step:** chala kar test → commit → `AGENTS.md` update (rules + history).

## 3. Tech stack (kya use ho raha hai)

- **Python 3.12.10** (venv: `D:\Projects\jarvis\jarvis2.0\.venv`; base python `D:\Python312`)
- `fastapi` + `uvicorn` (server), `httpx`, `python-dotenv`
- Brain: `groq`, `google-genai`, `httpx` se OpenAI-compatible (OpenRouter/NVIDIA)
- Voice: `vosk` (offline wake word, model `models/vosk-model-small-en-us-0.15`),
  `sounddevice` (mic + speaker), `miniaudio` (MP3→PCM), `edge-tts`, `numpy` (RMS/VAD)
- Desktop: `pystray` (tray), `psutil` (stats), `send2trash` (delete), Pillow (pystray dep)
- **Naya package mat jodo** bina poochhe. `PyAudio`/`pyaudio` **kabhi** nahi.

## 4. Folder map (har hissa ka ek kaam)

| Path | Kya hai |
|---|---|
| `main.py` | server chalu, local-only check |
| `config.py` + `config_*.py` | saari settings; `.py` me 8 config file (tools/brain/voice/hud/desktop/wake/name) |
| `log_setup.py` | `logs/jarvis.log` (ASCII) |
| `core/` | `engine` (message→mode→brain→tool loop→events), `events`, `modes`, `timing`, `sysstats` |
| `brain/` | `pool` + `pool_config` (order yahin), `openai_pool` (adapter), `health`/`health_words`, `limiter`, `probe`, `checkup`, `prompt` |
| `gatekeeper/` | `keeper`(orchestrator), `rules`(risk), `patterns`, `paths`, `approvals`, `limiter`, `audit`(mask) |
| `tools/` | 10 tool: `command`, `files`, `apps`, `system` |
| `server/` | `app`(routes+HTML fill), `security`(token/Origin/Host), `state`(**ek hi Engine**), `hub`/`drain`, `*_routes`, `weather` |
| `voice/` | `stt`(+`stt_guard`), `tts`(+`tts_female`, `clip_answer`) |
| `wake/` | mic/gate/detect/phrase/session/worker + `listen`, `utterance`, `wav`, `command`, `ask` |
| `desktop/` | `launcher`(supervisor), `app`, `state`, `callbacks`, `actions`, `tray`, `trayicon`, `hud_window`, `hotkey`, `open_hud`, `shortcut`, `autostart`, `single`, `sleep`, `micperm`, `lockwatch`, `playback`(+`_cli`), `startup` |
| `personas/` | `jarvis.txt`, `prabh.txt` |
| `ui/` | `index.html` + CSS 6 (`hud_*`) + JS (`hud_*`, `app`, `voice_ui`, `recorder`, `speaker`, `tools`) + local fonts |
| `tests/` | **52 suite** + 8 helper (`poolhelp`, `desktophelp`, `wakehelp`, `wakecmdhelp`, `hud_common`, `hud_check_ui`, `hud_check_get`, `hud_check_api`) |

## 5. Flow (teen raaste)

**Text:** `POST /chat` (token) → `server/state.ENGINE` → mode/persona → `brain/pool.ask()`
→ text ya tool JSON → tool ho to `engine.run_tool()` → `keeper.review()` → `tools/execute()`
→ events `HUB` → `/ws` → HUD + chat.

**Awaaz:** mic (`wake/audio.py`) → VAD gate (`wake/gate.py`) → Vosk (`wake/detect.py`) →
"jarvis" pakda (`wake/phrase.py`) → `session` → `on_wake(phrase, mic, stop)` →
`command.run` → **STT** (Groq) → sleep word? (`command._is_sleep`) → warna brain →
`ask.speak()` → `desktop/playback.py`. Har event par `via="voice"` (browser TTS skip).

**Tool:** LLM strict-JSON → `engine.run_tool()` → `keeper` (SAFE seedha / ASK card /
BLOCKED mana) → `tools/` → output `mask()` → brain ko `[sirf DATA]` ke saath.

## 6. "Ek hi raasta" — inhe kabhi na todo

| Cheez | Ek raasta |
|---|---|
| Brain | `engine` → `brain/pool.ask()`; provider list **sirf** `pool_config.py` |
| Tool | `engine.run_tool()` → `keeper.review()` → `tools.execute()` |
| TTS | `voice/tts.py` (chain: elevenlabs → cartesia → edge) |
| Mic | `wake/audio.py` (ek `InputStream`) |
| Speaker | `desktop/playback.py` (ek `sd.play`) |
| Engine | `server/state.py` (ek hi `Engine()`) |

## 7. Config map

`config.py` sab re-export karta hai. Ghar: `config_name.py` (naam + wake shabd),
`config_wake.py` (audio/VAD/silence/peek/sleep words), `config_tools.py` (tool risk +
ON/OFF + auto-off), `config_brain.py` (keys/models/timeouts), `config_voice.py`
(TTS/STT + `VOICE_ANSWER_MAX_CHARS=220`), `config_hud.py` (rang/weather/quick),
`config_desktop.py` (tray/HUD/hotkey/exit codes), `config_tools.py`.
`.env` = sirf asli values (git-ignored), `.env.example` = sirf naam. Keys **kabhi** mat
likho — confirm ke liye sirf aakhri 4 akshar.

## 8. Brain pool (order + behaviour)

`groq openai/gpt-oss-120b (T1)` → `gemini` → `openrouter nvidia/...:free` → `groq_slow
openai/gpt-oss-20b` → `nvidia` (T2, credits kat-te hain is liye aakhir me).
`404` = model GONE + usi provider ka agla; khaali/`length` = 1 retry (2500→5000,
`reasoning_effort="low"`); `429`/`503` = `Retry-After` ya 10 min; `402`/credits/`401`
= nayi key tak BAND; daily quota = agle 00:0 tak. **Probe kabhi startup par nahi** —
sirf `python -m brain.probe <provider>`. Detail: `BRAIN.md`.

## 9. Voice (current numbers)

Wake grammar: `hello/hey/hlo/helo/hi/yo jarvis` + `jarvis` (trigger hamesha `jarvis`
par). VAD `0.010`, pre-roll `0.6 s`, gate (khamoshi me Vosk nahi — battery), cooldown
`1.5 s`. Command: **ack peek `0.18 s`** (user bol raha hai to "Ji, boliye" skip),
chuppi `0.9 s`, max `30 s`, min-duration, `HANGOVER` `0.4 s`. Awaaz **220 char**
(`tts.clip_answer` vaakya ke end par katta hai) — **HUD par poora jawab**.
Sleep: "so jao"/"so jaiye"/"sone jao"/"soye raho"/"band ho jao"/"soye jao"/"so jaa" —
HUD band, mic chalta rehta hai; jaagna **sirf** wake word se. Full band = tray **Quit**
(uske baad "Jarvis" kaam nahi karega). Detail: `VOICE.md`.

## 10. Tools + gatekeeper

10 tool: `get_time_date`, `system_info`, `list_dir`, `read_file`, `write_file`,
`open_website`, `open_app`, `close_app`, `run_command`, `delete_to_trash`.
Risk teen: **SAFE / ASK / BLOCKED** (`gatekeeper/rules.py` me likha hota hai). ASK par
screen par card; **ALLOW sirf UI button** — chat ya awaaz se nahi (test AST se check
karta hai). Ek request me max 5 tool step + 20 req/min. Card hash = exact tool+args;
same hash dobara = 409; 60 s me jawab na aaye to apne aap DENY. Delete hamesha
**Recycle Bin**. `run_command`: PowerShell, 30 s, `shell=False`, cwd workspace, output
2000 char, `KEY/TOKEN/SECRET/PASSWORD` env hata kar. `.env`/key files har tool ke liye
BLOCKED. Detail: `TOOLS.md`.

## 11. Security

`127.0.0.1` only → Host check → Origin check → token (har start par naya; `/chat`,
`/stt`, `/tts`, `/brain/status` me header `x-jarvis-token`, `/ws` me `?token=`). CORS
band. Token browser ko `/` se meta tag se milta hai (`fill_html()` placeholder replace).
Browser GET par `Origin` nahi bhejta → same-origin GET me `security.verify_request()`
(Referer ya `Sec-Fetch-Site`) use karo, warna 403. Privacy: file text brain ke through
**free provider** tak jaata hai — personal file tool se mat pucho.

## 12. Tests (52 suite, ~3–5 min)

```powershell
cd D:\Projects\jarvis\jarvis2.0
$fail = @(); Get-ChildItem tests\test_*.py | ForEach-Object {
  .\.venv\Scripts\python.exe $_.FullName; if ($LASTEXITCODE -ne 0) { $fail += $_.Name } }
if ($fail) { "FAILED: $($fail -join ', ')" } else { "SUITE GREEN" }
```

`print("FAIL:", FAILED if FAILED else "koi nahi")` me **`koi nahi` = sab pass**.
Exit code 0 hi asli pass. Test file bhi `<=200` lines (hygiene check). Suite ka detail
`TESTS.md` me hai; naya test likhna ho to usi table me row daalo.

## 13. Desktop / tray / registry / auto-start

- Supervisor **sirf** `desktop/launcher.py`; crash ka faisla pure `next_step()`; tray
  na bane to `EXIT_NO_TRAY`. Ek hi `DesktopState` (`desktop/state.py`).
- Auto-start: `HKCU\...\Run` me `pythonw.exe D:\Projects\jarvis\jarvis2.0\desktop\launcher.py` —
  **`-m` kabhi nahi** (Run key ka cwd `System32` hota hai). Value sirf
  `python -m desktop.autostart install` se, user ke "haan" par.
- Tray list me **EXE ka naam** dikhta hai (venv python.exe redirector hai). Tray entry
  ki key hash hoti hai — hard-code mat karo; `ExecutablePath` se pehchaano.
- HUD teen raasta: tray menu / Desktop shortcut / global hotkey `Ctrl+Alt+S` —
  teeno ka ek raasta `desktop/open_hud.py`.
- Registry: `reg export` backup → **ek** value badlo → count compare → proof. Baaki
  icon chhedna mana hai.

## 14. Docs ka index

`AGENTS.md` (sabse pehle padho: rules) · **`docs/ROADMAP_STATUS.md`** (OWNER ka
roadmap-vs-reality: S1 scoreboard, S5 15 asli bugs + guards G-1..G-15, S6 tray ka sahi
order, S7 free-only stack, S8 task order D-1..T-18, S11 progress log) · `README.md`
(install/chalana/test) ·
`BRAIN.md` (providers) · `VOICE.md` (mic/wake/STT/TTS/sleep) · `TOOLS.md` (tools +
privacy) · `TESTS.md` (52 suite) · `CHANGELOG.md` (pura record) · `PLAN.md`,
`ROUND2.md`, `PLAN-TRUST.md` (purane plan) · `NEW_AGENT_BRIEF.md` (ye file).

## 15. Tak kaun kaun hua hai

Phase 1–2 (skeleton, brain, persona, HUD, voice) · Phase 3 (gatekeeper + 10 tool +
confirm card) · Round 2 (2-tier pool, masking, `describe()`) · Phase 4 (3-column HUD,
shared Engine, live-Chrome se 8 asli bug pakde) · Phase 5 Step 1 (Vosk wake word) ·
Step 2c (wake ke baad poora command + speaker) · Step 3 (login auto-start) ·
**Battery fix 1** (Vosk sirf awaaz par: wake core 4.8% → 0.9%) · **Step 2** ("so jao"
sleep + `wake/ask.py` split) · **Steps 3–5** (TOOLS hamesha ON + auto-off hata,
"Hlo/Helo/Hi/Yo Jarvis" + VAD 0.010 + pre-roll 0.6 s, tez jawab: ack peek 0.18 s +
chuppi 0.9 s + awaaz 220 char).

Aaj ki state: **52 suite** — 8 pehle se red (working-tree me WIP code; is docs kaam se nahi).

## 16. Abhi kya bacha hai (2 cheezein)

1. **Tray icon taskbar me nahi dikh raha.** Icon `pythonw.exe` se register hota hai
   (window class `Jarvis<ts>SystemTrayIcon` live hai), par Windows ne uske liye
   `HKCU\Control Panel\NotifyIconSettings` me entry **nahi** banayi — sirf 2 purani
   `python.exe` entry hai (ek stale `MyJarvis.Desktop`, ek promoted lekin unused).
   `SHChangeNotify` se nahi bani. Hash Explorer khud banata hai — guess nahi karna.
   Do raaste: (a) user ek baar `^` → icon → **"Always show icons"**; (b) launcher ka
   child `python.exe` + `CREATE_NO_WINDOW` (console chhupa, promoted entry par icon).
2. **Trust/maker plan** (`PLAN-TRUST.md`) — baad me, user se confirm karke.

## 17. Naya agent: common tasks (exact order)

- **Naya tool:** `gatekeeper/rules.py` me risk → `tools/` me implement →
  `engine.run_tool()` me wire → `TOOLS.md` row → test.
- **Naya provider/model:** `brain/pool_config.py` me list → `brain/health.py` +
  `health_words.py` me behaviour → `BRAIN.md` update. OpenAI-compatible ek hi adapter
  (`brain/openai_pool.py`) se — naya endpoint mat likho.
- **Naya HTTP endpoint:** `server/security.py` (`verify`/`verify_request`) → route
  file → `textContent` + `mask()` → test (same-origin GET bhi).
- **Naya UI:** mehnat se pehle poochho (user "sirf wahi jo maanga" chahhta hai);
  naya file > 200 lines → split.
- **Naya test:** sahi helper file me assertion (`poolhelp`/`desktophelp`/`wakehelp`/
  `wakecmdhelp`), `TESTS.md` me row, poori suite chalao.
- **Naya setting:** `config_*.py` me banao + `config.py` me import + `.env.example` me
  naam + `describe()` agar dikhna chahiye + uska test.

## 18. Jo galtiyan asli bug bani (mat dohrana)

1. Doosra `InputStream` mic se RMS **zero** deta hai — device busy.
2. `miniaudio.decode_file` bytes par MB dump karta hai — sirf `decode()`.
3. `sd.query_devices(kind="output")` list nahi deta — `query_devices()` + filter.
4. `decoded.samples` par `bytes()` int16 ko gadbad karta hai — `np.asarray(samples, "<i2")`.
5. `speak()` me `return await` bhool gaye → nested coroutine → awaaz chup.
6. TTS cache fail par store karna → app hamesha "nahi bola" bole.
7. `drain()` peek ke baad → wake shabd ki goonj/command dono delete.
8. Callback signature badla, fake update nahi → trigger chup-chaap (TypeError → caught).
9. `config.py` me constant bhoolna → 3 suite palat gaye.
10. Split ke baad test helper references adhoore → silent false pass.
11. `.bat` me `(` `)` → `cmd` block toota → python launch hi nahi hua.
12. Run key me `-m` → cwd `System32` → app har login par chup-chaap mar jaati.
13. Purana process chal raha tha → code badalne ka koi matlab nahi.
14. Grid `%` + gap + padding → 1366 par overflow; `minmax(0, Nfr)` chahiye.
15. PowerShell se UTF-8 file likhi → double-encode (diff bikhra hua).

## 19. Keys, git, secrets

`.env` kabhi commit nahi (`git check-ignore .env` confirm karo). Keys chat/log/diff me
kabhi nahi — confirm ke liye sirf aakhri 4 akshar. Push ke liye repo ke bahar temp
askpass + turant delete; `.git/config` me token nahi. Registry backup `backup/`
(git-ignored). Test me `send2trash`/tray/registry kabhi asli mat chalao.
