# OVERNIGHT REPORT — 13 Oct 2026 raat → 14 Oct 2026 subah

Rachit so raha hai. Ye file **har kaam ke baad** update hoti hai, aakhir me nahi.
Rachit subah sirf yahi padhega.

**Sandarbh:** `D:\prabh` · Windows · Jarvis (HUD browser me, wake word + STT + brain + TTS)
**Shuru:** `fix/stt-speed` @ `b0112bb` (S-2 ho chuka tha)
**Repo:** `https://github.com/Rachit-Sharma08/jarvis2.0.git` (pehle se maujood, `origin`)

**NIYAM jo follow hue:** `.env` kabhi nahi khuli, koi key print/commit nahi; har kaam apni
branch par (pichhli se); Jarvis/start_prabh.bat **chalu nahi kiya**; koi process kill nahi;
port 8000 par kuch nahi; asli mic/speaker se awaaz nahi; koi naya package nahi.

---

## Kaam ka status

| # | Kaam | Status | Branch | Commit | Suite (pass/total) |
|---|---|---|---|---|---|
| 0 | Test log `logs/prabh.log` se alag | **ho gaya** | `fix/stt-speed` | `695e5c5` | 58/64 (6 purane) |
| 1 | Subah 7 baje alarm | **ho gaya** | `feat/wake-alarm` | `84842a0` | 61/67 (6 purane) |

---

## PUSH — BLOCKED (Rachit karna padega)

**Teen baatein clear hain (13 Oct ~03:40):**

1. **Remote sahi hai** — `origin = https://github.com/Rachit-Sharma08/jarvis2.0.git`
   (pehle se maujood, maine nahi badla, naya remote nahi joda).
2. **Repo PRIVATE hai** — bina login `ls-remote` **fail** hua
   (`could not read Password ... terminal prompts disabled`). Public repo me
   ye bina login chal jata. Yaani GitHub pe private hai. ✅
3. **History me koi asli secret nahi** — poori history scan ki; 13 hit mile
   par **sab nakli test key** hain: `gsk_FAKEFAKEFAKEFAKE1234567890`,
   `gsk_test1234567890abcdef`, `gsk_abcdefghijklmnop` — koi asli key nahi.
   `.env`, `logs/`, `data/`, `models/` gitignore me hain aur track nahi hain.

**Lekin push nahi kiya**, kyunki saved git credential **alag account** ka hai:

```
could not read Password for 'https://rachithunyawrr@github.com'
```

Target repo `Rachit-Sharma08` ka hai, par git `rachithunyawrr` se login karne
ki koshish kar raha hai aur password maang raha hai. NIYAM ke mutabiq maine
apna aap na password maanga, na git ka saved credential/account badla, na
force kiya.

### TUMHARA KAAM: push

Ek hi command (apne terminal me, apne account se):

```
cd D:\prabh
git push -u origin fix/stt-speed
git push -u origin feat/wake-alarm
```

Agar `rachithunyawrr` account abhi valid hai to ye foran chal jayega.
Nahi to pehle login badal do:

```
git config --global credential.helper manager
git config --global user.name "Rachit Sharma"
git config --global user.email "rachithunyawrr@users.noreply.github.com"
```

(Account/user badalna **tera** faisla hai — maine nahi chheda.)

**Push ke baad bhi ye verify kar lena:**
`git branch -r` me dono branch dikhein, aur
`https://github.com/Rachit-Sharma08/jarvis2.0` (logged-out/private window me)
khulne par "Not Found" de — yani private hai.

---

---

## KAAM 0 — test ka log alag (done)

**Kya tha:** `logs/prabh.log` ek hi file — app aur test dono likhte the. S-1 audit me isi
wajah se mic ka asli level galat nikaala gaya tha: `tests/wakehelp.py` ka `loud()` ka RMS
**exactly 0.129** asli app ke log me aa raha tha.

**Kya badla:**
- `config.py:25-31` — `LOG_DIR` ab `PRABH_LOG_DIR` env se (default bilkul waisa hi).
- `tests/logsafe.py` (naya) — env import ke time set karta hai + `clear()`/`read()`.
- **64 test file** me `from tests import logsafe` pehle repo-touching import banaya.
- `tests/test_logsafe.py` (naya) — 9 check.

**SABOOT:** poori suite pehle app log **+17974 byte** likh rahi thi, ab **+0**.

**Do galtiyan jo script me hui (sab theek hui, sikh liya):**
1. `sys.path.insert` ko **string literal** me bhi dhoondh liya → beech me `IndentationError`
   (`test_desktop_login.py`). Pakka anchor: `^sys\.path\.insert\(` column 0.
