# Changelog (Jarvis ka pura record)

`AGENTS.md` sirf **niyam** rakhta hai; kaam ka poora record yahan hai. Ek line =
ek kaam ka group. Doc ka detail `BRAIN.md`, `TOOLS.md`, `VOICE.md`, `TESTS.md`,
`ROUND2.md` me hai.

---

## Wake fix: do command me dusra nahi chalta + mic busy (5 Oct 2026)

Do shikayatein thi: **"ek command ke baad doosra command nahi leta"** aur app
start par `wake: nahi chala` (mic busy).

### Asli bug 1 — Vosk ka pending text chhoot jata tha

`wake/gate.py` khamoshi par sirf `listener.reset()` karta tha. Isi reset me Vosk ka
**abhi tak poora nahi hua** text (`partial`) khatam ho jata tha. Wake debug
(`PRABH_WAKE_DEBUG=1`) se yehi nikla: chunks aa rahe the, Vosk ko ja rahe the,
par `finals=0`. Log me do alag lines the:

```
sun liya (final): 'hello'
sun liya (final): 'yo'
```

Yaani "Hlo Jarvis" **do tukde** me toot raha tha aur dono pheke ja rahe the —
koi bhi tukde me `jarvis` nahi tha, is liye trigger nahi. (Jab dono ek saath
aa jaate — "hello jarvis" — trigger ho gaya tha.)

Fix — **teen raaste, ek faisla** (naya `wake/trigger.py`):

| Raasta | Kya kiya |
|---|---|
| **final** | purana raasta, waise hi |
| **partial** | naya — Vosk abhi bol raha hai aur text me `jarvis` hai (sabse tez, khamoshi ka intezaar nahi) |
| **flush** | naya — gate silence par `FinalResult()` se pending text **nikal** deta hai (`detect.Listener.flush()`), phir reset |

Naye `start()` par cooldown bhi saaf hota hai (`Trigger.reset_cooldown()`) —
warna restart ke baad pehla "Jarvis" 1.5 s tak pakda hi nahi jata tha.

### Asli bug 2 — grammar me poori phrase, shabd nahi

`config_name.wake_grammar()` poori list deta tha (`"hello jarvis"`, `"hlo jarvis"`).
Vosk/Kaldi aise multi-word phrase ko apne lexicon se map **nahi** kar pata — isi
liye upar wala split hua. Ab grammar me har **shabd** alag hai (`grammar_words()`),
trigger ka faisla phir bhi `WAKE_WORDS` se. Chhota nuksan: `hlo`/`helo` model ke
lexicon me nahi hain, is liye Vosk ek warning deta hai (`desktop.out` me ek line);
text me wo rahte hain.

### Asli bug 3 — mic busy par ek hi koshish

Log: `PortAudioError ... [MME error 1]` → `wake start fail (#1)` → app chup.
Asli wajah: mic kisi aur app (Chrome/Teams) ne pakda hua tha. Ab
`Session._open_mic()` `MIC_OPEN_ATTEMPTS` (default **3**, beech me
`MIC_OPEN_RETRY_SECONDS` = 1.2 s) tak sirf `MicUnavailable` par retry karta hai —
constructor/model ka crash turant upar jaata hai. Mic ka error log ab batata hai
ki **kaun** pakad raha hai.

### Do aur asli galti jo split me pakdi

1. **`stop()` par double loop** — join 3 s ke baad bhi thread zinda ho to
   `_close()` karke `_thread = None` kar deta tha, aur agla `start()` **doosra**
   loop chala deta tha (ek hi Session, do loop). Ab zinda thread par `_close()`
   nahi hota.
2. **`worker.wakes()` ka count reset** — `Trigger` har `start()` par naya banta
   tha, to app-lifetime trigger count ghata deta tha. Ab `Trigger` ek hi
   instance hai (`Session.__init__`), sirf callbacks `set_callbacks()` se badalte
   hain.

### Naye file + test

| File | Kaam |
|---|---|
| `wake/trigger.py` | Trigger ka poora faisla: cooldown + `hit()` + `on_wake(phrase, mic, stop)` + `flush` |
| `wake/lifecycle.py` | `Session` ka zindagi hissa (`_end`/`_fail`/`_close`/`_say`) |
| `tests/test_wake_trigger.py` | **Naya** - teen raaste + mic retry (asli mic/Vosk kabhi nahi) |
| `tests/test_wake_phrases.py` | **Naya** - `test_name_jarvis.py` 200 cross kar gaya tha, wake-phrase wala hissa yahan |

`test_wake_gate.py` me 3 naye check (flush par text wapas, khaali flush → reset,
flush crash-safe). `test_wake_loop.py` ka crash fake ab **teen** args leta hai
(`on_wake(phrase, mic, stop)`) — ek-arg fake se TypeError hota tha. Sab file
`<=200` lines, **51 suite green**.

---

## Test-hang fix: `stt.transcribe` me size guard nahi tha (5 Oct 2026)

Doosri run me poori suite **3+ minute atki** — `test_voice.py` ka "badi audio"
check. Asli wajah: `voice/stt.py` me **size guard kahin nahi tha**; 10 MB ki limit
sirf `server/voice_routes.py` (HTTP) par thi. Test direct library call karta hai, to
11 MB ka blob **asli Groq par upload** ho raha tha (aur quota bhi ja raha tha).

Fix: `SttError` wale size check ko `voice/stt.py` me daala — ab ye guard
har caller ke liye hai, sirf HTTP ke liye nahi. Wake path (`wake/listen.py`) bhi
yahin se guzarta hai (16 kHz mono, 30 s max ≈ 1 MB), to asli use me guard kabhi nahi
chalta — sirf bade blob par. Ab `test_voice.py` **network-free** hai aur 2 second me
pass hota hai; poori suite **63 second** me green.

**Niyam:** test me provider API kabhi sach me call nahi honi chahiye. Test ka
`_stt_fails()` ab guard par fail hota hai, asli upload par nahi.

---

## T-01 fix: tray icon ASLI wajah invisible tha (4 Oct 2026, sha 1929028)

Upar wala T-01 pura **galat diagnosis** tha. Woh likha gaya tha ki icon `^` me chhupa
hai aur `IsPromoted` missing hai — dono galat. **Asli bug ek line ka tha.**

### Asli bug

`desktop/tray.py` me `run_detached(setup=self._on_setup)` diya tha. **pystray tabhi
`visible = True` khud karta hai jab `setup` callback na mile** (`_base.py:395` —
`setup` diya to sirf `setup(icon)` chalta hai, `else` branch `visible = True` karta
hai). Hamara `_on_setup` sirf `log.info("tray ready")` karta tha → **icon kabhi
visible nahi hua**.

Isi se sab samjhaya aata hai:
- `NIM_ADD` chala tha → `NotifyIconSettings` me entry banti thi → `tray_watch`
  "tray icon taskbar me dikh raha hai" bolta tha (wo **galat** report thi).
- `IsPromoted=1` likhne se bhi kuch nahi hua — kyunki entry ban chuki thi, sirf
  icon invisible tha.
- Settings me sirf "python" dikha — kyunki shell exe ka naam dikhata hai.
- Tray menu kuch bhi karne par "band" lagta tha.

Fix: `_on_setup` me `icon.visible = True` (comment ke saath, taaki koi na hata de).

### Kaise pakda (3-step live debug — naya tareeka)

Pehle ka pura andaza galat tha, is liye **source code ke bajaye live measurement**:

1. **UIA se taskbar padha** (`.NET AutomationElement`) — `Shell_TrayWnd` ke
   descendants me hamara icon `Name` se dikhta hai ya nahi, aur overflow flyout
   (`TopLevelWindowForOverflowXamlIsland`) khol kar uske andar. Pehle: na promoted
   me, na overflow me.
2. **raw Win32 probe** (pystray bilkul nahi, sirf `ctypes`) — `NIM_ADD` ka **BOOL
   return `1`** aaya (shell ne maan liya) aur icon overflow me **dikha**. Is se
   pichla "GetRect is PC par kaam nahi karta" wala nivaaj bhi confirm hua.
