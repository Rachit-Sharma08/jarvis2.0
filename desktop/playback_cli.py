"""`desktop/playback.py` ka CLI + device list — Step 2b ke do chhote kaam.

Ye file **split** hai (200-line niyam): asli kaam — decode, play aur `say()` —
`desktop/playback.py` me hai. Yahan sirf do cheezein hain:

1. `devices()` — saare **output** device ki list. Dhyan do: `sounddevice`
   ka `query_devices(kind="output")` **list nahi** deta, us ek default output
   device ka dict deta hai. List ke liye `query_devices()` bina argument, phir
   `max_output_channels` se filter (helper `_output_rows` wahi file me hai).
2. `main()` — `python -m desktop.playback --list | --say "Ji, boliye"`. Ye
   **asli speaker** ka test hai, app ke bina.

Speaker ka ek hi raasta phir bhi `playback.say()` hai — is file me koi naya
`sd.play`/`OutputStream` nahi, aur koi TTS provider yahan chuna nahi jaata
(awaaz hamesha `voice/tts.py` se).
"""

import config
from desktop.playback import _modules, _output_rows, available, say
from log_setup import get_logger

log = get_logger("playback")


def devices() -> list:
    """Saare output device -> [(index, name), ...]. Sirf `--list` ke liye.

    Dhyan do: `sounddevice.query_devices(kind="output")` **list nahi** deta, us
    default output device ka **ek dict** deta hai. List ke liye sab devices
    chahiye, phir `max_output_channels` se filter karo — is liye yahan
    `query_devices()` bina argument ke.

    Yahan koi **playback** nahi hai (koi `sd.play`/`OutputStream` nahi) — sirf
    query. Asli bajna hamesha `playback.say()` se hota hai.
    """
    try:
        _mini, sd = _modules()
        found = sd.query_devices()
    except Exception as exc:
        log.error("device list nahi mili: %s: %s", type(exc).__name__, exc)
        return []
    return _output_rows(found)


def main(argv: list) -> int:
    """`python -m desktop.playback` — asli speaker ka test (app ke bina)."""
    if "--list" in argv:
        rows = devices()
        if not rows:
            print("koi output device nahi mila")
            return 1
        for index, name in rows:
            print("%d  %s" % (index, name))
        return 0

    words = ""
    if "--say" in argv:
        at = argv.index("--say")
        words = " ".join(argv[at + 1:]).strip()
    if not words:
        print("usage: python -m desktop.playback --list | --say \"Ji, boliye\"")
        return 2

    ok, reason = available()
    if not ok:
        print(reason)
        return 1
    ms = say(words, config.DEFAULT_MODE)
    print("baja: %d ms" % ms if ms else "nahi baja")
    return 0 if ms else 1


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))