"""`python main.py --doctor` - ek command me "kya chalega?" ka jawab.

Owner coding nahi jaanta, aur "Jarvis sunta nahi / jawab nahi deta" ka asli
kaaran har baar alag hota hai (key, model, mic, port). Ye file har hissa alag
se jaanchti hai aur **saaf Hinglish** me batati hai kya theek hai aur kya nahi.

Rule: yahan kuch **shuru nahi** hota (na server, na mic stream). Sirf padhta
hai - is liye chalte hue app ke saath bhi safe hai.
"""

import socket

import config
from log_setup import get_logger

log = get_logger("doctor")

OK, WARN, BAD = "OK  ", "WARN", "FAIL"


def _line(mark: str, what: str, detail: str = "") -> tuple:
    print(f"  [{mark}] {what}" + (f" - {detail}" if detail else ""))
    return mark, what, detail


def _brain() -> list:
    out = []
    if config.has_groq():
        out.append(_line(OK, "Brain (jawab)", "Groq key mili"))
    elif config.has_gemini():
        out.append(_line(OK, "Brain (jawab)", "Gemini key mili"))
    else:
        out.append(_line(BAD, "Brain (jawab)", ".env me koi API key nahi"))
    return out


def _stt() -> list:
    from voice import stt
    which = stt.provider()
    if which == "groq":
        return [_line(OK, "Sunna (STT)", "Groq cloud")]
    if which == "local":
        return [_line(OK, "Sunna (STT)", "local faster-whisper (free/offline)")]
    return [_line(BAD, "Sunna (STT)",
                  "na Groq key na local model - JARVIS behra rahega")]


def _wake() -> list:
    from pathlib import Path
    out = []
    if not config.WAKE_ENABLED:
        out.append(_line(WARN, "Wake word", "JARVIS_WAKE=0 se band hai"))
        return out
    if not Path(config.WAKE_MODEL_DIR).is_dir():
        out.append(_line(BAD, "Wake word", f"Vosk model nahi: {config.WAKE_MODEL_DIR}"))
        return out
    out.append(_line(OK, "Wake word", "'Hlo Jarvis' sunega (Vosk, offline)"))
    return out


def _mic() -> list:
    try:
        import sounddevice as sd
        info = sd.query_devices(kind="input")
        name = str(info.get("name", "?"))[:40]
        rate = int(info.get("default_samplerate", 0))
        return [_line(OK, "Mic", f"{name} ({rate} Hz)")]
    except Exception as exc:
        return [_line(BAD, "Mic", f"input device nahi mila ({exc})")]


def _port() -> list:
    """Port free hai? Bind karke turant band - kuch sunta nahi."""
    with socket.socket() as sock:
        sock.settimeout(0.3)
        busy = sock.connect_ex((config.SERVER_HOST, config.SERVER_PORT)) == 0
    if busy:
        return [_line(OK, "Server", f"pehle se chal raha hai ({config.SERVER_ORIGIN})")]
    return [_line(OK, "Server", f"port {config.SERVER_PORT} khaali hai")]


def _tools() -> list:
    from gatekeeper import keeper
    state = "ON" if keeper.tools_on() else "OFF"
    return [_line(OK, "Tools", f"{state} (trust mode)")]


def run() -> int:
    """Saare hisse jaancho. -> 0 sab theek, 1 kuch critical toota."""
    print(f"\n{config.ASSISTANT_NAME} doctor - kya chalega?\n")
    rows = []
    for part in (_brain, _stt, _wake, _mic, _port, _tools):
        try:
            rows.extend(part())
        except Exception as exc:                       # noqa: BLE001
            rows.append(_line(BAD, part.__name__.strip("_"), str(exc)))

    bad = [what for mark, what, _detail in rows if mark == BAD]
    warn = [what for mark, what, _detail in rows if mark == WARN]
    print()
    if bad:
        print(f"  Natija: {len(bad)} cheez tooti - {', '.join(bad)}")
        print("  Upar wali line padho; .env aur models/ wahi kaaran batate hain.")
        return 1
    if warn:
        print(f"  Natija: chalega, par dhyan do - {', '.join(warn)}")
        return 0
    print("  Natija: sab theek. 'Hlo Jarvis' bolo, HUD khulega.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