3. **bare pystray probe** (app ke bina) — `PYSTRAY-PROBE` overflow me dikha. To
   pystray theek hai, Win32 theek hai → farq **hamare app ke setup** me hai.
   Hamara asli `desktop.tray.Tray` class chala kar dekha → wo nahi dikha.
   `print` se `visible = False` confirm hua.

Uske baad `_base.py:395` padha aur fix mil gaya.

### Live proof

App restart → promoted tray me `Jarvis - band` dikha (UIA se verify). Pehle kabhi
nahi tha.

### S6 step 6: base `python.exe` — try kiya, chhoda

`child_python()` ko `D:\Python312\python.exe` par pin karne se child
`ModuleNotFoundError: No module named 'uvicorn'` se mar gaya (base venv me
`include-system-site-packages = false`). **Asli masla interpreter nahi tha** —
wapas venv `sys.executable`. Docstring me wajah likhi.

### Baaki

- `tray_watch.py` ke dono message ab "lagta hai" jaisa shabd use karte hain —
  registry entry **register** hona proof hai, **visible** hona nahi.
- Naya regression test `tests/test_desktop.py::test_tray_visible`.
- `AGENTS.md` 8.2 me 4 naye bullet (asli bug + UIA tareeka + ctypes dtype traps).
- **48 suite green.**

---

## T-01: tray icon taskbar me (4 Oct 2026) — ye diagnosis GALAT thi

Roadmap ka pehla task. Owner ne confirm kiya ki icon `^` (hidden icons) me **nahi**
dikhta — matlab pehle ka "overflow me chhupa hai" wala andaza adhoora tha.

> ⚠️ **Neeche ka poora section galat diagnosis hai** — asli bug `visible=True` tha
> (upar wala section padho). Yahan jo likha hai wo "registry se faisla" wala galat
> raasta document karta hai, is liye rakha hai taaki dobara na ho.

### Asli kya mila (3 tareeke se prove kiya — ye teen galat the)

