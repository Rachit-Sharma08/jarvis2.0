# Tests (75 suites)

Sab suite **standalone** hain — ek-ek karke ya loop me. Koi **asli API call nahi**
karta, koi **khatarna command** nahi chalta, aur key ki zarurat nahi padti.
Har file ke end me "OK" / "Saare ... test pass." aana chahiye aur **exit code `0`**.

Kuch suite aakhir me `print("FAIL:", FAILED if FAILED else "koi nahi")` likhte hain —
usme `"FAIL:"` sirf static label hai. **`koi nahi` matlab sab pass**. asli faisla exit
code se lena, text se nahi.

## Sab ek saath

```powershell
cd D:\prabh
$fail = @()
Get-ChildItem tests\test_*.py | ForEach-Object {
  .\.venv\Scripts\python.exe $_.FullName
  if ($LASTEXITCODE -ne 0) { $fail += $_.Name }
}
if ($fail) { "FAILED: $($fail -join ', ')" } else { "SUITE GREEN" }
```

> **Dhyan do:** 75 suite lagbhag 3–5 minute lete hain. Terminal ka timeout na ho
> isliye sabse aasan raasta — background me chala kar result file padho:
>
> ```powershell
> $r = "$env:TEMP\prabh_suite.txt"; Remove-Item $r -ErrorAction SilentlyContinue
> Start-Job { $f=@(); Get-ChildItem D:\prabh\tests\test_*.py | ForEach-Object {
>     & D:\prabh\.venv\Scripts\python.exe $_.FullName *> $null
>     if ($LASTEXITCODE -ne 0) { $f += $_.Name } }
>   if ($f) { "FAILED: $($f -join ', ')" } else { "SUITE GREEN" } } | Tee-Object -FilePath $r
> ```
>
> Job chal jaye to `Get-Content $r` se pata chal jayega.

Ek-ek karke:

```powershell
.\.venv\Scripts\python.exe tests\test_gatekeeper.py
.\.venv\Scripts\python.exe tests\test_pool.py
```

## Kaunsa suite kya check karta hai

