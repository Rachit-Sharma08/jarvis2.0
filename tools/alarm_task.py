"""Windows Task Scheduler se alarm — **haath se**, LLM se kabhi nahi.

Ye file sirf `python tools/wake_alarm.py --install/--status/--uninstall` se
chalti hai. Task Scheduler me kuch bhi **sirf yahan** likha jaata hai, is liye
Jarvis ka tool (`tools/alarm.py`) sirf request file banata hai — system ko LLM
ke text se haath nahi lagta.

Do task:

| Task | Kab | Kya |
|---|---|---|
| `JarvisWakeAlarm` | 07:00 | awaaz + alarm wav |
| `JarvisWakeAlarmBackup` | 07:10 | **sirf** tab jab `data/alarm_ack` nahi bana |

Dono **user-level** hain (admin nahi), **sirf tab** jab user logged on ho
(`LogonType Interactive` — isiliye console dikhta hai), aur **PC ko jaagane**
ka pakkaura laga hai (`WakeToRun`).

Date locale se bachi hai: `schtasks /sd` par bharosa nahi — yahan
PowerShell ko ek `DateTime` object dete hain (`New-ScheduledTaskTrigger -Once -At`).
"""

import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
SCRIPT = ROOT / "tools" / "wake_alarm.py"
TASK = "JarvisWakeAlarm"
TASK_BACKUP = "JarvisWakeAlarmBackup"
HIDE = 0x08000000

# `Register-ScheduledTask` ka poora block. `{when}` ko `ps_when()` bharata hai.
#
# Do galti yahan pehle ho chuki hain — dono guard ab script me hi hain:
# 1. `Register-ScheduledTask` par **`-ErrorAction Stop`** + upar
#    `$ErrorActionPreference = 'Stop'`. Bina iske `| Out-Null` non-terminating
#    error ko nigal deta tha aur script **"OK"** bol deta tha jabki task bana
#    hi nahi tha (pehli baar yahi hua).
# 2. Aakhir me `Get-ScheduledTask` se **dobara** check — task sach me bana ya
#    nahi ye khud confirm karta hai aur `StartBoundary` wapas deta hai.
_TEMPLATE = r"""
$ErrorActionPreference = 'Stop'
$action  = New-ScheduledTaskAction -Execute '{python}' -Argument '-u {script} {extra}' -WorkingDirectory '{root}'
$trigger = New-ScheduledTaskTrigger -Once -At {when}
$prin    = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$set     = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries `
                     -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName '{name}' -Action $action -Trigger $trigger `
                       -Principal $prin -Settings $set -Force -ErrorAction Stop | Out-Null
$t = Get-ScheduledTask -TaskName '{name}' -ErrorAction Stop
Write-Output ('OK {name} state=' + $t.State + ' start=' + $t.Triggers[0].StartBoundary + ' wake=' + $t.Settings.WakeToRun + ' logon=' + $t.Principal.LogonType)
"""


def ps_when(when: datetime.datetime) -> str:
    """`New-ScheduledTaskTrigger -At` ke liye literal — **locale safe**.

    `schtasks /sd` par bharosa nahi (MM/DD/YYYY vs DD/MM/YYYY machine par
    badalta hai), aur `[datetime]::new(y,m,d,h,mi)` par bhi nahi — uska 5-arg
    overload exist hi nahi karta. `Get-Date -Year .. -Month ..` sabse pakka hai.

    ⚠️ **Minute bhi dena zaroori hai.** Pehle yahan `-Minute 0` likha tha, to
    backup task (07:10) bhi 07:00 par ban gaya — aur `Register-ScheduledTask`
    ne khush-khush "OK" bol diya. Isi liye har baar task ka `StartBoundary`
    wapas padha jaata hai (`register()` ka aakhri `Get-ScheduledTask`)."""
    return ("(Get-Date -Year {0} -Month {1} -Day {2} -Hour {3} -Minute {4} "
            "-Second 0)").format(when.year, when.month, when.day, when.hour,
                                 when.minute)


