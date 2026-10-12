# OVERNIGHT REPORT — 13 Oct 2026 raat → 14 Oct 2026 subah

Rachit so raha tha. Maine raat bhar kaam kiya. **Ye file poori report hai** —
sirf ise padhna kaafi hai. Baaki har kaam ka detail neeche hai.

**Sandarbh:** `D:\prabh` · Windows · Jarvis (HUD browser me, wake word + STT + brain + TTS)
**Suite ab:** 75 total = **69 pass + 6 jaane-pehchane fail** (naya fail nahi)

---

## 1. Ek nazar me — kya hua

| # | Kaam | Status | Branch | Commit |
|---|---|---|---|---|
| 0 | Test ka log `logs/prabh.log` se alag | **ho gaya** | `fix/stt-speed` | `695e5c5` |
| 1 | **Subah 7 baje ka alarm** (sabse zaroori) | **ho gaya + task bana** | `feat/wake-alarm` | `84842a0` |
| 2 | Apni awaaz se wake (tail guard) | **ho gaya** | `fix/self-hearing` | `5bb76cc` |
| 3 | Permissions v2 + injection | **ho gaya** | `fix/permissions-v2` | `f6e28f8` |
| 4 | Tez jawab (awaaz + cache) | **ho gaya** | `fix/speed-replies` | `9223b86` |
| 5 | Follow-up bina "Jarvis" | **ho gaya (band)** | `fix/hot-window` | `1f970eb` |
| 6 | HUD `--` fix + stats load | **ho gaya** | `fix/hud-polish` | `0e446d5` |
| 7 | **Naya Arc Reactor HUD theme** | ❌ **SHURU NAHI HUA** | — | — |
| — | **Push** | ❌ **TERA KAAM** | — | — |

**Ek line me:** 6 kaam poore, 1 (Arc theme) chhoda kyunki verification ka
samaan (Playwright) is machine par nahi tha, aur 1 (push) tere login par atka.

---

## 2. TUMHARA KAAM (tere bina pura nahi hua) — 4 cheezein

### 2.1 PUSH — sabse pehle ye kar

Teen baatein **check kar chuki hain**, koi kaam nahi bacha:

| Check | Nateeja |
|---|---|
| `origin` sahi hai? | ✅ `https://github.com/Rachit-Sharma08/jarvis2.0.git` (pehle se, maine nahi badla) |
| Repo **PRIVATE** hai? | ✅ **haan** — bina login `ls-remote` fail hua (public hota to chal jata) |
| History me secret? | ✅ **nahi** — poori history scan ki, 13 hit mile par **sab nakli test key** (`gsk_FAKEFAKEFAKEFAKE1234567890`, `gsk_test1234567890abcdef`) |
| `.env` / `logs/` / `data/` gitignore me? | ✅ haan, aur track nahi hain |

**Atka ye hua:** git ka saved credential **alag account** ka hai —

```
could not read Password for 'https://rachithunyawrr@github.com'
```

Target repo `Rachit-Sharma08` ka, par git `rachithunyawrr` se login karne ki
koshish kar raha hai aur password maang raha hai. **Maine na password maanga,
na git ka credential/account badla, na force kiya** (tera faisla hai).

Bas ye 2 command chalana hai:

```
cd D:\prabh
git push -u origin fix/stt-speed
git push -u origin feat/wake-alarm
git push -u origin fix/self-hearing
git push -u origin fix/permissions-v2
git push -u origin fix/speed-replies
git push -u origin fix/hot-window
git push -u origin fix/hud-polish
```

(`main` push **mat** karna.)

Login sahi hai to foran chal jayega. Nahi to pehle apna account set kar:

```
git config --global user.name "Rachit Sharma"
git config --global user.email "rachit.sharma08@users.noreply.github.com"
```

### 2.2 ALARM subah check karna (task ban chuka hai)

Task dono ban chuke hain aur Ready hain — **proof neeche** (section 3).

```
New-Item D:\prabh\data\alarm_ack -ItemType File   # alarm CHUP ho jaani chahiye
Remove-Item D:\prabh\data\alarm_ack               # hata de!
```

