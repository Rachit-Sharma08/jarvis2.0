# CLAUDE.md — Jarvis (Prabh) ka handoff

Ye file **sirf direction** deti hai — haalaat, chalti cheezein, pakkaurey aur roadmap.
Detail ke liye: `AGENTS.md` (poore niyam) · `CHANGELOG.md` (kaam ka record) ·
`PLAN.md` (Phase 5 ka plan) · `TESTS.md` / `BRAIN.md` / `TOOLS.md` / `VOICE.md`.

> Owner coding nahi jaanta. Har baat **simple Hinglish** me samjhana hai.

---

## 1. Ye project kya hai

`D:\prabh` me ek **local personal app** hai — sirf usi PC par (`127.0.0.1`), web app
nahi. Naam **Jarvis** (pehle "Prabh" tha, wo mode ab band hai). Ek brain hai
(sirf **free** providers), awaaz hai, aur 10 PC tools hain jinse Jarvis computer par
kaam kar sakta hai.

## 2. Ab ka haal (3 Oct 2026)

- Git **clean**, commit `07161c0` (GitHub par push ho chuka hai).
- **40 test suite green** (`SUITE GREEN`). Sab standalone, koi real API call nahi.
- App chalta hai: `GET http://127.0.0.1:8000/` = 200, tray + HUD live.
- Phase 5 **Step 1 (Vosk wake word)**, **Step 2a** (command capture + WAV),
  **Step 2b** (speaker `desktop/playback.py`) aur **Step 2c** (poora command:
  STT + brain + jawab ki awaaz) — teeno 3 Oct tak complete.
- Sab production file **200 line se chhoti ya barabar** (`test_desktop.py` ka hygiene
  check ye khud har file par lagata hai, test file me bhi).

## 3. Chalane ka tareeka

| Kya | Kaise |
|---|---|
| App chalao | `start_prabh.bat` par double-click (supervisor crash par dobara chalata hai) |
| HUD kholo | tray menu · Desktop ka `Jarvis HUD.lnk` · **Ctrl+Alt+S** |
| Browser me | `http://127.0.0.1:8000` |
| Band karo | tray me **Quit** (window band karna app nahi rokta) |

> ⚠️ **HUD hamesha `http://127.0.0.1:8000`** — `localhost:8000` par kaam nahi karta.
> Browser GET par `Origin` header nahi bhejta, security `127.0.0.1` maangti hai.
> (Phase 3/4 me isi ki wajah se kuch features chhupi hui thi.)

## 4. Test kaise chalate hain

```powershell
cd D:\prabh
$fail = @()
Get-ChildItem tests\test_*.py | ForEach-Object {
  .\.venv\Scripts\python.exe $_.FullName
  if ($LASTEXITCODE -ne 0) { $fail += $_.Name }
}
if ($fail) { "FAILED: $($fail -join ', ')" } else { "SUITE GREEN" }
```

- Exit code **0** hi asli pass hai. `print("FAIL: koi nahi")` matlab **sab pass**.
- 3–5 min leti hai (40 suite) — `Start-Job` + result file wala tarika `TESTS.md` me
  hai. Har naye shell me `Start-Job` mar jaata hai, is liye **detached** process chalao
  (`Start-Process powershell -File <script> -WindowStyle Hidden`).

## 5. Jarvis ABHI ye kar sakta hai

**Baat-cheet**
- Text: HUD ya browser me likho → brain sochta hai → jawab.
- Awaaz (browser): mic dabao → bolo → wahi brain → **female awaaz** me jawab
  (TTS chain: ElevenLabs → Cartesia (abhi skip) → Edge Swara).
- Awaaz (Python, Step 1-2): mic hamesha sunta hai, **"Jarvis"** bolte hi HUD khulta hai
  (100% offline Vosk). TTS ki awaaz `desktop/playback.py` se bajti hai — app ke
  bina bhi: `python -m desktop.playback --say "Ji, boliye"`.