| Suite | Kya check karta hai |
|---|---|
| `test_basic.py` | Chat, mode switching, brain, logging |
| `test_security.py` | Token, origin, host, dangerous endpoints |
| `test_paths.py` | Traversal, case, 8.3 naam, junction, drive root |
| `test_gatekeeper.py` | SAFE/ASK/BLOCKED cases, path tricks, mode parity |
| `test_gatekeeper_approval.py` | Card hash, single use, 60s timeout, kill switch, rate limit, log masking |
| `test_tools.py` | 10 tools (temp folder me), 20 KB limit, scrubbed env, timeout |
| `test_tool_routes.py` | Tool endpoints, CSP, UI source safety |
| `test_prompt_strict.py` | LLM JSON strict validation + duplicate key reject |
| `test_engine_tools.py` | 5-step loop, ASK/BLOCKED, kill switch, mode parity |
| `test_engine_detail.py` | Tool output aur confirm card ki masking |
| `test_pool.py` | Tier failover, 404 par agla model, khaali jawab + 1 retry, 429 par retry nahi |
| `test_pool_billing.py` | Cooldown, Retry-After, credits lock, daily quota, free-only, sab-fail message |
| `test_probe.py` | Strict JSON probe, 2-call limit, 8s latency gate, 24h cache |
| `test_brain_status.py` | `/brain/status` route, Host/Origin/token, key masking, `.env` ignored |
| `test_voice.py` | Voice chain, limit, mode naam, `/stt` `/tts` |
| `test_voice_tts.py` | TTS chain order, clean(), teeno fail par saaf error |
| `test_tts_cache.py` | **Ack audio cache** — `speak_cached()` dobaara call na kare (fake provider, koi asli TTS nahi), hit asli tez ho, mode/text alag key, `cache_clear()`, bounded, **fail cache na ho**, plain `speak()` cache na kare |
| `test_speed_fix.py` | **Warm-up deadline + chuppi** — `listen.warmup(deadline=...)` ka sach: pura wait / bilkul free / sirf bacha hua; `COMMAND_END_SILENCE_SECONDS == 1.2`; hangover aur max/min seconds waise hi; `.env` override; `command.py` ke chhah stage naam + `deadline=settled_by` |
| `test_voices_female.py` | Female allowlist, male id skip, Edge Swara fallback |
| `test_stt_guard.py` | Duration <600ms, silence/khaali, non-Hindi/English script reject |
| `test_fixes_r1.py` | Round-1 fixes (modes, events, engine) |
| `test_fixes_r1_brain2.py` | Brain fallback + health rules |
| `test_fixes_r1_ui.py` | UI fixes, dedupe, labels |
| `test_fixes_r1_voice.py` | Cartesia payload, female chain, khaali text block |
| `test_hud.py` | Phase 4 HUD — ye khud se 4 helper file me phaila hai (neeche dekho) |
| `test_desktop.py` | Desktop shell: config/backoff, HUD `--app` command, launcher ke crash-restart ke faisle, startup ki 4 line, log ASCII, **hygiene (har source + har test file `<=200` lines)** |
| `test_desktop_single.py` | Single instance + stale PID/lock: `pid_alive`/`http_alive` ke fake probe, 4 "CHAL/atka/stale" combination, stale PID ka apne aap hatna |
| `test_desktop_guard.py` | App ke do "ruk jaao" pakkaure: TOOLS 30-min auto-off (+crash-safe hook) aur tray ke bina 3 koshish → `EXIT_NO_TRAY` |
| `test_desktop_tray.py` | Tray icon ke 5 rang, menu ke **6** button (naya `SO JAAO`), shared state (`asleep` bhi), mic permission key, lock heuristic |
| `test_desktop_shortcut.py` | HUD ka backup raasta: `open_hud.plan()`, `shortcut.command()` list, Desktop path padhna, app/tray wiring — `.lnk` **kabhi banata nahi** |
| `test_desktop_hotkey.py` | `hotkey.parse/describe` (pure) + `Hotkey` stub flow + **thread-ownership pakkaura** (`RegisterHotKey` aur pump ek hi thread) + hotkey file ka hygiene |
| `test_desktop_playback.py` | Speaker: TTS bytes -> 16-bit PCM (`miniaudio.decode`, memory buffer), PCM -> `sounddevice.play`, output device list + filter, `--list`/`--say` (`desktop/playback_cli.py`) |
| `test_desktop_play_say.py` | `playback.say()` — text se TTS, **har galti par `0` aur crash nahi** (TtsError / crash / khaali audio / timeout), `--say` ka raasta |
| `test_desktop_autostart.py` | **Step 3 auto-start** — `FakeReg` (dict-based nakli `winreg`): naam `Jarvis`, command `pythonw desktop\launcher.py`, space wale path me quote, install/remove/status cycle, error + "pehle se nahi tha", CLI dispatch (registry ke baghair), module-level koi registry call nahi |
| `test_wake_gate.py` | **Battery ka pakkaura** — `wake/gate.py` pure hai: khamoshi me 40 chunk me Vosk tak 0 (battery), awaaz + hangover par feed, `VAD_SILENCE_BLOCKS` par ek `listener.reset()`, `gate_on=False` par sab chunk (purana behaviour), wake ke baad reset, **khamoshi par flush** (`on_text` + crash-safe + flush khaali to reset), `config.describe()` me `gate=on` |
| `test_desktop_login.py` | **Login ka asli pakkaura** — Run key ka cwd `C:\Windows\System32` hota hai aur wahan se `-m module` mar jaata hai: value me `-m` nahi, launcher ko **asli** cwd par load karke `BASE` prove, `sys.path.insert` ka order `import config` se pehle, `os.chdir` + `creationflags` (app start/mic/tray kabhi nahi) |
| `test_desktop_hud_single.py` | **REGRESSION R-2: har "Jarvis" par nayi HUD window** (13-Oct). `_focus_existing()` hamesha `False` deta tha (bug) → 10 **asli** wake (`callbacks.on_wake`, `command.run` nakli) par **sirf 1** window + browser 1 hi baar; `focus_existing()` ab `True`; **alag process** (`open_hud.py` ka naya `HudWindow`) par bhi 1; `Ctrl+Alt+S` bhi wahi window |
| `test_desktop_hud_win.py` | HUD window ke edge cases — `win_find.is_hud_title` **pure** (exact `Jarvis HUD` / URL / `J.A.R.V.I.S` pakde, "Jarvis - Wikipedia" na pakde), khaali title, **Edge dheere khule** (grace se 1 hi spawn), grace ki hadd ke baad dobara koshish, band karke dobara kholna |
| `test_wake.py` | Wake constants, PCM/RMS + energy VAD (pure), Vosk JSON par `detect`, "jarvis" pakadna, model ke **error** raaste |
| `test_name_jarvis.py` | **Step 1 naam**: persona `jarvis.txt`, mode id `sunday` dormant, tray/shortcut ka naam, `fill_html()` placeholder replace, aur UI grep (teen exception chhodkar har "Sunday" pakadta hai) |
| `test_wake_phrases.py` | **Wake phrase + grammar** (5-Oct split): phrase variants + near-miss, grammar me **shabd** (multi-word phrase nahi) + `[unk]` aakhri + duplicate nahi, legacy "sunday" list (default band, `PRABH_WAKE_LEGACY=1` par chalu) |
| `test_wake_loop.py` | Worker ka poora loop **fake mic + fake listener** se: trigger, `heard` state, cooldown, mute-pause, crash-safe callbacks |
| `test_wake_trigger.py` | **Trigger ke teen raaste + mic retry** (5-Oct): final, partial, gate ka flush — sab `on_wake(phrase, mic, stop)`; wake shabd ke bina koi trigger nahi; `MME error 1` par `MIC_OPEN_ATTEMPTS` tak koshish |
| `test_wake_worker.py` | Worker ka **wiring** (`wake_worker.start/stop/…`) — `Session` ke sirf do cheez fake, asli mic/model kabhi nahi |
| `test_wake_utterance.py` | Wake ke baad ka command: pre-roll, VAD se band karna (end-silence 2.0s), `COMMAND_MAX_SECONDS` par kaatna, min/wait/stop, **mic mar jaye to turant lautna**, `wav.py` ka sahi WAV |
| `test_wake_command.py` | **Step 2c ka flow** — fake mic + fake STT + fake playback: ack -> capture -> stt -> shared ENGINE -> awaaz; mute/lock par kuch nahi; not-heard / no-text; `via="voice"`; har stage ka time; `ui/app.js` guard |
| `test_wake_brain.py` | Wake se **brain** tak: brain ne kuch nahi diya / saare provider fail (awaaz par reasons **na** padhe, `BRAIN_FAILED` bole) / brain crash; **ASK card par awaaz se allow nahi** (AST se gatekeeper import check); "confirm kijiye" generator rukne se **pehle** boli jaaye |
| `test_wake_listen.py` | `listen.py` ke chaar kaam + pause: drain/warmup; **stop par to_text aur speak dono ruke**; command me hold aur baad me chhod; **MUTE hold absorb kare** (MUTE haar nahi maarta) |
| `test_desktop_sleep.py` | **Battery: 'so jao'** - `desktop/sleep.py` ka pure guard (chhota text hi), `enter`/`wake_up`/`toggle` (`STATE.asleep` + HUD band, band na ho to bhi so jana), wake par **jaag jaana** (`callbacks.on_wake` pehle flag hatata hai), `command.run` par brain/ASK **chalta hi nahi**, tray ka item, aur do guard ki ek jaisi list |
| `test_wake_ack.py` | **Speed fix 2** - `listen.peek_speech` (awaaz pakdi/khamoshi/khaali queue/stop par ruka; chunks **wapas** queue me), user bol raha hai to **ack skip** (drain sirf goonj phenke), khamoshi me ack boli jaaye, brain ka poora jawab HUD par + awaaz me `tts.clip_answer` (vaakya ke end par kata) |
| `test_bat.py` | `start_prabh.bat`: CRLF + ASCII + raw-bracket rule, aur asli `cmd` par launch line sach me chalti hai ya nahi |
| `test_stt_speed.py` | **S-2 STT tez + pakka** — apna timeout 6 s (brain wala nahi), `max_retries=1`, `stt_deadline()` ceiling 16 s, `.env` override; **daemon thread + `join(timeout)`** par caller turant lautta hai (ye `asyncio.run` ke shutdown-join ka nuksan rokta hai), tez jawab wapas milta hai, provider error ka message shape |
| `test_tts_auth.py` | **S-2 ElevenLabs 401 = ek baar** — 401/403/unauthorized/invalid_api_key → `auth` → is session me BAND → do jawab me ElevenLabs sirf **1** baar, Edge dono baar; purane category (429/503/402/404/timeout) nahi bigde; `missing_key()` pure (key khaali par provider 0 baar, voice id set hone par bhi) |
| `test_wake_levels.py` | **S-2 chuppi 0.7 s + level log** — `pcm.quality()` pure (None/khaali/sine RMS 0.129/peak=max/clip pakda/square ~100%/normal level 0 clip), `capture()` ki **log line** me `peak_rms` + `clip` dono (success aur chhote dono par), raw audio log me nahi; default 0.7 + `.env` override + baaki windows (hangover/min/max/pre-roll) nahi badle |
| `test_tray_watch.py` | **T-01 tray icon** - `desktop/tray_watch.py`: `status()` ke teen haal (`IsPromoted=1` = visible / missing = hidden `^` / entry hi nahi = missing), apni entry tooltip se pehchan (`MyJarvis.Desktop` jaisa purana entry chhoda), tez→dheere timing, **sirf haal badne par** message, registry fail par chup, aur `start`/`stop` (ek hi watchdog, env `PRABH_TRAY_WATCH=0` par thread nahi). **Asli registry kabhi nahi** — fake `entries_fn` |
| `test_logsafe.py` | **KAAM 0 — test ka log alag** — `config.LOG_DIR` asli `logs/` nahi, `PRABH_LOG_DIR` env se aata hai, ek line temp log me likhi jaati hai + `logs/prabh.log` **bilkul** nahi chhoota, ASCII rule, aur **har** `tests/test_*.py` me `logsafe` import hai |
| `test_wake_alarm.py` | **KAAM 1 — alarm ka loop** (awaaz nahi) — `--dry-run` plan me 07:00/07:10/15 min; `alarm_ack` flag (shuru me + beech me) se ruka; console key par ruka; **15 min** cap (~45 round, 45 sleep); `max_rounds` safety; `--no-audio` par `alarm_audio.speak/play_wav/edge_tts` **0 baar** |
| `test_wake_alarm_audio.py` | **KAAM 1 — awaaz + flag file** (PowerShell/wav/speaker sab fake) — edge-tts pehle → khaali audio par **SAPI** → dono fail par `'none'`; koi crash bubble na kare; wav sirf path check; `clear_ack()`/`--keep-ack`; system volume code se nahi chheda |
| `test_wake_alarm_tool.py` | **KAAM 1 — tool (DEFAULT OFF) + Task Scheduler** — `parse_when()` pure (7/7:30 am/9 pm/12 am/kal/galat/ValueError), `clamp_minutes`, `ALARM_TOOL_ENABLED=0` par tool LLM ko dikhta hi nahi + `execute()` mana + koi file nahi, on par request file; `gatekeeper` risk **ASK**; `ps_when()` **minute rakhta hai** (07:10 ka task 07:00 na bane) + locale-safe + `[datetime]::new` nahi; `install()` ke do task 10 min door + `--if-no-ack` sirf backup par; `register()` bina `OK` ke `NAHI BANA` bolta hai. **Asla PowerShell kabhi nahi** |
| `test_self_hearing.py` | **KAAM 2 — apni hi TTS se WAKE HIT nahi** — `Trigger.mark_tail/tail_active/suppressing` (0.4 s, expire, 0/negative safe, cooldown alag), `_loop` ab `suppressing()`, `set_tail` delegate, `release_from_command()` **order: tail pehle phir unpause**, 18 s wali apni awaaz par trigger nahi, guard hatte hi asli "Jarvis" phir se |
| `test_hearing_audit.py` | **KAAM 2 — saboot** — `config.PLAYBACK_MUTE_MIC` production me **kahin use nahi hota** (sirf define), asli rok `hold_for_command`/`release_from_command` hai, aur `listen.drain()` 400 chunk (~12 s) bounded hai jabki jawab 18 s — yahi self-hearing ki wajah |
| `test_permissions_v2.py` | **KAAM 3 — permissions v2** — allowed apps (VS Code/Brave/WhatsApp + aliases, anjaan app poochhta hai); **hamesha card** ke 6 kaam apni wajah ke saath; `NEVER_ALLOW` **BLOCKED**; safe tool safe rahe; `discord`/`scare` jaise shabd galat na pakde; purana BLOCKED table bhaara nahi; **injection** — page/file/message ka "sab allow kar do" / "WhatsApp bhej do" / "ignore previous instructions" args me bhi kuch nahi badalta, guard-file unlock nahi hota, URL me `risk=SAFE` likhne se SAFE nahi milta, aur rule **sirf args** dekhta hai (source ka naam hi nahi) |
| `test_permissions_table.py` | **KAAM 3 — table ki jagah** — `ALWAYS_ASK`/`NEVER_ALLOW` **config** me (code me hard-coded nahi), aur **har** faisle ke saath karan bhara hua |
| `test_speed_replies.py` | **KAAM 4 — tez jawab** — `voice_answer()` pehle 1-2 **poore** vaakya (vaakya beech se nahi kata), char limit, `sentences()` helper (danda bhi), `command.py` wiring; `answer_cache.key()` static waisa (**tuple text `str()` nahi** — prewarm ka pop chup-chaap fail hota tha) + volatile me **minute ka bucket** (usi minute hit, agli minute naya); `speak_cached()` wiring + cache bounded |
| `test_hot_window.py` | **KAAM 5 — follow-up (DEFAULT OFF)** — flag band par `mark_hot`/`hot_active` False aur **sirf bolne par trigger nahi** (wake shabd zaroori); ek wake + **teen follow-up**; window re-arm + expiry; **apni awaaz follow-up nahi** (tail guard); silence (`Thank you.`/`hmm uh`) follow-up nahi; `is_utterance()` sirf asli baat (STT ki wahi silence list, duplicate nahi) |
| `test_hot_window_helpers.py` | **KAAM 5 — wiring** — `command.py` ke `finally` me `mark_hot()` aur wo **release ke BAAD**; `Session.set_hot` + `worker.mark_hot` delegate; config 12 s; env key ke naam; `config.describe()` me `hot=` |
| `test_hud_stats_load.py` | **KAAM 6 — SYSTEM panel `--` na rahe** — `/hud/stats` 200 + `cpu`/`ram` **kabhi `None` nahi** (yaani `--` data ki kami nahi, call na hone ki kami thi); battery `percent=None` par UI PLUG; bina token 401; naya `ui/hud_prime.js` load par `/hud/stats` maarta hai + token bhejta hai + `index.html` me tag; weather **double** fetch nahi; WS raasta bhi bacha; `textContent` (innerHTML nahi); pump **pehle** sota hai (ye `--` ki wajah tha). **Browser nahi, port 8000 par kuch nahi** |
| `test_hud_bar.py` | **KAAM A — bottom bar (Playwright headless, nakli server)** — 1366x768 + 1280x720 + 1920x1080 + 1200x688 + 1024x700 par bar ka cut nahi, koi element clip nahi, 13 overlap pair me koi overlap nahi, hud overflow nahi. Bug-injection: `.remind-pill` par absolute wapas daalne se 5 check fail. Screenshot `%TEMP%` me, repo me nahi |
| `test_hud_arc.py` | **KAAM B — Arc theme (Playwright headless, nakli server)** — 1366x768 + 1920x1080 par clip/overflow nahi, input bar poori, reactor ka **asli geometry** (`getBBox()` > 0 — namespace bug yahin pakda), 3 state label, Hindi typewriter, default neela regress nahi, `?theme=` whitelist (adhoori value reject, bada `ARC` chalta hai). Bug-injection: namespace bug wapas daalne par 8 clean FAIL (crash nahi). Screenshot `%TEMP%` me |