1. **`Shell_NotifyIconGetRect` is PC par kaam hi nahi karta.** Sahi hwnd + sahi uid
   ke saath bhi `E_INVALIDARG (0x80070057)`. Doosre process se bhi same. Pehle isi
   API par watchdog likha tha, aur wo **galat** warning de raha tha ("icon shell me
   nahi") — jabki icon shell me tha. Throwaway probe se confirm: ek naya, alag
   pystray icon banaya, shell ne uski registry entry bana di (matlab icon accept
   hua) par GetRect phir bhi fail raha. **API ko hata diya** — galat warning asli
   kaam chhupa deti hai.
2. **Sahi source `HKCU\Control Panel\NotifyIconSettings`.** Shell sirf usi exe ki
   entry banata hai jiska icon uske paas hai. Entry apni `InitialTooltip` se pehchan
   hui (`Jarvis - band` — naam se shuru). `IsPromoted` sirf tab hota hai jab icon
   **taskbar me dikhta** hai; missing = `^` me chhupa.
3. **Stale entry ka dhoka.** Pehle ka `MyJarvis.Desktop` entry 2 din se pada tha
   (`Stop-Process -Force` par shell icon hata nahi). Naye probe ka entry bhi
   `icon.stop()` ke baad pada raha — matlab "entry hai" akela proof nahi.

### Kya badla

- Naya `desktop/tray_watch.py` (~150 lines): roz registry **padh** kar batata hai
  `visible` / `hidden` (`^` me) / `missing` (entry hi nahi), aur **sirf tab log
  karta hai jab haal badle** — ek start = ek line. `VISIBLE` par INFO, baaki par
  WARNING + sahi raasta (`^` par click karo / `Ctrl+Alt+S`).
- Naya `config_tray.py` (timing: pehle 60 s har 3 s, phir har 30 s;
  `PRABH_TRAY_WATCH=0` se band). `config_desktop.py` 198 par tha, is liye naye
  switches wahin nahi daale. `config.py` me re-export.
- `desktop/app.py`: `_start_tray()` ke baad `tray_watch.start()`, `_shutdown()` me
  `tray_watch.stop()`. Ek hi raasta.
- **Registry:** backup `backup/notifyicon-traywatch-20261004-123546.reg` (23 entry,
  329 KB) → sirf apni entry `1254505825646409161` par `IsPromoted=1`. Entry count
  23 → 23 (baaki 22 icon chhua nahi), `SHChangeNotify` bheja.
- Naya suite `tests/test_tray_watch.py` (pure + fake `entries_fn`, asli registry
  kabhi nahi). **48 suite green.**
- Probe ka apna entry (`ProbeTestIcon`) delete kiya — 24 → 23.

### Proof (live log)

```
tray watchdog chalu (pehle 60s, phir 30s me ek dekh)
tray icon taskbar me dikh raha hai - theek hai
```

### S6 ke baaki steps

Step 6 (`python.exe + CREATE_NO_WINDOW`) **zarurat nahi padi** — icon asli me shell
me tha, sirf promote nahi tha. Interpreter badalne se ye bug solve nahi hota, sirf
ek aur cheez badalti hai. Decided: mat karo.

---

## Step 2-5: battery sleep, tools hamesha ON, "Hlo Jarvis", tez jawab (4 Oct 2026)

User ke 4-Oct ke 4 faisle, ek hi round me. Sab kaam **app hi chalu rakhkar** hua.

### Step 2 - "so jao" (sleep) + `wake/ask.py` split

Mic sunna kabhi band nahi hota, is liye battery ka bachat **baaki sab** band karke
mila. Naya `desktop/sleep.py`: pure `matches()` + `enter`/`wake_up`/`toggle`.
Wake ke baad STT se pehle hi text se pata chalta hai ki "so jao" bola ya nahi -
us case me brain/ASK chalta hi nahi, sirf haalat. Jaagne ka ek hi raasta: wake word
(`desktop/callbacks.on_wake` pehle `asleep` hatata hai, phir HUD + command wahi
purana flow). Tray me naya **SO JAAO** item (menu 5 -> 6 button).

`wake/command.py` 219 lines cross kar gaya tha, is liye brain/speaker wala hissa
nayi `wake/ask.py` me gaya (command 178, sirf flow). Do test me references badalne
pade - `wakecmdhelp.talk()` ab dono `HUB` patch karta hai, aur
`gatekeeper_uses()` `command.py` + `ask.py` **dono** scan karta hai (split ke baad
wo check khud chup ho gaya tha - "approve import hi nahi dikha" wala false pass).

### Step 3 - TOOLS default ON, auto-OFF hata

`TOOLS_ENABLED_DEFAULT` ab ON (`.env` ke `PRABH_TOOLS_ON=0` se wapas OFF) aur
`TOOLS_AUTO_OFF_MINUTES = 0` (pehle 30). Ye setting `config_tools.py` me gayi
(tools ke constants ka apna ghar) - `config_desktop.py` 202 par cross kar raha tha.
Lock par TOOLS apne aap OFF **rehta** hai; awaaz se OFF/ALLOW ka koi raasta nahi.

### Step 4 - "Hlo Jarvis" pakadna

Grammar me `hlo jarvis`, `helo jarvis`, `hi jarvis`, `yo jarvis` bhi daale gaye
(English Vosk model Hinglish greeting sahi nahi chunta tha). Trigger ka faisla
waise bhi `WAKE_WORDS` se hota hai - sab ka aakhri shabd `jarvis` hai, is liye
trigger badalta nahi. VAD threshold **0.012 -> 0.010** (door se/dheere awaaz par
trigger nahi ho raha tha) aur pre-roll **0.4 -> 0.6 s** (pehla shabd kat raha tha).
Koi naya Hindi Vosk model (470 MB) nahi download kiya.

### Step 5 - tez jawab

1. **Ack skip** - naya `listen.peek_speech()`: wake ke baad 0.18 s suno; agar
   user bol hi raha hai to "Ji, boliye" **nahi** bolo (pehle hamari awaaz uske upar
   chadh jaati thi - isi liye use lagta tha "sun nahi pa raha"), aur wahi 0.18 s mic
   ka settle + pehli awaaz pakadne ka kaam kar deta hai (warm-up alag se nahi).
   Chunks wapas queue me daale jaate hain, warna `capture()` ko command milti hi
   nahi. `drain()` uske **pehle** hi chalta hai taaki wake shabd ki goonj na mile.
2. **Chuppi 1.2 s -> 0.9 s** (`PRABH_CMD_SILENCE`).
3. **Chhoti awaaz** - brain ka poora jawab HUD par rehta hai, par awaaz
   `config.VOICE_ANSWER_MAX_CHARS` (220) se zyada nahi boli jaati. Naya
   `voice/tts.py` ka `clip_answer()` **vaakya ke end** par katta hai (beech se nahi;
   ek hi lambe vaakya me `clip()` par hafta). 500 char ka playback hi 4.3 s tha.

Naye suite: `test_desktop_sleep.py`, `test_wake_ack.py` - **47 suite green**.

---

## Battery fix - 1 (4 Oct 2026) - Vosk khamoshi me nahi, chunk 30 ms sach me

User ki shikayat: "mic har waqt on rehta hai, battery jaldi drain hoti hai". Mic
hardware on rakhna **zaroori** hai (warna "Hlo Jarvis" sunai hi nahi dega), par
uske aage ka CPU bekaar chala rahta tha.

**Do asli wajah, dono code me:**

1. `wake/session.py` ka loop **har 30 ms chunk** recognizer ko deta tha, chahe koi
   na bol. VAD pehle se bol raha tha ya chup — sirf us faisla ki upaj thi hi nahi.
   Naya `wake/gate.py`: VAD + khamoshi ka hisaab + "Vosk ko ye chunk chahiye?"
   ka faisla (`listener.reset()` bhi usi jagah, purana behaviour waisa hi).
   Khamoshi me chunk recognizer tak **jaata hi nahi**. Mic ka stream kabhi band
   nahi hota — duty-cycle niyam mehfooz, sirf inference rukti hai. `.env` ke
   `PRABH_VOSK_GATE=0` se purana behaviour wapas (debug).
2. `wake/audio.py` ke `_pump` me `read()` ke baad **`sd.sleep(30ms)`** tha, jabki
   `InputStream.read()` blocking hai (pura chunk aane tak ruk jaata hai). Natija:
   chunk ~43 ms me aata tha. Do nuksan — CPU dobara jaagna, aur
   `utterance.capture()` chunk **ginti** par chalti hai, to "0.9 s chuppi" asli me
   1.4 s thi: jawab late, aur log ka ms jhootha (`82 chunk = 2460ms` jabki asli
   3.5 s lage). `sd.sleep()` hata diya — cadence ab sach me 30 ms.

**Napi napa (asli probe, app band, `%TEMP%\opencode` me — repo me nahi):**

| S | Kya | CPU (ek core par) |
|---|---|---|
| A | purana: mic + Vosk har chunk | **4.8%** |
| B | gate: sirf RMS, Vosk sirf awaaz par | **1.4%** |
| C | gate + `sd.sleep` hata (naya) | **0.9%** |
| D | sirf mic, Vosk bilkul nahi | 0.8% |

Chup kamre me 500 chunk me se **1** loud — yani gate 99.8% skip karta hai. App poora
(launcher + child + HUD + mic) **3.9% → 2.3%**; usme app ka apna core 1.46% hai
(`PRABH_WAKE=0` karke nikala — server/tray/psutil, `psutil` `interval=None` hai
is liye blocking nahi).

**Saath me:** `config.describe()` ab 5 hisse (`... stt=groq-whisper gate=on`) +
startup log par `vosk gate: ON (khamoshi me Vosk nahi)`. Naya suite
`tests/test_wake_gate.py` (pure — mic/thread/Vosk nahi) battery ka fix khud
pakadta hai. **45 suite green.** `session.py` 200 lines par tha, is liye gate ka
seam nayi file me gaya aur `_fire()` ab sirf `text` leta hai.

Baaki do shikayatein (tray icon + TOOLS default, aur "sun nahi pa rha / jawab
late") agli entries me.

---

## Phase 5 Step 3 (4 Oct 2026) - Windows login par auto-start

Har login par Jarvis khud chalega - double-click nahi. `HKCU\...\Run` me **ek**
value, is liye admin/UAC nahi chahiye.

**Value kya hai:** `D:\prabh\.venv\Scripts\pythonw.exe D:\prabh\desktop\launcher.py`

Wahi supervisor jo `start_prabh.bat` chalaata hai, bas `pythonw` se - login par
koi black console nahi aata. Crash phir bhi `logs/desktop.out` me padha jaata
hai (`launcher` ka `_tee`), matlab "crash chup mat ho" wala niyam bhaala gaya.

**Kaam**

| File | Kya |
|---|---|
| `desktop/autostart.py` (naya) | `value_name` / `pythonw` / `script` / `command` / `run_value` / `read` / `enabled` / `install` / `remove` / `status` / `main` |
| `config_desktop.py` | `AUTOSTART_NAME` ab `ASSISTANT_NAME` se banta hai (pehle `"Prabh"` hard-code tha - naam badle to bhool gaye the) + naya `AUTOSTART_SCRIPT` |
| `config.py` | `AUTOSTART_SCRIPT` re-export |
| `desktop/launcher.py` | (a) `_NO_WINDOW` constant **dead** tha - ab `Popen(creationflags=)` me use; (b) `BASE_DIR` khud `sys.path` me + `main()` me `os.chdir` (neeche padho) |
| `tests/test_desktop_autostart.py` (naya) | `FakeReg` (dict-based nakli `winreg`) - **asli registry kabhi nahi chhooti** |
| `tests/test_desktop_login.py` (naya) | Foreign-cwd ka **asli** pakkaura (launcher ko System32 par load karke) |

Ek hi raasta: value wahi supervisor chalaati hai jo haath se. Quote ka kaam
`subprocess.list2cmdline` karta hai (path me space ho to khud `"` lagata hai) -
haath se quote karna kisi aur jagah nahi.

**2. Sabse bada asli bug: Run key ka cwd `C:\Windows\System32` hota hai**

Pehle value `-m desktop.launcher` thi. Wo **chalti hi nahi** - par chup-chaap:

```
D:\prabh\.venv\Scripts\python.exe: Error while finding module specification
for 'desktop.launcher'
```

Wahan se `import config`/`desktop` fail hota hai, yaani har login par app mar
jaati - bina tray, bina HUD, bina crash message (pythonw me stdout hota hi
nahi). Do fix:

1. Value me `-m module` ki jagah **file ka path** (`desktop/launcher.py`).
2. `desktop/launcher.py` khud apna `BASE_DIR` `sys.path` me daalta hai
   (`import config` se **pehle**), aur `main()` me `os.chdir(config.BASE_DIR)`
   karta hai - **child** (`python -m desktop.app`) ko bhi sahi cwd chahiye,
   warna wahi ModuleNotFound mar jaata.

Yeh sirf "test me theek tha" se nahi pakda - asli Windows jaisa launch
`Start-Process ... -WorkingDirectory C:\Windows\System32` se chala kar proof
liya (us raaste ka bhi ek test bana: `tests/test_desktop_login.py`).

**3. Entry chalu kar di (owner ke "haan" par)**

- Pehle `reg export` backup: `backup\run-key-20261004-083516.reg` (1854 byte).
- Phir **sirf ek** value: `python -m desktop.autostart install`.
- Proof: Run key me value **6 → 7**, nayi value ka naam `Jarvis`. Baaki 6
  (OneDrive, Teams, Hermes x2, Microsoft.Lists, Edge) **shaant**.
- **Login jaisa launch pakda** (`pythonw.exe desktop\launcher.py`, cwd
  `C:\Windows\System32`): supervisor + dono child zinda, `GET /` = **200**,
  log me startup ki chaar line (`server up` / `tray started` / `HUD ready` /
  `wake: sun raha hai (jarvis)`), mic khula, `Ctrl+Alt+S` hotkey chalu, aur
  tray icon register (`Jarvis2239513293984SystemTrayIcon`).

**Teeno niyam jo is module me chipke hain**

1. `HKCU` = sirf is user ka.
2. Module me **koi module-level registry call nahi** - sirf `main()` se
   (`python -m desktop.autostart install`). Test me har function ka `reg`
   fake deta hai, is liye suite asli registry chhooti hi nahi.
3. Wapas karna ho to `python -m desktop.autostart remove` (ya Task Manager →
   Startup me `Jarvis` disable).

**44 suite green**, sab file `<=200` (`test_desktop_autostart.py` 222 lines ho
gaya tha, is liye `test_desktop_login.py` me launcher wala hissa alag kiya).

---

## Step 2 speed fix (3 Oct 2026) - wake 18.5 s se tez

Owner ne bola "bhot slow hai, placeholder bhi aa raha". Do alag baatein thin:

**1. Placeholder ka asli kaaran — stale process.** `GET /` raw
`__PRABH_ASSISTANT_NAME__` de raha tha. Code sahi tha; woh **purana** chal raha
process tha jisne `fill_html()` nahi jaana tha (Step 1 ke baad restart hi nahi
hua tha). Teeno PIDs band karke `start_prabh.bat` chala diya. Ab `GET /` =
`Jarvis HUD` + `J.A.R.V.I.S`, koi placeholder nahi. Ye wahi bug family hai jo
Phase 4 me bhi aayi thi (`localhost` vs `127.0.0.1`, three `Engine()`).

**2. Der kahan thi.** Brain tez tha (Groq 1.1-1.7 s). Log me der wake path me
thi:

```
TIME wake_command: TOTAL 18450ms | ack=3520ms warmup=1036ms capture=8088ms
```

Teen fix:

| Kya | Pehle | Ab |
|---|---|---|
| "Ji, boliye" ka TTS | har wake par ~1.4-1.8 s | `voice/tts.py` me cache - dusri baar **0 ms** |
| Warm-up | har baar 1 s dead wait | ack chalti hai, usi me mic settle (`deadline`) |
| Chuppi | 2.0 s | **1.2 s** (`PRABH_CMD_SILENCE`) |

- `voice/tts.py`: `speak_cached()` + `cache_clear()`, `_CACHE` (max 8, FIFO),
  `speak()` sirf `_speak_uncached()` ka wrapper. Hit par log: `tts cache hit`.
  Provider fail hone par **cache me kuch nahi** jata (warna app hamesha
  "nahi bola" repeat karegi).
- `wake/listen.py`: `warmup(mic, stop, deadline=None)` — deadline diya to jitna
  poora hua utna hi wait, warna poora `COMMAND_WARMUP_SECONDS`.
- `wake/command.py`: `settled_by = stage() + WARMUP` **ack se pehle** banta hai,
  is liye ack ki 2 s me warm-up poora ho jata hai aur wo 1 s har baar bachta hai.
- `desktop/playback.py` 205 lines ho gaya -> **split**: naya
  `desktop/playback_cli.py` (`--list`/`--say` + `devices()`). Asli decode/play/
  `say()` wahi rahe. CLI ab `-m desktop.playback_cli` se (teeno test + doc update).
- Naye suite: `tests/test_tts_cache.py` (cache hit/miss/bounded/fail-not-cached),
  `tests/test_speed_fix.py` (warm-up deadline ka sach + 1.2 s + env override).
  **42 suite green**, sab file `<=200`.
- Ek asli galti: nayi `speak()` me `return _speak_uncached(...)` likh diya tha
  bina `await` ke — `test_voice_tts.py` ne `cannot unpack non-iterable coroutine
  object` pakda. Split karte waqt bhi do test fudge hue the (import stub +
  `devices()` ab `playback_cli` me hai, dono test me badle gaye).

---

## Step 1 (3 Oct 2026) - naam "Sunday" -> "Jarvis"

Sirf **naam** badla, **id nahi**. `config.SUNDAY_ONLY`, `PRABH_SUNDAY_ONLY`,
`ELEVENLABS_VOICE_SUNDAY` aur `CARTESIA_VOICE_SUNDAY` aise hi hain - `.env`
ki keys aur voice id toot jaati agar id bhi rename karte.

**Wake word:** ab `hello jarvis`, `hey jarvis`, `jarvis` (+ `[unk]`) sunta hai.
Purane 5 "sunday" shabd `config_name.LEGACY_WAKE_PHRASES` me chhupaye hain,
**default band**; `.env` me `PRABH_WAKE_LEGACY=1` se wapas aa jaate hain.

**Ek hi raasta:** naya `config_name.py` (`ASSISTANT_NAME`/`DISPLAY_NAME` +
wake shabd). UI ka naam `index.html` ke placeholder se aata hai jo
`server/app.py` ke naye **pure** `fill_html()` se bharta hai (test isi ko
chala-ta hai, asli server nahi); JS usi ko `meta[name="prabh-name"]` se
padhta hai; tray tooltip aur `Jarvis HUD.lnk` `ASSISTANT_NAME` se bante hain.

**Do asli galti pakdi:**
1. `ui/app.js` me `currentMode = ev.data.mode.toUpperCase()` — wahi value
   `voice.speak()` me jaati thi, aur `voice_for(provider, "SUNDAY")` match hi
   nahi karta tha (default mode ka provider chup-chaap chhoot jaata). Ab
   `currentMode` **lowercase id** hai, display ke liye alag `LABEL`.
2. Persona file ka naam `jarvis.txt` hua, is liye `PERSONA_FILES` map bana —
   warna `persona_for("sunday")` File-not-found deta.

**Test:** naya `tests/test_name_jarvis.py` (14 check) - wake phrase variants +
near-miss (`jarvisly`, `sunay` nahi), grammar, legacy off/on, persona, tray,
`fill_html()`, aur UI grep. Purane 9 test file update hue (fake listener naye
shabd par trigger hi nahi karta, warna chup-chaap fail hote).

Docs sync: `README.md`, `VOICE.md`, `TOOLS.md`, `TESTS.md`, `CLAUDE.md`,
`AGENTS.md` (current rules; §8.1 + change history jaise ki taisa).

---

Step 2a ne command **kaat** li, 2b ne awaaz **baja** di. Ab dono jury/judge se
jud gaye: "Sunday" ke baad Sunday sunta hai, aapki baat sunta hai, brain se
jawab paata hai, HUD par dikhata hai aur **awaaz se** bolta hai.

### Naye file

- **`wake/listen.py`** (mic wala hissa, policy nahi) - `stop()`/`reset()` ke saath
  module-level `_STOP`, aur chaar kaam: `drain()` (purana queue phenko),
  `warmup()` (mic khulne ka wait), `capture()` (chunks), `to_text()` (WAV bana kar
  Groq STT). **Chaaron par stop event** — app band ho raha ho to turant laut jaate
  hain, TTS aaj bhi bajti hai ye check `worker.stop()` par pakda gaya.
- **`wake/command.py`** (flow) - `allowed()` guard → `speak("Ji, boliye")` →
  drain + warm-up → capture → STT → brain → awaaz. Brain ke liye **shared
  `server.state.ENGINE`** (naya Engine nahi), har event par `via="voice"`.

### Flow ka faisla

- **`Session._fire()` ab `on_wake(phrase, mic, stop)` deta hai**, teeno, aur
  **synchronously** wake thread par. Isi wajah se teen kaam ek saath mile:
  1. mic/stop-event ka **sirf wahi raasta** bana (kahin aur se `MicSource` ya
     `Session` private access nahi).
  2. Command poore chal jaane tak wake **rukega** — nahi to Sunday ki apni awaaz
     par dobara trigger hota.
  3. `worker.stop()` ka join 3 s hai, par capture+TTS 8 s+ lag sakta hai — is liye
     mic ke chaaron kaam aur `speak()` dono `stop` event maangte hain.
- **Pause ke do alag kaam:** `set_paused()` = tray ka MUTE (user ka faisla),
  `hold_for_command()` = command ka temporary hold. Beech me MUTE aa gaya to
  `_HELD` clear ho jaata hai — **MUTE haar nahi maarta**. Naya public
  `worker.paused()`/`Session.paused()` (test + UI dono ke liye).
- **Bole hue to aawaaz dobara trigger na ho:** `run()` ke `finally` me pehle mic
  queue `drain()`, **tabhi** hold chhoda. Ulta karne par `Session._loop` TTS ko
  `sunday` samajh kar phir uth jaata.
- **`via="voice"`** - wake se aaye **har** engine event par. `ui/app.js` is par
  browser TTS skip karta hai ( warna do awaaz), par **type** kiye message ka
  raasta badalta nahi - waise hi bolte hain.

### Naye config

`COMMAND_END_SILENCE_SECONDS = 2.0` (`.env` se `PRABH_CMD_SILENCE` se badal sakta
hai), `COMMAND_MAX_SECONDS = 30` (Step 2a ka 8 s bahut chhota tha), aur teen bolne
wali line: `NOT_UNDERSTOOD` (suna hi nahi), `BRAIN_FAILED` (brain/net fail),
`CONFIRM_VOICE` (card par "confirm kijiye").

### Safety

- **Awaaz se ALLOW kabhi nahi.** Mute ya PC lock par command **bilkul nahi**
  chalta - na record, na awaaz, na brain (`desktop/callbacks.py` ka `allowed()`
  callback; `wake/` ko `desktop/` ka import nahi karna pada).
- ASK par sirf HUD card khulta hai aur "confirm kijiye" bolta hai. Faisla sirf
  screen ke button se - `wake/command.py` me `keeper.approve/deny/wait` ka koi
  bhi raasta nahi, sirf `gatekeeper.audit.mask()` (text ke masking ke liye).
- **Recording kabhi disk par nahi** - memory byte buffer, seedha Groq STT. Wake
  word detection poora offline (Vosk).

### Stage time

`core/timing.py` ke `Stopwatch` se ek line: `ack / warmup / capture / stt /
brain / speak`. `tts` aur `play` ka apna time `voice/tts.py` aur
`desktop/playback.py` alag log karte hain - `playback.say()` ek hi raasta hai,
is liye usko do hisson me nahi toda.

### Test

- **Teen naye suite, pura fake** (`tests/wakecmdhelp.py` ke fakes):
  - `test_wake_command.py` (139) - poora flow: ack -> capture -> STT -> brain -> awaaz,
    mute/lock par kuch nahi, not-heard / no-text, `via="voice"`, stage timing, `ui/app.js`.
  - `test_wake_brain.py` (140) - brain tak ka raasta: brain ne kuch nahi diya, saare
    provider fail, brain crash, ASK card par awaaz se allow nahi, confirm line ki
    **ordering**.
  - `test_wake_listen.py` (85) - `listen.py` ke chaar kaam + pause: drain/warmup, stop,
    hold-then-release, MUTE absorb.
  Koi **asli** API, mic ya speaker nahi. **36 → 39 suite green.** Teenon file
  200-line niyam me hain (fakes `wakecmdhelp.py` me jaake dono bhi).
- **Paanch asli galti test ne hi pakdi:**
  1. Source-scan docstring ke text se **false positive** de raha tha (file me
     likha tha "approve yahan nahi hai"). Ab **AST** se check — sirf asli
     `from gatekeeper... import ...` lines gin-te hain, docstring nahi.
  2. `FakeMic` ki queue sirf **400** chunk rakh sakti hai, is liye 30 s wala
     "max par kaatna" test preload nahi ho sakta tha (`queue.Full`). Ab
     `COMMAND_MAX_SECONDS=1.5` karke wahi niyam test hota hai.
  3. Test me worker **shuru** nahi tha, is liye `state()` "off" tha - do check
     chup-chaap False hue. Ab pause ka faisla naye `paused()` se hota hai.
  4. **ASK par "confirm kijiye" 60 second BAAD boli jaati thi.** `run()` us line ko
     `ask_brain()` ke **return ke baad** bolta tha, par engine confirm event ke baad
     `keeper.wait()` par **ruk jaata hai** - to user ko card dikhta hi tha, awaaz 60 s
     baad aati. Ab `ask_brain()` generator ko aage badhane se **pehle** bolta hai, aur
     ek test jaanbujh kar block hone wala generator banakar **ordering prove** karta hai.
  5. **Brain fail par awaaz saare provider ke technical reasons padh leti thi** -
     `pool.ask()` "Abhi koi brain jawab nahi de paya. Ye reasons mila: - groq 429 -
     gemini timeout ..." bhejta hai. Ab engine log event me `data.brain` bhejta hai;
     `ask_brain()` usse `config.BRAIN_FAILED` bolta hai. **HUD par reasons waise hi
     dikhte hain** (wo theek hai), sirf awaaz chhoti line hai.
- `test_wake_utterance.py` ke window ab asli (end-silence 2.0 s = 67 chunk,
  max 30 s), purane 0.9 s/8 s wale numbers hataye.

### Do aur galti poori suite se nikal kar

Poori 39-file suite pehli baar chalao to **do** suite fail hue — dono Step 2c se
bhaari nahi, dono **purane** test the:

1. **`test_wake_loop.py` — trigger chup-chaap gaya.** Step 2c ne `on_wake` ka
   signature badla: ab `on_wake(phrase, mic, stop)` teen args leta hai. Test ka
   fake callback `heard.append` (ek arg) tha → `TypeError` → `Session._fire()`
   ke `except Exception` ne pakad liya → **koi crash log nahi, koi trigger nahi**.
   Test pass hota tha jab tak `wakes() == 1` hi dekhta; `heard` khaali reh gaya.
   Doosri galti: pehla fix **module level** helper banaya tha jo local `heard`
   ko dekh nahi sakta tha (`NameError`, isi `except` me gaya) — yahi trap
   `AGENTS.md` me pehle bhi likha hai, phir bhi ho gaya. Ab closure `test_worker_loop()`
   ke **andar** hai.
2. **`test_desktop_single.py` — test ko bahar ki duniya par depend.** `acquire()`
   andar se `diagnose()` call karta hai, jo **asli** HTTP se 8000 par poochta hai.
   Test "CHAL raha hai" shabd maangta tha, jo tabhi aata hai jab Sunday ka server
   sach me chala ho. Matlab suite **environment** par depend karti thi — app band
   ho to fail, app chalu ho to pass. Ab sirf wo check hai jo **guarantee** hai
   (live process lock pakde hai to "stale" kabhi nahi bola jaata + apna PID
   bataya) — is file ke docstring ke vaade ka khilaf bhi nahi. Wording wahi
   fake-probe test (`test_diagnose_message`) me pehle se cover hai.
- `tests/test_desktop.py` ki 200-line list me `wake/listen.py` bhi gaya.

### Naye pakkaurey (AGENTS.md)

Section **3.5** (voice privacy) aur **3.6** (Step 2c ke 7 niyam): mic ka ek
raasta, pause ka do matlab, `via="voice"`, awaaz se ALLOW nahi, stage time ka
ek line, MUTE/lock par kuch nahi.

---

## Phase 5 Step 2 (3 Oct 2026) - wake ke baad ka command + speaker

Step 1 sirf **sunta** tha. Ab mic se command uthane ka raasta bana, aur TTS ki
awaaz bajane ka bhi. Brain tak pohanchna agli sub-step hai (`wake/command.py`).

### 2a - command capture (commit `5e9a2fc`)

- **Naye file:** `wake/utterance.py` (mic se command, VAD se sahi waqt band) -
  `wake/wav.py` (16 kHz mono PCM -> WAV, Groq ko bhejne ke liye).
- **Teen window:** pre-roll 0.4 s ("Sunday, WhatsApp kholo" ek saath bole to
  "WhatsApp" bhi pakde), end-silence 0.9 s, max 8 s, wait 5 s.
- **Do asli bug:** (1) queue khali rahe to capture **infinite wait** karta tha -
  ab `empty * 0.2 >= COMMAND_WAIT_SECONDS` par laut jaata hai. (2) min-duration
  ab **awaaz** gin ta hai, aakhir ki khamoshi ko "0.6 s bola" na samjhe.
- **`wake/session.py` ka mic-death fix:** pehla `chunks.get(timeout=0.5)` wala
  `queue.Empty` par loop chala gaya tha aur `_end()` chup-chaap `off` bol deta
  tha. Ab `_end()` sirf `_stop` se `off` decide karta hai - loop khud khatam
  hua matlab `error`.

### 2b - speaker (commit `d3a5f7a`)

- **Naya file:** `desktop/playback.py` - TTS bytes (mp3/wav) -> `miniaudio`
  16-bit PCM -> `sounddevice`. Awaaz hamesha `voice/tts.py` se (`say()` sirf
  bajata hai), thread se `asyncio.run`.
- **Naye config:** `OUTPUT_DEVICE` (default Windows speaker), `OUTPUT_RATE`
  (32 kHz mono), `PLAYBACK_TIMEOUT_SECONDS` (45 s).
- **Do asli galti probe/fake se pakdi gayi:**
  1. `miniaudio.decode_file` sirf **filename** leta hai. Bytes dene par wo poora
     audio buffer apne `FileNotFoundError` message me daal deta hai - terminal
     par MB ka binary dump. Sirf `decode()` (memory buffer) use hota hai.
  2. `sd.query_devices(kind="output")` **list nahi** deta - sirf default output
     device ka ek dict (sounddevice 0.5.6). List ke liye `query_devices()`
     bina argument + `max_output_channels > 0` filter.
- **Test me asli speaker kabhi nahi bajti:** `miniaudio` + `sounddevice` ke fake
  `tests/desktophelp.py` me `install_audio()` se `sys.modules` me. Asli check:
  `python -m desktop.playback_cli --list` aur `--say "Ji, boliye"`.
- **Test:** 30 -> **32 suite green**. Naye suite `test_desktop_playback.py`
  (decode + play + device list) aur `test_desktop_play_say.py` (TTS + har error
  par `0`, crash nahi). Test me `int16` buffer `bytes()` se nahi, `np.asarray`
  se padha jaata hai.
- **Do chhote pakkaure:** `tests/test_wake.py` dono model path badal kar sirf ek
  wapas karta tha (`WAKE_MODEL_ALT_DIR` hamesha ke liye galat reh jaata) -
  ab dono wapas + 2 naya check. `wake/__init__.py` ka docstring ab Step 2 ke
  asli haal se match karta hai.
- **Test split (isi din):** `tests/test_desktop.py` 390 lines tha - 200-line
  niyam tod raha tha. 4 file me toda: `test_desktop.py` (160, shell + hygiene),
  `test_desktop_single.py` (163, single instance + stale PID/lock),
  `test_desktop_guard.py` (96, TOOLS auto-off + tray guard) aur naya
  `test_wake_worker.py` (49, wake wiring). **Ek asli galti** split karte hi pakdi:
  `Ok` / `boom` helper naye function me local reh gaye the, to `diagnose()` ke 2
  check chup-chaap `False` hue. Isi liye ab helper **module level** par rakhne ka
  pakkaura banaya. Hygiene check `<200` se **`<=200`** hua aur ab har
  `tests/test_*.py` par lagta hai - koi badi test file chup-chaap nahi reh sakti.
  **32 -> 36 suite green.**

---

## Phase 5 Step 1 (2 Oct 2026) - wake word "Sunday" (asli Vosk, offline)

Shell (Step 3a) poora tha, wake sirf **stub** tha (`worker.READY = False`). Ab app
shuru hote hi mic khul kar **"Sunday"** sunta hai - trigger milte hi HUD khul
jaata hai. Awaaz 100% offline (Vosk), kuch bahar nahi jaata.

- **Do alag STT, jaan-boojh kar:** wake word ke liye **Vosk**
  (`models/vosk-model-small-en-us-0.15`, grammar me sirf 5 shabd), aur Hinglish
  command ke liye **Groq Whisper** (`voice/stt.py`, Step 2 me lagega). Isi wajah se
  470 MB ka Hindi model download karne ki zarurat hi nahi padi.
- **Naye file:** `config_wake.py` (constants; `config.py` re-export karta hai) -
  `wake/model.py` (load + cache + saaf error) - `wake/detect.py` (Vosk JSON ->
  text) - `wake/phrase.py` (pure trigger) - `wake/audio.py` (mic ka **ek** owner
  + energy VAD + PCM helpers) - `wake/session.py` (asli loop) - `wake/worker.py`
  (module-level ek hi worker).
- **Desktop wiring:** startup ki 4th line ab `wake: sun raha hai (sunday)` (ya
  wajah: mic band / model missing). Wake chalu ho to mic ka pill + tray icon
  `listening`. Tray ka **Mic Mute** worker ko pause karta hai (`set_paused`),
  Win+L par wake chalta rehta hai (AGENTS.md ka niyam).
- **Split kiya (200-line niyam):** `worker.py` 212 line tha -> `session.py` + patla
  `worker.py`; `desktop/app.py` 221 -> naya `desktop/callbacks.py` (chaaron
  callback: lock / tools / wake / hotkey) aur `startup.say_hud()` /
  `say_wake()`; `test_wake.py` 216 -> `test_wake.py` + `test_wake_loop.py`.
- **Test:** 28 -> **30 suite green**. Naya `tests/wakehelp.py` (fake recognizer /
  listener / mic + `loud()`/`quiet()` PCM). Wake suite me **asli mic, Vosk model
  aur sounddevice kabhi nahi** chalti - loop bhi fake se, `before = worker.wakes()`
  pakad kar (count poore app ka hota hai).
- **Do asli bug test me pakde:** (1) `phrase.FILLER` me `"[unk]"` likha tha par
  `normalize()` bracket hata deta hai - asli filler `"unk"` hai; (2) purana
  `test_desktop.py` asli `worker.start()` chala raha tha, yaani test me **asli
  mic khul rahi thi** - ab fake se.
- **GitHub:** private repo `github.com/rachithunyawrr/jarvis2.0` bana, poora history
  push. Remote URL me token **nahi** - ek baar ke liye temp askpass script use
  hui aur delete ho gayi. (Dono PAT ab chat me hain - kaam hote hi revoke karna.)

**Abhi kya nahi hota (jaan-boojh kar):** wake ke baad command **nahi** sunta, "Ji,
boliye" **nahi** bolta, sunke tool **nahi** chalta - teeno Step 2.

## Fix round 4 (2 Oct 2026) — tray icon promote + shortcut + global hotkey

User ka sawaal: Windows 11 ki "Other system tray icons" list me "Sunday" nahi
mila. **User ka andaza sahi tha** — list exe ke naam se bhakti hai.

- **Vichar pakka hua (live proof):** venv ka `python.exe` sirf ek redirector hai
  — asli process `D:\Python312\python.exe` chalata hai. `Win32_Process` me dono
  dikhe: `D:\prabh\.venv\Scripts\python.exe -m desktop.app` **aur**
  `D:\Python312\python.exe -m desktop.app`. Tray ka window class
  `Sunday2587022232368SystemTrayIcon` **base** python ke PID par mila.
  Is liye Settings me iska naam **"python"** dikhega, "Sunday" kabhi nahi.
- `NotifyIconSettings` me `D:\Python312\python.exe` ki **do** entry thi. Pehchaan
  ka pakka raasta: ek ka `InitialTooltip` = `MyJarvis.Desktop` (purana JARVIS,
  jo chalta nahi — naya entry ban hi nahi hua jab app start hua), dusri khali.
  **Prabh wali = `13638010186279013602`**, sirf usi me `IsPromoted=1` kiya.
- Backup: `backup/notifyicon-python-20261002-194804.reg` (9764 byte, `reg export`).
  Wapas chahiye to wahi `.reg` `reg import`.
- **Diff proof:** shuru aur baad me 21 entry, sirf **ek** value badli. Baaki 20
  (Teams, OneDrive, Hermes, Chrome, Edge, WhatsApp…) bilkul chhed nahi gaye.
  Baad me `SHChangeNotify(SHCNE_ASSOCCHANGED)` bheja — sign-out ki zarurat nahi.
- **Ek kaam bacha user ke haath:** taskbar dekhna ki icon ab seedha dikhta hai ya
  nahi. Na dikhe to batao — dusri entry pe flip kar denge (backup se wapas bhi
  aa sakta hai). `InitialTooltip` khali hone ki wajah ye hai ki pystray title
  `NIM_ADD` ke baad hi lagata hai.

### Naya code — tray ke alawa do raasta

| File | Kaam |
|---|---|
| `desktop/hotkey.py` | Global hotkey, sirf `ctypes` + `RegisterHotKey` (koi package nahi) |
| `desktop/open_hud.py` | Shortcut aur hotkey dono ka **ek hi** raasta: server zinda → HUD khulo, warna message box |
| `desktop/shortcut.py` + `hud_shortcut.ps1` | Desktop ka `Sunday HUD.lnk` banao / hatao (`WScript.Shell`) |
| `desktop/app.py` | Hotkey `start()`/`stop()`, `_on_hotkey()` |
| `desktop/tray.py` | Menu me ek disabled line — `ya phir Ctrl+Alt+S` (warna pata hi nahi chalta) |
| `config_desktop.py` / `config.py` | `HUD_HOTKEY` (`.env` se badalta hai), `HUD_SHORTCUT_NAME` |

- `parse()` pure hai: **ek modifier + ek key**. Galat spec par `(0,0)` →
  `Hotkey.start()` `False`, app safe rehti hai. `PeekMessage` + chhota wait
  (GetMessage block karta hai, `stop()` turant nahi maanta).
- `PeekMessageW.argtypes` zaroori tha — warna 64-bit par `lParam` kat jaata hai.
- `.ps1` alag file me taaki PowerShell quoting na badhe. `shell=False`, har jagah.
- Test me **asli** Desktop/registry/`RegisterHotKey` kabhi nahi chalta —
  `shortcut.command()` ki list + `Hotkey(api=StubApi())`.

### ⚠️ Ek asli bug jo test se pakda (aur pehle chhup chhupa tha)

Pehle `start()` `RegisterHotKey` **caller (main) thread** par call karta tha, aur
message pump **doosre** thread par chalta tha. `hWnd=NULL` hone ki wajah se
`WM_HOTKEY` usi thread ki queue me aata hai jisne register kiya — yaani key
**kabhi trigger hi nahi hoti thi**, sirf `hotkey chalu` log dikhta tha.

- Fix: `register()` + `pump()` + `unregister()` **ek hi thread** par. `start()`
  ab `_live` event se wait karta hai ki Windows ne haan bola ya nahi.
- Naya pakkaura: `tests/test_desktop_hotkey.py` stub me `threading.get_ident()`
  record karta hai aur teeno ka thread compare karta hai.
- **Test khud ne sach me bug pakda** — purana code wapas daal ke run kiya:
  `register aur pump ek hi thread` FAIL hua. Fix ke saath 28 suite green.
- Pehle wala stub galat pass de raha tha kyunki uska `pump()` khud `on_press()`
  bana deta tha — asli `PeekMessage` ki zaroorat hi nahi padi.

### Live verify

- `RegisterHotKey` ne `hotkey chalu: Ctrl+Alt+S` log kiya (yahi tab log hota hai
  jab Windows ne haan bola).
- Shortcut ka payload Edge `--app` window khola `D:\prabh\data\hud-profile` par,
  aur server-band par message box aaya.
- Synthetic keystroke (`SendInput`) se trigger nahi hua — struct theek tha par
  ye shell non-interactive window station me hai. **Asli keyboard se ek press
  user ko karna hai**, tab `HOTKEY HIT` log aayega.
- Registry proof: `IsPromoted=1` app ke **restart ke baad bhi** bacha hai
  (21 entry, wahi key hash). Backup se live ka diff = sirf ek nayi value.

### Ek naya pakkaura (section 8.2)

- **Koi bhi tray/registry ka naam ya value hard-code mat karo.** Windows tray entry
  ka key ek hash hota hai, aur ek hi exe ki **do** entry ho sakti hai. Pehchaan
  `InitialTooltip` ya live process se karo, aur har change se pehle `reg export`.
  Poora yahan: `AGENTS.md` 8.2.

---

## PC wale kaam + fix round 3 ka record (2 Oct 2026 raat)

Code ka poora record upar hai. Ye sirf **project ke bahar** wale kaam hain — detail
`AGENTS.md` section **8.1** me.

- **Purana JARVIS auto-start hata diya** — `HKCU\Run` se `electron.app.Electron` value
  delete, backup `D:\prabh\backup\jarvis-autostart-20261002-141601.reg` (456 byte, UTF-16LE).
  `D:\jarvis` folder/exe chhua nahi, koi electron process nahi tha. Baaki 7 Run values shaant.
- **`D:\SystemConfig` ki poori jaanch** — chain, file dates (14-Sep-2026 shaam), "internet par
  kuch nahi bhejta" ka proof, startup-judne ka tareeka, aur chhupaye hue secrets ka record.
  **Koi badlav nahi kiya** — user ke "haan" ka wait. Reversible plan bhi likha hai.
- **Tray icon na dikhne ki asli wajah** — pystray nahi, Windows overflow. `NotifyIconSettings`
  me 22 icon me se sirf 1 `IsPromoted=1`; baaki 21 `^` chevron me. Icon register hua tha, bas
  dikha nahi. User ko `^` → right-click → "Always show icons" batana hai.
- **`localhost` vs `127.0.0.1`** — HUD hamesha `http://127.0.0.1:8000`, `localhost` se token reject.
- **Fix round 3 live verify** — naya code **asli** stale PID file saaf ki:
  `15:41:21 | WARNING | single | stale pid file hata di: D:\prabh\data\prabh.pid (pid=19584)`.
  `start_prabh.bat` dobara chalane par naya saaf message + exit 3.
- **Jahan chhoda** — app band, port khaali, pid file saaf, lock free, git clean. Agla step
  user ka: double-click → `^` me icon → "Always show icons". Iske baad Phase 5 Step 1 (Vosk).

---

## Phase 5 Step 3a fix round 3 (2 Oct 2026) — stale-lock message + tray guard

User ne live par do shikaayat ki: (1) dobara click karne par sirf "pehle se chal raha hai
(pid=...)" aata tha, kuch samajh nahi aata tha; (2) tray icon overflow me chhupne par lagta
tha ki app shuru hi nahi hua.

**1. "Chal raha hai" ab proof par hai, sirf lock par nahi**

- `desktop/single.py` me `pid_alive(pid, probe=None)` (Windows `OpenProcess` +
  `PROCESS_QUERY_LIMITED_INFORMATION`, doosre platform par `os.kill`) aur
  `http_alive(origin, opener=None)` (`GET /` ka status 200?) — dono probe injectable hain.
- `Single.diagnose(pid_probe=None, http_check=None)` 4 haal alag-alag bolta hai:
  - PID zinda + `GET /` 200 → "pehle se CHAL raha hai (pid=...)"
  - PID zinda par 200 nahi → "app atki hai, Task Manager se band karo"
  - PID murda par 200 → "port 8000 kisi aur ka hai, ye lock stale nahi"
  - dono murda → "lock stale hai, ye instance apne aap lock pakad lega"
- `os.kill(pid, 0)` jaan-boojh kar **nahi** likha — CPython isay `TerminateProcess` bana
  sakta hai. Ye baat `AGENTS.md` me pakkaari gayi hai.
- `_clean_stale_pid()` — lock milne ke baad mar ke bache `.pid` file apne aap hat jaati hai.
  Windows par `msvcrt` lock marne par khud release hota hai, is liye asli stale *lock* rare
  hai, stale `.pid` file hi common hai.
- `desktop/app.py` ab ye message **console par bhi** bolta hai (`print(..., flush=True)`),
  kyunki double-click karne wala user log nahi padhta.

Live verify (asli app ke against): `owner_pid = 19584` →
*"Sunday pehle se CHAL raha hai (pid=19584). Usi tray icon se Open HUD karo, ya Quit dabao."*
aur `start_prabh.bat` dobara chalane par wahi message + exit 3.

**2. Bina tray ke app ab chup-chaap nahi chalta**

- `desktop/tray.py` me `retry_start(tray, attempts=3, delay=1.5, sleep=None)` — alag
  function is liye ki test me `sleep` daal kar bina wait check ho jaaye.
- 3 koshish ke baad bhi icon na bane to `config.EXIT_NO_TRAY = 4` se saaf exit; launcher
  is par alag se bolta hai *"Wajah: tray icon nahi bana..."*. Bina tray ke app chalta rahe to
  usse band karne ka koi raasta hi nahi hota — is liye ye pehle se theek nahi tha.
- `run()` me `_start_tray()` ke baad `self._stop.is_set()` check — warna app server chalu
  karke aage badh jaata tha.

**3. Chhoti split**

- `desktop/actions.py` naya — tray ke 5 button ka faisla (`app.py` se nikaala, taaki
  `app.py` 200 line ke andar rahe).

**Test** — `tests/test_desktop.py` me 3 naye block: `STALE LOCK DIAGNOSE` (helper + 4
combination) · `STALE PID SELF-HEAL` (asli temp-dir end-to-end) · `TRAY GUARD` (retry count,
exit code, source check). Sab probe injectable — koi asli process/socket nahi chhua gaya.
**26 suite green.**

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

**Asli app chala kar 4 bug pakde** (sirf test se nahi):

1. `app.py` me `NameError: open_hud_at_start` — app shuru hi hote hue gir raha tha
   (supervisor 5 baar restart kar raha tha). Test ise miss karta tha kyunki koi
   test `run()` tak nahi jaata tha.
2. `single.py` PID hamesha `0` dikha raha tha — lock wali file ka pehla byte locked
   hone par dusra process use **padh hi nahi sakta** (`ERROR_SHARING_VIOLATION`).
   Ab PID alag `data/prabh.pid` me.
3. HUD ka DESKTOP pill `DESKTOP …` hi reh raha tha — state WebSocket se pehle set
   ho chuki thi, is liye `publish()` ka event kisi ko nahi mila. Ab `Hub.welcome()`
   hook: naye client ko turant snapshot milta hai.
4. TOOLS toggle HUD se karne par tray icon nahi badalta tha (`/tools/toggle` seedha
   `keeper` ko bulata tha). Ab `Limiter.set_on_change()` hook hai — TOOLS kahin se
   bhi badle, `STATE` ek hi raaste se update hota hai (auto-off timer bhi).

**Manual check (asli app):** `GET /` 200 · token meta + DESKTOP pill present ·
`/hud/stats` bina token 401 · doosra instance exit 3 (PID sahit) ·
Edge `--app` sach me khula · tray ready · koi crash nahi (`logs/desktop.out` khali).

**Abhi nahi hua (jaan-boojh kar)** — wake word (Step 1), VAD/command flow (Step 2),
aur **auto-start**. Registry me koi entry nahi likhi gayi hai.

## Fix round 2 — `start_prabh.bat` launch hi nahi ho raha tha (2 Oct 2026)

User ne bataya: double-click par na tray icon, na python process — sirf
"Press any key to continue". Ye **test se nahi, bilkul fresh shuruat se** pakda
gaya (purane code par koi test nahi tha).

**Asli wajah — ek `echo` line par raw bracket.** `cmd` ka `if not exist (...)`
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
huyin — `exit /b 1` unse pehle chala gaya.

**5 fix:**

1. `start_prabh.bat` — bracket block hata kar `goto novenv` label; poori file
   **CRLF** (pehle 19 LF / 0 CRLF — Windows `.bat` ko CRLF chahiye); ASCII only.
2. `desktop/launcher.py` — child ka stdout ab **console + `logs/desktop.out`
   dono** me jaata hai (`_tee`). Har crash par console par `CRASH #n/limit`,
   exit code, backoff aur crash ki **wajah** bhi print hoti hai (`_console`).
   Pehle crash sirf `log.error` me thi — user ko console par kuch nahi dikhta
   tha, matlab app "chup-chaap mar" sakta tha.
3. **Startup ki 4 line ek jagah** — `server up` / `tray started` /
   `HUD ready` / `wake: stub`. Shabd `config_desktop.STARTUP_*` me, bolta sirf
   `desktop/app.py` (naya `desktop/startup.py` helper: `say()` + `await_http()`).
   Console par **aur** `logs/prabh.log` dono me. `HUD ready` ab sach me
   `GET /` ka 200 check karta hai — nahi mila to `HUD ready: FAILED - <wajah>`,
   chup-chaap nahi. `server/app.py` ka duplicate log hata diya.
4. `log_setup.py` — `ascii_text()` + `AsciiFormatter`; file `encoding="ascii"`.
   Pehle `wake word ... — mic nahi khula` log me `??` ban kar aata tha (console
   `cp1252` hai). Ab em-dash `-`, arrow `->`, baaki Unicode hata deta hai.
5. `tests/test_bat.py` (naya) — CRLF check, ASCII check, **raw bracket rule**
   (bracket sirf `if`/`for`/`else` line par), aur asli pakka test: file ki copy
   me python line ki jagah `echo` daal kar `cmd` se chala kar dekho ki line
   sach me pahunchti hai ya nahi. Buggy file par ye test fail hota hai
   (sirf "Press any key to continue" aata hai) — manually confirm kiya.

**Live (asli double-click jaisa, `cmd /c start_prabh.bat`):**

```
server up: http://127.0.0.1:8000
tray started: Sunday
HUD ready: stats pump + 6 quick buttons
wake: stub: Step 1 me aayega - mic nahi khula
```

Tray icon window mila (`Sunday...SystemTrayIcon`, pid 13668), `GET /` = 200.

**Purana JARVIS auto-start (sirf bataya, chhua nahi):**
`HKCU\...\Run` me `electron.app.Electron` →
`D:\jarvis\desktop\node_modules\electron\dist\electron.exe D:\jarvis\desktop --hidden`.
`D:\jarvis` abhi bhi maujood hai. Startup folder me Jarvis nahi — sirf
`start_local_hidden.vbs` (VoiceMemories AI ka `node local_host.js`) aur
`SystemConfig.bat` (`D:\SystemConfig\run-all.ps1`). Koi scheduled task nahi.

**26 suite green.**

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

test+feat(overnight): 7 branch, 75 suite — test log alag, alarm, tail guard,
permissions v2, tez jawab, hot window, HUD stats fix (KAAM 0-6)

Ek raat ka kaam, har kaam apni branch par (chain), koi merge/push nahi.

KAAM 0 (fix/stt-speed, 695e5c5) — test ab logs/prabh.log me NAHI likhte
  (tests/logsafe.py + PRABH_LOG_DIR). Wajah: S-1 audit me nakli RMS 0.129 asli
  mic ka data samajh aaya tha. 64 test file me import, puri suite pehle
  +17974 byte, ab +0.

KAAM 1 (feat/wake-alarm, 84842a0) — subah 7 baje ka alarm. tools/alarm_loop.py
  + alarm_audio.py + wake_alarm.py + alarm_task.py + alarm.py (DEFAULT OFF).
  Do Task Scheduler task ban chuke hain (07:00 + 07:10 backup, dono Ready).
  teen asli galti: Register-ScheduledTask par -ErrorAction Stop na hone se "OK"
  jhooth bola; [datetime]::new 5-arg overload exist hi nahi karta; ps_when()
  minute hataa raha tha (07:10 ka task 07:00 par bana).

KAAM 2 (fix/self-hearing, 5bb76cc) — tail guard 0.4 s. drain() 400 chunk
  (~12 s) bounded hai par jawab 18 s — apni awaaz queue me bachi rehti thi,
  take_fresh() sirf ek chunk bachata tha. maybe() me bhi suppressing() check
  (gate.on_flush gate thread se bypass kar sakta tha).

KAAM 3 (fix/permissions-v2, f6e28f8) — Brave/WhatsApp/VS Code allowed apps;
  ALWAYS_ASK (7) + NEVER_ALLOW (2); injection nahi kar sakta kyunki risk sirf
  args se nikal ti hai (source ka koi hissa nahi).

KAAM 4 (fix/speed-replies, 9223b86) — awaaz 1-2 poore vaakya; time/date jawab
  ka minute-bucket cache (purana cache kabhi hit nahi hua tha). Sentence
  streaming ka design note (code nahi — sahi soch raha tha).

KAAM 5 (fix/hot-window, 1f970eb) — follow-up bina "Jarvis", DEFAULT OFF.
  Apni awaaz follow-up nahi ban sakti (tail guard + is_utterance pehle).

KAAM 6 (fix/hud-polish, 0e446d5) — SYSTEM panel ka "--" fix. render() sirf WS
  event par chalti thi, pump pehle 2 s sota hai, aur WS na chala to "--"
  hamesha. Naya ui/hud_prime.js. Type-bar 1366x768 FIX NAHI hua (Playwright
  nahi hai — honestly chhoda).

Suite 75 = 69 pass + 6 jaane-pehchane fail (naya nahi). Push nahi hua — git
ka saved credential alag account ka hai. Poora record docs/OVERNIGHT_REPORT.md.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
## Keys

- `.env` me 6 brain/voice keys + voice ids (values kabhi commit nahi).
- `.env.example` me sirf naam.
- `.env` git-ignored.