⚠️ **`data\alarm_ack` agar 07:00 se PEHLE bana raha aur reh gaya, to alarm
nahi bajegi.** Ye file abhi nahi hai (maine check kiya).

**Alarm ko abhi test karna hai** (koi fake nahi, sach me awaaz aayegi):

```
D:\prabh\.venv\Scripts\python.exe D:\prabh\tools\wake_alarm.py
```

→ Console me **koi bhi key daba** → ruk jaani chahiye.

**Hataana:** `python D:\prabh\tools\wake_alarm.py --uninstall`, ya

```
schtasks /delete /tn JarvisWakeAlarm /f
schtasks /delete /tn JarvisWakeAlarmBackup /f
```

**Wapas banana:** `python D:\prabh\tools\wake_alarm.py --install "2026-10-15 07:00"`
**Bina awaaz check:** `python D:\prabh\tools\wake_alarm.py --dry-run`

### 2.3 Playwright install karwana (KAAM 7 + KAAM 6 ka baaki hissa)

```
.venv\Scripts\python.exe -m pip install playwright
.venv\Scripts\python.exe -m playwright install chromium
```

Isi ke bina **HUD ka type-bar (1366x768 par katna)** theek nahi ho sakta.
Maine **andaza laga kar CSS nahi badla** — Phase 4 me isi tarah ka overflow
bug hua tha, aur bina browser dekhe badalna bug aur bada kar sakta.

### 2.4 Jarvis abhi BHI chal raha hai

`desktop.app` PID **7672** + **3564**, start **01:26:12** — mere kaam shuru
hone se **pehle**. Usne **mic bhi khula rakha hai** (`wake_audio | mic khula`
01:26:15). Task me likha tha "band hai" par wo nahi tha. **Maine chheda nahi**
(NIYAM: koi process kill mat karo). Tera faisla — band karna hai ya nahi.

---

## 3. ALARM TASK — asli proof (`schtasks /query`, 13-Oct raat)

```
TaskName:                             \JarvisWakeAlarm
Next Run Time:                        14-10-2026 07:00:00
Status:                               Ready
Task To Run:                          D:\prabh\.venv\Scripts\python.exe -u D:\prabh\tools\wake_alarm.py
Scheduled Task State:                 Enabled
Run As User:                          fvcvv
Schedule Type:                        One Time Only

TaskName:                             \JarvisWakeAlarmBackup
Next Run Time:                        14-10-2026 07:10:00
Status:                               Ready
Task To Run:                          D:\prabh\.venv\Scripts\python.exe -u D:\prabh\tools\wake_alarm.py --if-no-ack
Scheduled Task State:                 Enabled
Run As User:                          fvcvv
```

`WakeToRun=True` aur `LogonType=Interactive` (PowerShell se verify) — yaani PC
so raha ho to jaagayega, aur console dikhega. **Do alag tools se verify kiya**
(`Get-ScheduledTask` + `schtasks /query`), dono sahi.

**Kaise kaam karta hai:** har ~20 s: Hindi awaaz (edge-tts `hi-IN-SwaraNeural`,
na chale to **offline SAPI** Hinglish me) + `C:\Windows\Media\Alarm01.wav`.
Rukne ke **teen** tareeke: console me koi key · `data/alarm_ack` file · **15 min**
baad apne aap. System volume **chheda nahi** jaata.

---

## 4. Har kaam ka detail

### KAAM 0 — test ka log alag (`fix/stt-speed` @ `695e5c5`)

**Kyua:** `logs/prabh.log` ek hi file — app aur dono test likhte the. S-1 audit
me isi wajah se **mic ka asli level galat** nikaala gaya tha: `tests/wakehelp.py`
ka `loud()` **exactly 0.129** deta hai, aur wahi number asli app ke log me bhi
aa raha tha.

**Kya badla:** `config.py` me `LOG_DIR` ab `PRABH_LOG_DIR` env se (default
bilkul waisa) · naya `tests/logsafe.py` · **64 test file** me import ·
naya `tests/test_logsafe.py`.

**SABOOT:** poori suite pehle app log **+17974 byte** likhti thi, ab **+0**.

