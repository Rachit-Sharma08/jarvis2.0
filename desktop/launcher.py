"""Supervisor — crash par app ko dobara chalata hai.

Startup par `start_prabh.bat` isko chala dete hain (ya Windows login par
`pythonw -m desktop.launcher`). Ye ek child process banata hai
(`python -m desktop.app`) aur uska intezaar karta hai.

Exit code ka matlab:
  0                        — user ne Quit dabaa. Kuch nahi karna.
  3 (EXIT_ALREADY_RUNNING) — app pehle se chal raha hai. Chup-chaap band.
  20 (EXIT_RESTART)        — tray ka Restart. Turant dobara, crash count me
                             nahi gina (user ne khud kaha hai).
  koi aur non-zero         — crash. Backoff ke saath dobara, jab tak
                             `RESTART_MAX` baar me `RESTART_WINDOW_SECONDS`
                             ke andar na ho jaaye — warna crash-loop RAM/CPU
                             khaali kar dega aur kuch dikhega bhi nahi.

Child ka console do jagah jaata hai: **seedha is console par** (taaki crash
turant padhne ko mile) **aur** `logs/desktop.out` me (pythonw me koi console
hota hi nahi, to traceback wahin se padha jaayega).
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

import config
from log_setup import ascii_text, get_logger

log = get_logger("launcher")


def _console(text: str) -> None:
    """Line console par bhi. Sirf log me rakhne se user ko crash ka pata hi
    nahi chalta — isi liye har crash/backoff dono jagah dikhta hai."""
    line = ascii_text(text)
    print(line, flush=True)
    log.error("%s", line)


def _tee(stream, sink) -> None:
    """Child ki stdout/stderr -> console + `logs/desktop.out` (dono)."""
    try:
        for raw in iter(stream.readline, b""):
            line = ascii_text(raw.decode("utf-8", "replace").rstrip())
            try:
                sink.write(line + "\n")
                sink.flush()
            except (OSError, ValueError):
                pass
            print(line, flush=True)
    except (OSError, ValueError):
        pass
    finally:
        try:
            stream.close()
        except OSError:
            pass

# Child ka stdout/stderr. pythonw ke saath console na ho to ye zaroori hai.
CHILD_OUT = config.LOG_DIR / "desktop.out"
_NO_WINDOW = 0x08000000


def child_python() -> str:
    """Child wahi python se chalta hai jis se supervisor chala.

    `start_prabh.bat` (haath se) par `python.exe` — console dikhta hai, crash
    turant padha jaata hai. Windows login par `pythonw.exe` — koi black console
    nahi aata. Pythonw me bhi stdout/stderr redirect ho raha hai, is liye
    crash ka traceback `logs/desktop.out` me hi milega.
    """
    return sys.executable


def child_command() -> list:
    return [child_python(), "-m", "desktop.app"]


def _log_tail(lines: int = 12) -> str:
    """Child ka aakhri kuch — crash ki wajah samjhne ke liye."""
    try:
        content = CHILD_OUT.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    return " | ".join(content[-lines:])[-800:]


EXIT, RESTART, GIVE_UP = "exit", "restart", "give_up"


def next_step(code: int, crashes: list, now: float, span: int,
              limit: int = None) -> tuple:
    """Exit code + pichle crash times se faisla. Pure function — test me
    process chala kar nahi, seedha yehi check hota hai. `crashes` ko
    mutate NAHI karta; nayi list wapas deta hai.

    -> (kya_karo, kitne_second_ruko, naya_crash_list)
    """
    limit = config.RESTART_MAX if limit is None else limit
    if code in (config.EXIT_QUIT, config.EXIT_ALREADY_RUNNING):
        return EXIT, 0, crashes
    if code == config.EXIT_RESTART:
        return RESTART, 0, crashes        # user ne khud kaha — crash count me nahi

    recent = [t for t in crashes if now - t < span] + [now]
    if len(recent) > limit:
        return GIVE_UP, 0, recent
    return RESTART, config.backoff_for(len(recent)), recent


def supervise(max_restarts: int = None, window: int = None) -> int:
    """Child chalao, gire to dobara. -> app ka exit code"""
    limit = config.RESTART_MAX if max_restarts is None else max_restarts
    span = config.RESTART_WINDOW_SECONDS if window is None else window
    crashes = []                        # crash ke timestamps

    while True:
        config.LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CHILD_OUT, "a", encoding="ascii", errors="replace") as out:
            proc = subprocess.Popen(
                child_command(), shell=False, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            log.info("child shuru (pid=%s)", proc.pid)
            threading.Thread(target=_tee, args=(proc.stdout, out),
                             name="child-out", daemon=True).start()
            code = proc.wait()

        now = time.monotonic()
        action, wait, crashes = next_step(code, crashes, now, span, limit)

        if action == EXIT:
            log.info("child band (code=%s) — supervisor band", code)
            return code
        if code == config.EXIT_RESTART:
            log.info("tray ne restart kaha — turant dobara")
            continue
        if action == GIVE_UP:
            _console("%s BAND: %d crash %d second me. Aage chhod diya."
                     % (config.ASSISTANT_NAME, len(crashes), span))
            _console("Crash ki wajah (logs\\desktop.out): %s" % (_log_tail() or "khaali"))
            _console("Detail: logs\\prabh.log")
            return code or 1

        _console("CRASH #%d/%d (exit code %s). %d second baad dobara chalega."
                 % (len(crashes), limit, code, wait))
        if code == config.EXIT_NO_TRAY:
            _console("Wajah: tray icon nahi bana. Bina tray ke app band karna "
                     "mumkin nahi hota, is liye app ruk gaya.")
        tail = _log_tail()
        if tail:
            _console("Wajah: %s" % tail)
        time.sleep(wait)


def main() -> int:
    config.ensure_workspace()
    return supervise()


if __name__ == "__main__":
    sys.exit(main())