**Brain — 5 free provider, ye order (NVIDIA aakhir me, credits kat-te hain):**
Groq (T1) → Gemini → OpenRouter `:free` → Groq 20b (slow) → NVIDIA (T2).
Model ke naam `config_brain.py` / `.env` se aate hain — `brain/pool_config.py`
me provider ki list badlo, engine me kabhi hard-code mat likho.

**HUD (3 column)**
- Left: clock + chronometer, weather (Delhi, 15 min cache)
- Center: orb + chat + ACTIVITY
- Right: CPU / RAM / battery gauge, disk / network bar
- Top: SYSTEM pill (live provider) · DESKTOP pill (mic + wake)
- Bottom: **6 quick button** — BROWSER · YOUTUBE · WHATSAPP · MUSIC · FILES · SCAN

**Tools (10) — teen hi risk**
- **SAFE** (seedha chalta hai): `get_time_date`, `system_info`, `list_dir`,
  `read_file` (20 KB tak), `open_website`, `open_app` (list wale)
- **ASK** (screen par card → tumhe **ALLOW/DENY**): `write_file`, `run_command`
  (PowerShell, 30 sec), `delete_to_trash` (**Recycle Bin**), `close_app`, aur
  allowed folder ke bahar kuch bhi
- **BLOCKED** (hamesha mana): `.env`/key files, disk format, registry delete,
  `del C:\`, firewall band, `iwr|iex`
- Limits: 1 request me **max 5 step**, 20 req/min, card ka jawab 60 sec me nahi
  aaya to apne aap DENY, aur 30 min baad TOOLS apne aap OFF.

**Tray**: status line · Mic Mute · Open HUD · TOOLS · Restart · Quit

## 6. Jarvis ABHI ye NAHI kar sakta (galat mat samjho)

- ✅ **Wake ke baad poora command** — `Step 2c` (3 Oct) poora hai: "Jarvis" →
  "Ji, boliye" → mic se command → Groq STT → brain → HUD par jawab + awaaz.
  (2 Oct ki ye line ab purani hai.)
- ❌ **Awaaz se tool nahi chalta** — tool sirf chat se. Aur ALLOW hamesha screen par
  button se hoga, awaaz se kabhi nahi.
- ❌ **Auto-start nahi** — Windows login par khud nahi chalta (Step 3 me aayega).
- ❌ **Prabh mode band** — code maujood hai, `PRABH_SUNDAY_ONLY=1` se off.
- ❌ Cartesia ki female voice id nahi mili → wo provider skip ho jaati hai.
- ❌ **Cartesia voice id** (`CARTESIA_VOICE_*`) abhi khaali hai.

## 7. Pakkaurey (sabse zaroori)

1. **Ek hi Engine** — `server/state.py`. Kahin naya `Engine()` mat banao.
2. **Ek hi tool raasta** — `engine.run_tool()` → `keeper.review()` → `tools.execute()`.
3. **Ek hi brain raasta** — `brain/pool.py`. Order sirf `brain/pool_config.py`.
4. **Ek hi DesktopState** — `desktop/state.py` ka `STATE`.
5. **HUD ke 3 raasta ek hi function** — `desktop/open_hud.py`.
6. **Naya endpoint** → `server/security.py` ka `verify()` (Host → Origin → Token).
   Grid layout me `%` nahi, `minmax(0, Nfr)`.
7. **UI me sirf `textContent`** — `innerHTML`/`eval`/`onclick` kabhi nahi.
8. **Naya tool** → pehle `gatekeeper/rules.py` me risk, phir `tools/`, phir engine.
9. **Naya output** (card/activity/log) → `textContent` **aur** `audit.mask()` dono.
10. **File 200 se badi** → split karo. Ek file ka ek hi kaam.
11. **Keys** `.env` me — kabhi code/log/commit/README me nahi. Naya provider ka
    order + `brain/health.py` me behaviour.
12. **Test me asli Desktop/tray/Edge/registry/`RegisterHotKey`/mic/speaker kabhi mat
    chalao** — fakes `tests/desktophelp.py` / `tests/wakehelp.py` me hain.
13. **`.lnk` banana/hataana test me nahi** — `shortcut.command()` ki list check karo.
14. **Windows tray list exe ka naam dikhati hai**, app ka nahi. Registry ka key
    hash hota hai — hard-code mat karo, har change se pehle `reg export`.
15. **Speaker ka ek raasta `desktop/playback.py`** — naya `sd.play` kahin aur nahi.
    `miniaudio.decode_file` bytes par MB ka dump karta hai, sirf `decode()` chalao.
    `sd.query_devices(kind="output")` list nahi deta.
16. **Test file 200+ ho to split karo**, aur helper **module level** par rakh —
    warna doosre function me `NameError` se chup-chaap fail ho jaata hai.

Poora niyam → **`AGENTS.md`** (section 3.1–3.4, 8, 8.1, 8.2).

## 8. Aage ka roadmap

| Step | Kya | Halaat |
|---|---|---|
| **1** | Vosk wake word — mic hamesha sunta hai, "Jarvis" par HUD | **ho gaya** (2 Oct) |
| **2a** | Command capture + WAV (`wake/utterance.py`, `wake/wav.py`) | **ho gaya** (3 Oct) |
| **2b** | Speaker — TTS bytes bajana (`desktop/playback.py`) | **ho gaya** (3 Oct) |
| **2c** | Glue: "Ji, boliye" → mic drain + warm-up → capture → Groq STT → `ENGINE` → HUD events → awaaz me jawab | **agla kaam** |
| 3 | Auto-start (HKCU Run) | **sirf jab owner "haan" bole** |
| — | Face / trust / learn / maker | aage, decided nahi |

**Step 2c me dhyan rakhne ki baat:** `Session._fire()` `on_wake` ko wake thread par
synchronously call karta hai — command glue wahin chalega (ek hi queue consumer).
Mic/stop-event ka public raasta `wake/worker.py` se dena hai. `worker.stop()` ka
join sirf 3 s hai, par command + TTS 8 s+ lag sakte hain.

## 9. Owner ke haath me abhi ye kaam

1. **Awaaz ka asli test** (sirf ek baar, app band karke):
   `.\.venv\Scripts\python.exe -m desktop.playback --say "Ji, boliye"` — awaaz aayi?
2. **Ctrl+Alt+S dabao** → HUD khulna chahiye. Nahi khule to Desktop ka
   `Jarvis HUD.lnk` try karo (tray ki list me app ka naam **nahi** dikhta).
3. **Taskbar ke `^`** par click → Jarvis icon → right-click → **"Always show icons"**
   ( warna icon overflow me chhupa rehta hai).
4. **Purana Chrome tab `localhost:8000` band karo** → warna log token-reject se bharta hai.
5. **GitHub PAT revoke** — jo token push ke liye diya gaya tha, wo abhi chat me hai.

## 10. File ka rasta (kuch zaroori)

```
main.py            server (sirf 127.0.0.1)
config.py          .env + settings        -> config_brain / config_voice / config_hud / config_desktop
core/engine.py     message -> brain -> tool loop (sirf run_tool raasta)
brain/             pool, pool_config, health, probe
gatekeeper/        keeper, rules, approvals, audit (mask)
tools/             command, files, apps, system
server/            app + security + state (ek shared Engine) + *_routes
voice/             stt, tts (+ chain)
desktop/           launcher, app, tray, state, hud_window, hotkey, open_hud,
                   shortcut, playback (Step 2 ka speaker)
wake/              worker (module-level ek hi worker) + session, audio, model,
                   detect, phrase (Step 1) + utterance, wav (Step 2a)
ui/                index.html + hud_*.js + hud_*.css
tests/             40 suite + poolhelp.py / desktophelp.py / wakehelp.py / hud_*.py
```

## 11. Privacy warning

File ka text brain ke through **free provider** tak jaata hai. Personal/private
file ka content tool se mat pucho. `.env` har tool ke liye BLOCKED hai.