### `test_desktop*.py` ke helpers

`tests/desktophelp.py` me `check()` / `show()` / `truthy()` / `finish()` hai
(poolhelp jaisa) + **speaker ke fake**: `FakeMini` (`miniaudio`), `FakeSd`
(`sounddevice`), aur `install_audio()` / `remove_audio()` jo dono ko `sys.modules`
me daalte hain (playback late import karta hai, is liye bas yahi karna padta hai).
Naya desktop test yahin se import kare.

`tests/hudhelp.py` (HUD window, 13-Oct) — `FakeDesktop` (asli Edge ki jagah:
`finder()` = nakli `find_hud_window()`, `spawner()` = nakli `Popen`, window
"banati" hai), `FakeProc`, `FakeRun` (taskkill ka nakli), `FakeCommand`
(`wake/command.run`), `FakeApp`, `make_hud()`, `wake()` (asli
`callbacks.on_wake` call) aur `patched()` (`bring_front` fake +
`HUD_PROFILE_DIR` temp par). Naya HUD test yahin se import kare.

**Bade suite ko 2-3 file me todo** (AGENTS.md ka 200-line niyam). `test_desktop.py`
200+ lines ho gaya to usme se theme alag karke naya file banao — jaise
`test_desktop_single.py` (single instance) + `test_desktop_guard.py` (TOOLS
auto-off + tray guard) banaye gaye. Ek zaroori baat: file todte waqt **helper
function/class ko usi function me mat chhodo** jahan use hota hai — module level
par le jao, warna doosre function me `NameError` (silent fail) ho jaata hai.