2. Pehli baar `logsafe` ko `import config` se pehle daala, par
   `from tests.wakecmdhelp import ...` usse pehle tha — wo `desktop.playback` laata hai
   jo `config` le aata tha. **Sahi rule: logsafe = pehla repo-touching import.**

---

## KAAM 1 — subah 7 baje ka alarm (done)

**Task bana hua hai, dono Ready hain (proof neeche):**

```
TaskName:                             \JarvisWakeAlarm
Next Run Time:                        14-10-2026 07:00:00
Status:                               Ready
Task To Run:                          D:\prabh\.venv\Scripts\python.exe -u D:\prabh\tools\wake_alarm.py
Scheduled Task State:                 Enabled
Run As User:                          fvcvv

TaskName:                             \JarvisWakeAlarmBackup
Next Run Time:                        14-10-2026 07:10:00
Status:                               Ready
Task To Run:                          D:\prabh\.venv\Scripts\python.exe -u D:\prabh\tools\wake_alarm.py --if-no-ack
Scheduled Task State:                 Enabled
```

`WakeToRun=True` aur `LogonType=Interactive` (PowerShell query se verify).
Yaani: PC so raha ho to jaagayega, aur console dikhega.

### Subah kaise check kare (tera test)

1. **Alarm se pehle:** `New-Item D:\prabh\data\alarm_ack -ItemType File` —
   alarm chup ho jaana chahiye (backup task bhi). Ye file ban jaye to
   `Remove-Item D:\prabh\data\alarm_ack`.
2. **Alarm chalao (abhi, aise):** `D:\prabh\.venv\Scripts\python.exe D:\prabh\tools\wake_alarm.py`
   — console me **koi bhi key** daba → ruk jaana chahiye.
3. **Band karna:** `python tools\wake_alarm.py --uninstall`, ya
   `schtasks /delete /tn JarvisWakeAlarm /f` aur
   `schtasks /delete /tn JarvisWakeAlarmBackup /f`.
4. **Wapas banana:** `python tools\wake_alarm.py --install "2026-10-15 07:00"`.
5. `python tools\wake_alarm.py --dry-run` — kuch nahi bajata, plan dikhata hai.

### Files

`tools/alarm_loop.py` (loop + rukne ke 3 niyam + safety) ·
`tools/alarm_audio.py` (edge-tts → SAPI → Windows wav) ·
`tools/wake_alarm.py` (CLI) · `tools/alarm_task.py` (Task Scheduler) ·
`tools/alarm.py` (Jarvis ka tool, **DEFAULT OFF**).

Test: `test_wake_alarm.py` (loop) · `test_wake_alarm_audio.py` (awaaz/flag) ·
`test_wake_alarm_tool.py` (tool + task). Sab nakli audio se.

### Teen asli galti jo is kaam me pakdi

1. **`Register-ScheduledTask` par `-ErrorAction Stop` nahi tha** → `| Out-Null`
   non-terminating error nigal deta tha aur script **"OK"** bol deti thi jabki
   task bana hi nahi tha. Ab + aakhir me `Get-ScheduledTask` se verify.
2. **`[datetime]::new(y,m,d,h,mi)` ka 5-arg overload exist hi nahi karta** →
   trigger bana hi nahi. Ab `Get-Date -Year .. -Month ..` (locale safe bhi).
3. **`ps_when()` minute hataa raha tha** (`-Minute 0`) → backup task **07:10 ke
   bajaye 07:00** par ban gaya, jabki PowerShell "OK" bol raha tha. Test me
   minute ka check hai.

### ⚠️ Meri galti — report honesti se

Maine verify karte waqt `python tools\wake_alarm.py --if-no-ack` **bina
`--no-audio`** chala diya. Flag file nahi thi, to **asli alarm 2 round chala** —
edge-tts + `C:\Windows\Media\Alarm01.wav`, ~37 second (03:28:14 → 03:28:51,
`logs/prabh.log` me hai). Shell timeout par process apne aap band hua; koi
alarm process nahi bacha. Raat me awaaz — sorry. Do baar ki galti nahi: har
manual run me ab `--no-audio` ya `--dry-run` hi use karna hai.

### ⚠️ Do aur cheezein jo tujhe batana zaroori hai

1. **Jarvis chal raha hai** (task me bola tha band). `desktop.app` PID 7672 +
   3564, start **01:26:12** — mere kaam shuru hone se pehle. Usne mic bhi
   khula rakha hai. Maine **chheda nahi** (NIYAM). Tera faisla.
2. **`tests/wake_alarm.py` split ke baad runner kho gaya tha** — test chup-chaap
   *chalta hi nahi* tha (exit 0, koi check nahi). Maine poora file dobara likha
   aur ab `TestAudioRunsItsChecks` roop se guard bhi rakha hai.

---