**Do galti jo script me hui (sab theek hui):** `sys.path.insert` ko **string
literal** me dhoondh liya → beech me `IndentationError` (`test_desktop_login.py`).
Aur `logsafe` ko `import config` ke baad rakha, jabki
`from tests.wakecmdhelp import` usse pehle tha (wo `desktop.playback` laata
hai jo `config` le aata hai) → **sahi rule: pehla repo-touching import.**

### KAAM 1 — subah 7 baje ka alarm (`feat/wake-alarm` @ `84842a0`)

Files: `tools/alarm_loop.py` (loop + rukne ke 3 niyam + `max_rounds` safety) ·
`tools/alarm_audio.py` (edge-tts → SAPI → Windows wav) · `tools/wake_alarm.py`
(CLI) · `tools/alarm_task.py` (Task Scheduler) · `tools/alarm.py` (Jarvis ka
tool, **DEFAULT OFF** — sirf request file likhta hai, **Task Scheduler ko LLM
kabhi nahi chhoo sakta**).

**Teen asli galti jo is kaam me pakdi — teeno ab code me guarded hain:**

1. **`Register-ScheduledTask` par `-ErrorAction Stop` nahi tha** → `| Out-Null`
   non-terminating error nigal deta tha aur script **"OK"** bol deti thi jabki
   task bana hi nahi tha. Pehli baar yahi hua.
2. **`[datetime]::new(y,m,d,h,mi)` ka 5-arg overload exist hi nahi karta** →
   trigger bana hi nahi. Ab `Get-Date -Year .. -Month ..` (locale safe bhi).
3. **`ps_when()` minute hataa raha tha** (`-Minute 0`) → backup task **07:10 ke
   bajaye 07:00** par ban gaya, jabki PowerShell "OK" bol raha tha. Ab har baar
   task ka **asli `StartBoundary` wapas** padha jaata hai.

### KAAM 2 — apni awaaz se WAKE HIT nahi (`fix/self-hearing` @ `5bb76cc`)

**Tera sawaal: `PLAYBACK_MUTE_MIC` sach me har raaste par laagu hai?**
**NAHI — verified.** Wo flag sirf `config_wake.py:115` me define hai aur
`config.py:84` se re-export; production me koi file nahi padhti. **Dead code.**
SABOOT: `tests/test_hearing_audit.py`.

**Asli rok ka raasta:** `wake/worker.py` ka `hold_for_command()` /
`release_from_command()` (command poore chalte tak sunna band). Par sirf
`drain()` **kaafi nahi** tha:

| # | Kya | Number |
|---|---|---|
| 1 | `command.py` ke `finally` me drain + release ka **order** | sahi tha |
| 2 | `drain()` ki hadd `MAX_QUEUE_BLOCKS` | 400 chunk ≈ **12 s** |
| 3 | Jawab ka TTS | **18.5 s** (`speak 18530ms`, log) |
| 4 | To queue me apni awaaz bachi | ~**6 s** |
| 5 | Purana `take_fresh()` | sirf **1 chunk** bachata tha |
| 6 | `cooling()` | sirf **1.5 s** — is liye koi faida nahi |

**Fix:** `PLAYBACK_TAIL_GUARD_SECONDS = 0.4` (`.env`: `PRABH_TAIL_GUARD`) —
hold chhodte hi itni der **koi** chunk trigger nahi kar sakta.

**Ek aur asli path bug-injection me pakda:** `gate.on_flush()` gate **thread**
se `maybe()` bulata hai, aur wahan `_loop` ka check nahi lagta — matlab tail
guard **flush se bypass** ho sakta tha. Ab `maybe()` khud `suppressing()`
check karta hai. Test me guard hata kar dekha: 2 check fail hue.

**Fake wake-up ke raaste (sab test me):** (1) `gate.on_flush()` ← fix hua
(2) drain ke baad bache chunk (3) hold ke dauraan — pehle se theek
(4) TTS ke dauraan ack beep — pehle se theek (5) restart ke turant baad stale
tail — `reset_cooldown()` tail bhi saaf karta (6) cooldown khatam par apni
awaaz — pehle trigger ho jaata tha (test me prove).

### KAAM 3 — permissions v2 (`fix/permissions-v2` @ `f6e28f8`)