**Desktop suite ka niyam:** koi **asli** cheez mat chalao — Edge spawn nahi,
tray message loop nahi, Run registry nahi, mic nahi, **speaker nahi**. Sirf
**command/path/faisla** check karo (`hud_window.command(...)`,
`launcher.next_step(...)`). Isi liye `launcher.next_step()` pure function hai —
wapas me crash list deta hai aur `crashes` ko mutate nahi karta, to test me
process chane ki zarurat nahi.

### `test_wake*.py` ke helpers

`tests/wakehelp.py` me `check()` / `show()` / `truthy()` / `wait()` + **teen fake**:
`FakeRecognizer` (Vosk jaisa JSON), `FakeListener` (text ki list), `FakeMic`
(chunk queue), aur `loud()` / `quiet()` (raw PCM banao). Naya wake test yahin se
import kare.

**Wake suite ka niyam:** asli **mic**, **Vosk model** aur `sounddevice` kabhi nahi
chalti. Loop test me sirf **do** cheez patch hoti hain —
`wake.session.detect.build` aur `wake.session.audio_mod.MicSource` — kyunki
`Session.start()` bas yahi maangta hai. Model ke sirf **error** raaste check hote
hain (`load()` chala kar 1 second + RAM lagana test ka kaam nahi).

Dhyan do: `worker.wakes()` **poore app ka count** hai (reset nahi hota). Do test
me aage-pahe compare kar rahe ho to pehle `before = worker.wakes()` pakad lo.

