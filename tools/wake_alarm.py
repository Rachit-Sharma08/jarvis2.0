"""SAUBEH 7 BAJE KA ALARM — `python tools/wake_alarm.py`

Rachit ko subah uthane ke liye. **Jarvis chalu ho ya na ho** — ye alag script
hai, Task Scheduler se chalti hai (`JarvisWakeAlarm` 07:00, `JarvisWakeAlarmBackup`
07:10). Jarvis band bhi ho to bajegi.

Har ~20 second: **bol** (edge-tts → offline SAPI) + **Windows ka alarm wav**.
Loop ka kaam `tools/alarm_loop.py` me hai; ye file sirf CLI/flag ka hai.

Rukne ke tareeke wahi hain jo loop me hain: `data/alarm_ack` flag file, console
me koi key, ya **15 minute** baad apne aap band.

**Flags (test inhi se — raat me awaaz nahi):**

- `--no-audio`  — sirf logic + log, **koi awaaz nahi**.
- `--dry-run`   — plan batao (kab, kya, kitni baar) aur bhaag jao.
- `--if-no-ack` — backup task ke liye: flag bana ho to bilkul chup.

**Task banana hamesha haath se** (`--install`), LLM se kabhi nahi —
`tools/alarm_task.py` usi ka raasta hai.

Hataane ka tareeka: `python tools/wake_alarm.py --uninstall`, ya
`schtasks /delete /tn JarvisWakeAlarm /f` aur `...Backup /f`.
"""

import argparse
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config                                            # noqa: E402
from log_setup import get_logger                         # noqa: E402
from tools import alarm_audio, alarm_loop                # noqa: E402

log = get_logger("wake_alarm")

# Hindi text wahi hai jo `tools/alarm.py` use karta hai — ek hi jagah.
TEXT_HI = alarm_audio.TEXT_HI
TEXT_HINGLISH = alarm_audio.TEXT_HINGLISH
TASK_NAME = "JarvisWakeAlarm"
TASK_NAME_BACKUP = "JarvisWakeAlarmBackup"


def plan(args) -> str:
    """--dry-run ka plan. Kuch nahi chalta."""
    return "\n".join([
        "WAKE ALARM PLAN (kuch nahi chalega)",
        f"  bolna        : {len(TEXT_HI)} char Hindi (edge-tts {alarm_audio.VOICE})",
        f"  fallback     : SAPI Hinglish - {TEXT_HINGLISH}",
        f"  alarm wav    : {alarm_audio.alarm_wav() or 'NAHI MILA'}",
        f"  gap          : {alarm_loop.REPEAT_SECONDS:.0f} s",
        f"  apne aap band : {alarm_loop.MAX_MINUTES:.0f} min baad",
        f"  band karne ka : {alarm_loop.ack_file()}",
        f"  task         : {TASK_NAME} (07:00) + {TASK_NAME_BACKUP} (07:10)",
        f"  audio        : {'HAAN' if not args.no_audio else 'NAHI (--no-audio)'}",
    ])


def _silent_alarm():
    """`--no-audio` ka Alarm — nakli `say`/`play`, asli awaaz **kabhi** nahi."""
    calls = {"say": 0, "play": 0}

    def fake_say(_hi, _hinglish):
        calls["say"] += 1
        return "no-audio"

    def fake_play(_path):
        calls["play"] += 1
        return True

    alarm = alarm_loop.Alarm(
        repeat=alarm_loop.REPEAT_SECONDS, max_minutes=alarm_loop.MAX_MINUTES,
        wav=alarm_audio.alarm_wav(), say=fake_say, play=fake_play,
        sleep=lambda seconds: calls.setdefault("sleeps", []).append(seconds),
        key=lambda: False)
    return alarm, calls


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Subah ka alarm (Rachit ke liye)")
    ap.add_argument("--no-audio", action="store_true",
                    help="sirf logic + log, koi awaaz nahi (test ke liye)")
    ap.add_argument("--dry-run", action="store_true", help="plan dikha kar bhaag jao")
    ap.add_argument("--keep-ack", action="store_true", help="purana alarm_ack mat hatao")
    ap.add_argument("--if-no-ack", action="store_true",
                    help="backup task: alarm_ack bana ho to bilkul chup")
    ap.add_argument("--install", metavar="'YYYY-MM-DD HH:MM'", default=None,
                    help="Task Scheduler me dono task banao (haath se)")
    ap.add_argument("--status", action="store_true", help="dono task ki asli date/time")
    ap.add_argument("--uninstall", action="store_true", help="dono task hata do")
    args = ap.parse_args(argv)

    if args.dry_run:
        print(plan(args))
        return 0

    # Task Scheduler sirf `tools/alarm_task.py` se — system ek hi raasta.
    if args.install or args.status or args.uninstall:
        from tools import alarm_task
        if args.install:
            when = (datetime.datetime.strptime(args.install, "%Y-%m-%d %H:%M")
                    if args.install else None)
            print(alarm_task.install(when))
        elif args.uninstall:
            print(alarm_task.uninstall())
        else:
            print(alarm_task.status())
        return 0

    # Backup task: pehle hi rok diya gaya hai to kuch nahi bolna.
    if args.if_no_ack and alarm_loop.ack_file().exists():
        print("alarm_ack bana hai - alarm nahi bajaya.")
        return 0

    if not args.keep_ack and alarm_loop.clear_ack():
        log.info("purana alarm_ack hata diya")

    if args.no_audio:
        alarm, _calls = _silent_alarm()
    else:
        alarm = alarm_loop.Alarm(
            repeat=alarm_loop.REPEAT_SECONDS, max_minutes=alarm_loop.MAX_MINUTES,
            wav=alarm_audio.alarm_wav(),
            say=lambda hi, hinglish: alarm_audio.speak(hi, hinglish),
            play=alarm_audio.play_wav)
    print(f"alarm khatam: {alarm.run()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