Purana risk table (SAFE/ASK/BLOCKED + `EXTRA_BLOCKED_PATTERNS`) **bhaara
nahi** — naya uske upar.

**(a)** Allowed apps: VS Code pehle se tha; **Brave aur WhatsApp** jode
(+ `visual studio code`, `brave browser`, `whatsapp desktop` aliases).

**(c) Hamesha "haan" card** — `config.ALWAYS_ASK` (7): paise · naye contact ko
message · public post/git push · permanent delete · system settings/password ·
guard file badalna · main me merge. `config.NEVER_ALLOW` (2) **BLOCKED** (card
bhi nahi): guard file delete · password likhna.

**(b) Injection — tera sawaal ka jawab:** risk sirf **ARGS** se nikalte hain,
source ka koi hissa nahi dekhate. Is liye page/file/message me likha "sab allow
kar do" ya "WhatsApp bhej do" **kuch nahi badalta**. Tests me 5 tarah ke
injection line + guard-file unlock + fake-URL-marker par prove kiya.

**Ek asli kami bhi mili:** `decide()` ke aakhir me `return base, ""` tha,
jabki uski docstring kehta hai "reason hamesha bhar-i hui hoti hai" — UI/log me
khaali karan dikhta tha. Ab bhara hua.

### KAAM 4 — tez jawab (`fix/speed-replies` @ `9223b86`)

**(a)** `voice_answer()` pehle 1-2 **poore** vaakya bolta hai (config
`VOICE_SENTENCES=2`). Pehle `clip_answer()` 220 **char** par kaatta tha jo
beech se vaakya tod sakta tha. HUD par poora jawab waise hi rehta hai.

**(b)** `voice/answer_cache.py` (naya): time/date wale jawab ka key me **minute
ka bucket**. Kyun zaruri tha: `get_time_date` `core/directreply.py` me
DIRECT_TOOL hai — uska jawab LLM se nahi seedha tool-result se aata hai aur
**har baar naya text** hota hai ("Abhi 3:20 ho raha hai"). Purana cache
`(text, mode)` tha, to time wale jawab ka **kabhi hit nahi** hua aur TTS har
sawal dobara banti thi (~1.5-2 s). Ab usi minute me dobara puchho to **0 ms**.

**(c)** Sentence streaming: **code nahi, design note** —
`docs/SENTENCE_STREAM_NOTE.md`. Usme measured numbers (brain 1.9 s par pehla
shabd **18 s** baad) aur 5 dhyan rakhne wali baatein. Sabse important: wo
refactor bina asli speaker sune likhna **self-hearing wapas la sakta** tha
(mic hold chhoot jaata) — wahi bug jo 2 ghante pehle fix kiya.

### KAAM 5 — follow-up bina "Jarvis" (`fix/hot-window` @ `1f970eb`)

**DEFAULT OFF** (`PRABH_HOT_WINDOW=0`). Band par `hot_active()` hamesha
`False` aur follow-up ke liye wake shabd zaroori — **yaani app purane jaise**.

On karne par: jawab ke baad **12 s** tak sirf bolna sunna kaafi
(`PRABH_HOT_WINDOW_SECONDS`). Follow-up par window **dobara** lagta hai — is
liye ek wake ke baad **teen** follow-up chain ho sakte hain (test me wahi).

Do guard hamesha pehle: **tail guard** (KAAM 2 — apni awaaz follow-up nahi
ban sakti) + `is_utterance()` (sirf asli baat; "uh"/"hmm"/"Thank you." nahi —
guard **wohi** jo STT ke liye hai, duplicate list nahi).

`config.describe()` me `hot=off`/`hot=on:12s` — `--wake-info` se pata chalna
zaroori hai warna pata hi nahi chalega.

### KAAM 6 — HUD ka `--` (`fix/hud-polish` @ `0e446d5`)

**Asli wajah (code padh kar verified):** `hud_stats.js` ka `render()` sirf
WebSocket ke `stats` event par chalti thi. Par pump **pehle 2 s sota hai**
(`ws_routes.py:35`), yaani pehla event 2 s baad — har load par `--`. Aur WS
kabhi na chala (token mismatch — `localhost` vs `127.0.0.1` wala purana bug)
to `--` **hamesha**.

