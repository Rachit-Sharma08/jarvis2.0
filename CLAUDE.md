# CLAUDE.md — Sunday (Prabh) ka handoff

Ye file **sirf direction** deti hai — haalaat, chalti cheezein, pakkaurey aur roadmap.
Detail ke liye: `AGENTS.md` (poore niyam) · `CHANGELOG.md` (kaam ka record) ·
`PLAN.md` (Phase 5 ka plan) · `TESTS.md` / `BRAIN.md` / `TOOLS.md` / `VOICE.md`.

> Owner coding nahi jaanta. Har baat **simple Hinglish** me samjhana hai.

---

## 1. Ye project kya hai

`D:\prabh` me ek **local personal app** hai — sirf usi PC par (`127.0.0.1`), web app
nahi. Naam **Sunday** (pehle "Prabh" tha, wo mode ab band hai). Ek brain hai
(sirf **free** providers), awaaz hai, aur 10 PC tools hain jinse Sunday computer par
kaam kar sakta hai.

## 2. Ab ka haal (2 Oct 2026 raat)

- Git **clean**, commit `b999c92`.
- **28 test suite green** (`SUITE GREEN`). Sab standalone, koi real API call nahi.
- App chalta hai: `GET http://127.0.0.1:8000/` = 200, tray + HUD live.
- Phase 5 **Step 3a (desktop shell)** poora. Aage **Step 1 = Vosk wake word**.
- Sab production file **200 line se chhoti**.

## 3. Chalane ka tareeka

| Kya | Kaise |
|---|---|
| App chalao | `start_prabh.bat` par double-click (supervisor crash par dobara chalata hai) |
| HUD kholo | tray menu · Desktop ka `Sunday HUD.lnk` · **Ctrl+Alt+S** |
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
- 3–5 min leti hai — `Start-Job` + result file wala tarika `TESTS.md` me hai
  (har naye shell me `Start-Job` mar jaata hai, is liye **detached** process chalao).

## 5. Sunday ABHI ye kar sakta hai

**Baat-cheet**
- Text: HUD ya browser me likho → brain sochta hai → jawab.
- Awaaz: mic dabao → bolo → wahi brain → **female awaaz** me jawab
  (TTS chain: ElevenLabs → Cartesia (abhi skip) → Edge Swara).

**Brain — 5 free provider, ye order (NVIDIA aakhir me, credits kat-te hain):**
Groq `gpt-oss-120b` (T1) → Gemini 3.5 Flash → OpenRouter `nemotron-3-super-120b :free`
→ Groq `gpt-oss-20b` → NVIDIA `nemotron-3-super-120b`. (`brain/pool_config.py` me
badlo — engine me kabhi hard-code mat likho.)

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

## 6. Sunday ABHI ye NAHI kar sakta (galat mat samjho)

- ❌ **"Hello Sunday" wake word nahi hai** — `wake/worker.py` stub hai (`READY=False`).
  Chat likhne ya mic dabane se chalta hai, **bula kar nahi**.
- ❌ **Awaaz se PC control nahi** — sirf text/awaaz me soch. Tools chat se chalte hain.
- ❌ **Auto-start nahi** — Windows login par khud nahi chalta (Step 3 me aayega).
- ❌ **Prabh mode band** — code maujood hai, `PRABH_SUNDAY_ONLY=1` se off.
- ❌ Cartesia ki female voice id nahi mili → wo provider skip ho jaati hai.

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
12. **Test me asli Desktop/tray/Edge/registry/`RegisterHotKey` kabhi mat chalao.**
13. **`.lnk` banana/hataana test me nahi** — `shortcut.command()` ki list check karo.
14. **Windows tray list exe ka naam dikhati hai**, app ka nahi. Registry ka key
    hash hota hai — hard-code mat karo, har change se pehle `reg export`.

Poora niyam → **`AGENTS.md`** (section 3.1–3.4, 8, 8.1, 8.2).

## 8. Aage ka roadmap

| Step | Kya | Halaat |
|---|---|---|
| **1** | **Vosk wake word** — `wake/worker.py` asli, VAD + recognition → `on_wake` | **agla kaam** (model download ho chuka hai) |
| 2 | Mic se command + Python se playback (`wake/audio.py`, `desktop/playback.py`) | Step 1 ke baad |
| 3 | Auto-start (HKCU Run) | **sirf jab owner "haan" bole** |
| — | Face / trust / learn / maker | aage, decided nahi |

## 9. Owner ke haath me abhi ye 3 kaam

1. **Ctrl+Alt+S dabao** → HUD khulna chahiye (synthetic key se test nahi ho paya).
2. **Taskbar dekho** → Sunday icon seedha dikhta hai ya nahi? (Wo *python* likhta hai —
   ye normal hai, list exe ka naam dikhati hai.)
3. **Purana Chrome tab `localhost:8000` band karo** → warna log token-reject se bharta hai.

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
desktop/           launcher, app, tray, state, hud_window, hotkey, open_hud, shortcut
wake/worker.py     abhi STUB (Step 1 me asli)
ui/                index.html + hud_*.js + hud_*.css
tests/             28 suite + poolhelp.py / desktophelp.py / hud_*.py
```

## 11. Privacy warning

File ka text brain ke through **free provider** tak jaata hai. Personal/private
file ka content tool se mat pucho. `.env` har tool ke liye BLOCKED hai.