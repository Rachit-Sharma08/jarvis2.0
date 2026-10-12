"""Alarm ka **loop** — bolna, bajana, aur rukna. CLI nahi.

`tools/wake_alarm.py` ise entry point bana kar chalaata hai. Alag is liye:

- loop ka test bina `argparse` ke seedha chal jaata hai (`tests/test_wake_alarm.py`),
- aur 200-line niyam dono taraf bhar jaata hai.

Rukne ke **teen** tareeke `Alarm.stop_reason()` me hain:

1. `data/alarm_ack` flag file banna.
2. Console me koi bhi key.
3. `max_minutes` — iske baad apne aap band.

Aur ek **chautha** safety: `max_rounds` — clock/sleep kabhi na chale to bhi
loop se bahar aa jaye. "Kabhi hamesha na chale" ka niyam yahin pakda jaata hai.

Sab side-effect constructor me **inject** hote hain — test me nakli `say`/`play`/
`clock` se asli awaaz **kabhi** nahi bajti.
"""

import time
from pathlib import Path

import config
from log_setup import get_logger

log = get_logger("wake_alarm")

REPEAT_SECONDS = 20.0        # do bolne ke beech ka gap
MAX_MINUTES = 15.0           # iske baad apne aap band
MAX_ROUNDS = 500             # aakhri safety (loop kabhi na ghoome)
ACK_NAME = "alarm_ack"        # data/ me - band karne ka signal


def ack_file() -> Path:
    """Band karne ka flag file (`data/alarm_ack`)."""
    return config.DATA_DIR / ACK_NAME


def clear_ack(path: Path = None) -> bool:
    """Purana flag hata do — warna alarm shuru hi nahi hoga. -> tha/nahi."""
    target = path or ack_file()
    try:
        target.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        log.warning("purana ack hata nahi: %s", exc)
        return False


def key_pressed() -> bool:
    """Console me koi key dabayi? (msvcrt — pythonw par safe fail)."""
    try:
        import msvcrt
        return bool(msvcrt.kbhit())
    except Exception:                                   # noqa: BLE001
        return False


class Alarm:
    """Alarm poora loop. Sab side-effect inject hote hain."""

    def __init__(self, repeat=REPEAT_SECONDS, max_minutes=MAX_MINUTES,
                 ack=None, wav=None, say=None, play=None, key=None,
                 clock=None, sleep=None, max_rounds=MAX_ROUNDS):
        self.repeat = float(repeat)
        self.max_seconds = float(max_minutes) * 60.0
        self.max_rounds = int(max_rounds)
        self.ack = Path(ack) if ack is not None else ack_file()
        self.wav = wav if wav is not None else ""
        self.say = say or (lambda hi, hinglish: "none")
        self.play = play or (lambda path: False)
        self.key = key or key_pressed
        self.clock = clock or time.monotonic
        self.sleep = sleep or time.sleep
        self.started = self.clock()

    def elapsed(self) -> float:
        return self.clock() - self.started

    def stop_reason(self) -> str:
        """Rukna hai? -> karan ('' matlab chalu hai). Teeno niyam ek jagah."""
        if self.ack.exists():
            return "ack file bana"
        if self.key():
            return "key dabayi"
        if self.elapsed() >= self.max_seconds:
            return f"{self.max_seconds / 60:.0f} minute ho gaye"
        return ""

    def round(self) -> None:
        """Ek baar: bol + alarm. (`--no-audio` par nakli `say`/`play` lagte
        hain, is liye koi awaaz nahi.)"""
        from tools import alarm_audio
        who = self.say(alarm_audio.TEXT_HI, alarm_audio.TEXT_HINGLISH)
        log.info("alarm bola: %s", who)
        self.play(self.wav)
        log.info("alarm bajaya: %s", self.wav or "koi wav nahi")

    def run(self) -> str:
        """Loop. -> rukne ka karan (ya 'hat gaya')."""
        log.info("alarm shuru | gap=%.0fs cap=%.0fmin wav=%s",
                 self.repeat, self.max_seconds / 60, self.wav or "NAHI")
        rounds = 0
        while True:
            reason = self.stop_reason()
            if reason:
                log.info("alarm ruka: %s", reason)
                return reason
            self.round()
            rounds += 1
            if rounds >= self.max_rounds:
                log.warning("alarm safety cap: %d round", rounds)
                return f"safety cap ({rounds} round)"
            self.sleep(self.repeat)
        return "hat gaya"                     # unreachable, type ke liye