`hud_routes.py:4` ka docstring kehta hai ye endpoint "ek baar load par bhi
chalta hai taaki panel khali na rahe" — par JS **kabhi call hi nahi** karta
tha. Naya `ui/hud_prime.js` wahi karta hai.

**SABOOT:** `/hud/stats` 200 deta hai aur `cpu`/`ram` **kabhi `None` nahi** —
yaani `--` data ki kami nahi, **call na hone** ki kami thi.

**⚠️ Type-bar ka katna FIX NAHI HUA** — Playwright nahi hai. Reason section
2.3 me. Ye main jaan-boojh kar chhoda: bina browser dekhe CSS badalna Phase 4
ka overflow bug dobara la sakta tha.

---

## 5. ❌ KAAM 7 — Arc Reactor theme: SHURU NAHI HUA (honest report)

**Kuch nahi banaya.** Kyun:

1. **Playwright is machine par nahi hai** (Phase 4 ke baad hata diya gaya tha
   — `AGENTS.md` 3.2 me likha hai), aur **naya package lagana NIYAM 4 me
   mana** hai.
2. Us theme ka pura spec screenshot + 1366x768 par live measurement
   demand karta hai (input bar scroll na kare, Hindi font theek dikhe, state
   label badle, CPU na bade). **Bina browser ke koi bhi claim "theek hai"
   galat hota** — Phase 4 me isi tarah 8 asli bug source-check se chhoot
   gaye the aur sirf asli Chrome me pakde gaye.
3. Raat ke 4 baje ek bhaari UI theme likhna, phir subah 7 baje tera alarm
   bajna hai. Galat theme likh ke neeche jaana behtar tha.

**Meri takat ka andaaza:** ek pura theme (CSS variables, SVG rings, tick marks,
orbiting dots, typewriter, Devanagari font stack, `prefers-reduced-motion`,
sab panels) 6-8 ghante ka kaam hai **live verify** karte hue. Jo bacha tha,
usse achha se karne ka mauka hai.

**Kya zaroori hai (tera kaam, ek baar):** section 2.3 ke 2 command. Uske
baad main (ya koi agla session) `feat/hud-arc` branch par ye kar sakta hai:
`ui/hud_arc.css` + `ui/hud_arc.js` + `PRABH_HUD_THEME` flag (default purana
neela) + `?theme=arc` switch + 1366x768 aur 1920x1080 screenshot.

**Reference:** <https://jarvis.mukh1.com> — sirf **LOOK** dekhna, unka code/CSS
copy nahi. Chhota footer credit: "Interface style inspired by Mukh.1".

---

## 6. Meri galti — report honesti se

Maine verify karte waqt `python tools\wake_alarm.py --if-no-ack` **bina
`--no-audio`** chala diya. Flag file nahi thi, to **asli alarm 2 round chala** —
edge-tts + `C:\Windows\Media\Alarm01.wav`, ~37 second (03:28:14 → 03:28:51,
`logs/prabh.log` me entry hai). Shell timeout par process apne aap band hua;
koi alarm process nahi bacha. **Raat me awaaz — sorry.** Har manual run me ab
`--no-audio` ya `--dry-run` hi use karna hai.

Ek aur: `git checkout wake/trigger.py` (bug-injection test ke baad) ne meri
**kaam ki copy** hata di aur HEAD wala la diya — tail guard poora gaya tha.
Turant dobara laga diya aur test se verify kiya. Doosri baar split script ne
test file ka `if __name__ == "__main__"` runner hata diya, jisse test **chup-chaap
chalta hi nahi** tha (exit 0, koi check nahi). Poora file dobara likha aur ab
guard bhi rakha hai.

---

## 7. Naye flags — kaise on karun

Sab **DEFAULT OFF** hain (koi abhi on nahi). `.env` me likhna:

```
# KAAM 1 — Jarvis ke andar alarm tool ("kal subah 7 baje utha dena")
PRABH_ALARM_TOOL=1

# KAAM 5 — jawab ke baad 12 s follow-up, "Jarvis" na bola tab bhi
PRABH_HOT_WINDOW=1
PRABH_HOT_WINDOW_SECONDS=12

# KAAM 2 — apni awaaz ke liye guard (default 0.4 s)
PRABH_TAIL_GUARD=0.4

# KAAM 4 — awaaz me kitne vaakya bolne hain (default 2)
PRABH_VOICE_SENTENCES=2
```