**Step 2c ke fakes `tests/wakecmdhelp.py` me hain** — teenon Step 2c suite
(`test_wake_command` / `test_wake_brain` / `test_wake_listen`) wahan se import
karte hain: `patch()`, `Spy`, `FakeEngine` (`server.state.ENGINE` ki jagah),
`hub_spy()`, `engine_say()`, aur poora `command.run` chalane wala `talk()`.

### Data-safety (har suite ke liye) — `tests/datasafe.py`

Test asli `data/` ko **kabhi** nahi chhoo sakta. `with isolated_data():`
(plain test) ya `class X(DataSafeCase):` (unittest setUp/tearDown) — dono data
folder + memory/audit/todos/reminders/kb/notes/rss/pomodoro path tmp par
daalte hain, `MEM._items` khaali karte hain, tearDown par wapas. Guard: koi
path asli `data/` me gir gaya to AssertionError. Jo test `engine.handle()`,
asli `/chat`, `MEM.clear()` ya `config.DATA_DIR` chhue, usme ye **zaroori** hai.
`gatekeeper_uses()` bhi wahin hai — `wake/command.py` me gatekeeper ka kya import
hua, **AST** se (docstring me likhe text se dhoka nahi chalta). `COMMAND_WARMUP_SECONDS
= 0` kiya jaata hai warna har test 1 second extra lega. Asli API, mic ya speaker
**kabhi nahi**.

