# Tests (40 suites)

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

> **Dhyan do:** 40 suite lagbhag 3–5 minute lete hain. Terminal ka timeout na ho
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
| `test_desktop_tray.py` | Tray icon ke 5 rang, menu ke 5 button, shared state, mic permission key, lock heuristic |
| `test_desktop_shortcut.py` | HUD ka backup raasta: `open_hud.plan()`, `shortcut.command()` list, Desktop path padhna, app/tray wiring — `.lnk` **kabhi banata nahi** |
| `test_desktop_hotkey.py` | `hotkey.parse/describe` (pure) + `Hotkey` stub flow + **thread-ownership pakkaura** (`RegisterHotKey` aur pump ek hi thread) + hotkey file ka hygiene |
| `test_desktop_playback.py` | Speaker: TTS bytes -> 16-bit PCM (`miniaudio.decode`, memory buffer), PCM -> `sounddevice.play`, output device list + filter, `--list`/`--say` |
| `test_desktop_play_say.py` | `playback.say()` — text se TTS, **har galti par `0` aur crash nahi** (TtsError / crash / khaali audio / timeout), `--say` ka raasta |
| `test_wake.py` | Wake constants, PCM/RMS + energy VAD (pure), Vosk JSON par `detect`, "jarvis" pakadna, model ke **error** raaste |
| `test_name_jarvis.py` | **Step 1 naam**: wake phrase variants + near-miss, grammar me `[unk]`, legacy "sunday" list (default band, `PRABH_WAKE_LEGACY=1` par chalu), persona `jarvis.txt`, tray/shortcut, `fill_html()` placeholder replace, aur UI grep (teen exception chhodkar har "Sunday" pakadta hai) |
| `test_wake_loop.py` | Worker ka poora loop **fake mic + fake listener** se: trigger, `heard` state, cooldown, mute-pause, crash-safe callbacks |
| `test_wake_worker.py` | Worker ka **wiring** (`wake_worker.start/stop/…`) — `Session` ke sirf do cheez fake, asli mic/model kabhi nahi |
| `test_wake_utterance.py` | Wake ke baad ka command: pre-roll, VAD se band karna (end-silence 2.0s), `COMMAND_MAX_SECONDS` par kaatna, min/wait/stop, **mic mar jaye to turant lautna**, `wav.py` ka sahi WAV |
| `test_wake_command.py` | **Step 2c ka flow** — fake mic + fake STT + fake playback: ack -> capture -> stt -> shared ENGINE -> awaaz; mute/lock par kuch nahi; not-heard / no-text; `via="voice"`; har stage ka time; `ui/app.js` guard |
| `test_wake_brain.py` | Wake se **brain** tak: brain ne kuch nahi diya / saare provider fail (awaaz par reasons **na** padhe, `BRAIN_FAILED` bole) / brain crash; **ASK card par awaaz se allow nahi** (AST se gatekeeper import check); "confirm kijiye" generator rukne se **pehle** boli jaaye |
| `test_wake_listen.py` | `listen.py` ke chaar kaam + pause: drain/warmup; **stop par to_text aur speak dono ruke**; command me hold aur baad me chhod; **MUTE hold absorb kare** (MUTE haar nahi maarta) |
| `test_bat.py` | `start_prabh.bat`: CRLF + ASCII + raw-bracket rule, aur asli `cmd` par launch line sach me chalti hai ya nahi |

### `test_desktop*.py` ke helpers

`tests/desktophelp.py` me `check()` / `show()` / `truthy()` / `finish()` hai
(poolhelp jaisa) + **speaker ke fake**: `FakeMini` (`miniaudio`), `FakeSd`
(`sounddevice`), aur `install_audio()` / `remove_audio()` jo dono ko `sys.modules`
me daalte hain (playback late import karta hai, is liye bas yahi karna padta hai).
Naya desktop test yahin se import kare.

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