Flag on karne ke baad `.env` change hone par Jarvis **restart** karna padta
hai (config import-time par padhta hai). Check karne ka tarika:

```
D:\prabh\.venv\Scripts\python.exe D:\prabh\main.py --wake-info
```

`hot=on:12s` dikhna chahiye (KAAM 5), `stt=groq-whisper` (S-2) sab theek.

---

## 8. Subah main kya live test karu (tere liye, order me)

| # | Kya | Kaise | Expected |
|---|---|---|---|
| 1 | **Alarm** | `...\python.exe tools\wake_alarm.py` | awaaz + wav; koi key daba → ruke |
| 2 | Alarm chup | `New-Item data\alarm_ack -ItemType File` → alarm chalao | **awaaaz nahi** → `Remove-Item` |
| 3 | Task sach me | `schtasks /query /tn JarvisWakeAlarm` | `14-10-2026 07:00:00`, Ready |
| 4 | Wake + self-hearing | "Jarvis, mausam batao" | ek trigger; TTS ke baad **dobara trigger nahi** |
| 5 | Awaaz chhoti | same | 1-2 vaakya boli; HUD par **poora** jawab |
| 6 | Time cache | dobara "abhi kitne ghante" (usi minute) | tez (TTS dobara nahi bani) |
| 7 | Permissions | "WhatsApp kholo" | app khula (brave/whatsapp allowed) |
| 8 | Permissions card | "git push kar do" | **card/poochh** (public post → ASK) |
| 9 | HUD `--` | HUD kholo, WS band karke | SYSTEM panel **foran** bhar jaana chahiye (pehle `--` rehta) |
| 10 | Hot window | `.env` me `PRABH_HOT_WINDOW=1` + restart → wake, phir bina "Jarvis" follow-up | **kaam kare** (abhi band hai) |

---

## 9. Jo maine nahi kiya (saaf list)

- **KAAM 7** — Arc Reactor HUD theme (section 5).
- **KAAM 6 ka type-bar** — 1366x768 par katna (Playwright nahi).
- **KAAM 4c** — sentence streaming ka code (sahi jagah design note likha —
  task me bhi yahi kaha tha ki mushkil lage to note likho).
- **Push** — saved credential alag account ka (section 2.1).
- **`PLAYBACK_MUTE_MIC` ka hatana ya jodna** — dead code hai par use karta
  koi nahi; maine nahi chheda. Tera faisla: hata de ya use kar.
- **Purane 6 fail** — ek bhi theek nahi kiya (AGENTS 8.1.2 ke mutabiq
  **hisab me aata hai**, naya fail nahi). Wo hain: `test_desktop.py` +
  `test_desktop_shortcut.py` (`desktop/app.py` 207 lines — 200-line niyam) ·
  `test_wake_ack` / `test_wake_command` / `test_desktop_sleep` (ack ka text) ·
  `test_wake_resample` (gain).
- **`main` me kuch merge nahi**, **koi push nahi**, **koi force-push nahi**,
  **koi branch delete nahi**, **history nahi badli**.

---

## 10. Safety ka record

- `.env` **kabhi nahi khuli**. Koi key/token print, log ya commit nahi hua.
  Har commit se pehle staged diff me `sk-`, `gsk_`, `AIza`, `Bearer`,
  `api_key=`, `ELEVEN`, `GROQ` scan kiya — **har baar saaf**.
- Jarvis (`start_prabh.bat`) **chala nahi**. Koi process **kill nahi** kiya.
  Port 8000 par kuch nahi chala. Asli mic/speaker se awaaz nahi (sirf meri
  galti — section 6).
- **Koi naya package nahi** lagaya. Playwright nahi mila to KAAM 7 chhod di.
- Playwright/browser **koi window nahi** khuli.
- Ek hi throwaway script `%TEMP%\opencode` me (repo ke bahar) — screenshot
  aur probe wahin, repo me nahi.
- **Naya test har kaam ke saath** likha: 11 nayi suite, sab TESTS.md ki
  table me.