### `test_hud.py` ke helpers
Runner sirf hai; saare checks char helper me hain (har file `<200` lines):

| Helper | Kya check karta hai |
|---|---|
| `hud_common.py` | `check()` / `read()` / `headers()` + UI file list (sab yahin se import) |
| `hud_check_ui.py` | XSS guard (innerHTML/eval nahi), HTML ids, `<200` line, fonts, clock, orb SVG+animation, activity tags, STOP wiring, 1366x768 grid |
| `hud_check_get.py` | same-origin GET ka rule — Referer / `Sec-Fetch-Site` proof, cross-site reject, `origin_from_referer()` |
| `hud_check_api.py` | weather `_parse` mock + crash-safe, stats shape/cache, `/hud/*` security + CSP, `/hud/quick` extra-field 422, gatekeeper no-bypass, **ek shared Engine** |

### Playwright helper (`hudserve.py` + `hudcheck_bar.py`/`arccheck.py`)

`tests/hudserve.py` dono Playwright suite ka shared nakli server hai — sirf
`ui/` static + `/hud/stats` + `/hud/weather`, port **8731+** (8000 kabhi
nahin), `import config` nahi (`.env` chhua hi nahi). `ThreadingHTTPServer` +
HTTP/1.1 + Content-Length — warna Chromium ke parallel load beech me kat
jaate hain aur alag-alag baar alag JS error aata hai. `?theme=` ka rule asli
server jaisa (lowercase + whitelist).