def register(name: str, when: datetime.datetime, extra: str = "") -> str:
    """Ek task bana/refresh karo. -> PowerShell ka asli output.

    Script ke andar hi do guard hain (`-ErrorAction Stop` + aakhri
    `Get-ScheduledTask`), is liye **"OK"** ka matlab sach me task bana hua hai
    aur sahi time par. Phir bhi yahan ek aur check hai — agar output me `OK`
    nahi hai to `NAHI BANA` return karo (pehli baar yahi galti hui thi)."""
    if not PYTHON.exists():
        return f"NAHI BANA (venv python nahi mila: {PYTHON})"
    command = _TEMPLATE.format(
        python=str(PYTHON), script=str(SCRIPT), root=str(ROOT),
        extra=extra, when=ps_when(when), name=name)
    out = run_powershell(command, timeout=120).strip()
    if "OK " not in out:
        return f"NAHI BANA: {out[:300]}"
    return out


def run_powershell(command: str, timeout: int = 90) -> str:
    """Anya PowerShell (status/uninstall) — text wapas."""
    done = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        shell=False, capture_output=True, text=True, timeout=timeout,
        creationflags=HIDE)
    return (done.stdout or "") + (done.stderr or "")


def query(name: str) -> str:
    """Ek task ki asli detail (date/time/trigger) — user ke report ke liye."""
    safe = name.replace("'", "''")
    return run_powershell(
        "$t = Get-ScheduledTask -TaskName '{n}' -ErrorAction SilentlyContinue; "
        "if (-not $t) {{ 'NAHI HAI' }} else {{ "
        "'name=' + $t.TaskName + ' | state=' + $t.State + ' | trigger=' + "
        "$t.Triggers[0].StartBoundary + ' | action=' + $t.Actions[0].Execute + "
        "' | args=' + $t.Actions[0].Arguments + ' | wake=' + "
        "$t.Settings.WakeToRun + ' | logon=' + $t.Principal.LogonType }}".format(
            n=safe))


def install(when: datetime.datetime = None, backup_minutes: int = 10) -> str:
    """Dono task banao. -> har ek ke liye ek line (asli `StartBoundary` ke saath)."""
    when = when or tomorrow_seven()
    backup = when + datetime.timedelta(minutes=backup_minutes)
    lines = [f"{TASK} -> {register(TASK, when)}",
             f"{TASK_BACKUP} (+{backup_minutes} min) -> "
             f"{register(TASK_BACKUP, backup, extra='--if-no-ack')}"]
    return "\n".join(lines)


def tomorrow_seven(now: datetime.datetime = None) -> datetime.datetime:
    """Kal subah 07:00 (local)."""
    now = now or datetime.datetime.now()
    day = (now + datetime.timedelta(days=1)).date()
    return datetime.datetime.combine(day, datetime.time(7, 0))


def uninstall() -> str:
    """Dono task hata do. `schtasks /delete` — yehi report me bhi hai."""
    out = []
    for name in (TASK, TASK_BACKUP):
        done = subprocess.run(
            ["schtasks", "/delete", "/tn", name, "/f"],
            shell=False, capture_output=True, text=True, timeout=60,
            creationflags=HIDE)
        out.append(f"{name}: rc={done.returncode} "
                   f"{(done.stdout or done.stderr or '').strip()[:120]}")
    return "\n".join(out)


def status() -> str:
    """Dono task ki asli detail (proof ke liye report me daala jaata hai)."""
    return "\n".join(query(name) for name in (TASK, TASK_BACKUP))


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "--status":
        print(status())
        return 0
    if argv[0] == "--uninstall":
        print(uninstall())
        return 0
    if argv[0] == "--install":
        when = None
        if len(argv) > 1:
            when = datetime.datetime.strptime(argv[1], "%Y-%m-%d %H:%M")
        print(install(when))
        return 0
    print("usage: python -m tools.alarm_task --install ['YYYY-MM-DD HH:MM']"
          " | --status | --uninstall")
    return 2


if __name__ == "__main__":
    sys.exit(main())