`hudcheck_bar.py` (KAAM A) aur `arccheck.py` + `arc_probe.py` (KAAM B) me
asli checks hain; `test_hud_bar.py` / `test_hud_arc.py` sirf runner hain.
Dono ke niyam `hud-playwright-check` skill me hain.

Naya test is file me daalna ho to sahi helper chune — nayi file banane se pehle
socho, `hud_check_ui.py` UI ke liye hai aur `hud_check_api.py` server ke liye.

## Naya test likhte waqt

- **Asli network call kabhi nahi.** `httpx`/provider hamesha fake.
- Khatarna command **sirf faisle se** test karo (executor mock) — chalao mat.
- File tools **sirf temp folder** me.
- Bade suite ko 2-3 file me todo — har file `<200` lines rahe.
- Hindi print ho to pehli line ke baad `sys.stdout.reconfigure(encoding="utf-8")`
  zaroori hai, warna Windows console par `UnicodeEncodeError` aata hai.
- Route test me `app.routes` par `.path` mat pakdo (lazy router object);
  `app.openapi()["paths"]` use karo.
- Mile hue helpers `tests/poolhelp.py` me hain — naya pool test wahin se import kare.
- Desktop test me bhi `tests/desktophelp.py` se `check()` lo, aur startup entry
  (Run key) kabhi test me register mat karo.
- **Source-text check bhi badalta hai** — koi file split/reorganize karo to purane
  suite ka `app_src.count(...)` wala check fail hoga. Pakka raasta badlo, matlab
  nayi file ka naam aur sach (jaise `desktop/callbacks.py`) check karo.
- **Asli Desktop/registry kabhi mat chhedo** — `shortcut.install()`/`remove()`
  ko test me mat bulao, sirf `shortcut.command()` ki list check karo. Warna asli
  Desktop par `.lnk` ban jaata hai ya ghat jaata hai.
- **Asli `RegisterHotKey` bhi mat chalao** — `Hotkey(api=StubApi())` daal kar
  start/stop/press ka flow check karo. Stub me `threading.get_ident()` record
  karwao: `RegisterHotKey` aur `pump()` **ek hi thread** par hone chahiye
  (warna `WM_HOTKEY` kisi aur queue me chala jaata hai aur key kabhi trigger
  nahi hoti — 2-Oct ka asli bug yahi tha).
