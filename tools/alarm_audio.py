"""Alarm ki awaaz — teen sourse, ek ke baad ek.

Sirf yeh file awaaz banati hai; `tools/wake_alarm.py` sirf loop chalata hai.
Is liye test me `--no-audio` se **ye file kabhi call hi nahi** hoti (koi asli
awaaz nahi bajti).

Order:

1. **edge-tts** (`hi-IN-SwaraNeural`) — wahi female awaaz jo Jarvis bolta hai.
   Internet chahiye; band ho to fail.
2. **Windows SAPI** (`System.Speech`) — **offline**, Hinglish me bolta hai.
3. **WAV** — `C:\\Windows\\Media\\Alarm*.wav` (Windows ka apna). Ye **bhi
   SAPI** se chalega, is liye teesra sourse bhi bina internet ke hai.

System volume **chhedte nahi** — Rachit ne 70% par rakha hai, aur code volume
ko chhu hi nahi sakta (audiodevice ka default device use hota hai).
"""

import asyncio
import io
import subprocess
import sys
from pathlib import Path

from log_setup import get_logger

log = get_logger("alarm_audio")

WINDOWS_MEDIA = Path(r"C:\Windows\Media")
VOICE = "hi-IN-SwaraNeural"
HIDE = 0x08000000          # CREATE_NO_WINDOW - pythonw/console dono theek

# Do bhasha: edge-tts (Hindi, Jarvis wali female awaaz) aur SAPI fallback
# (romanized — Hindi font/SAPI par depend nahi karta). Text **yahan** ek jagah
# hai: `tools/wake_alarm.py` aur `tools/alarm.py` dono yahin se lete hain.
TEXT_HI = "सुबह हो गई है सर। सात बज गए हैं, उठने का समय हो गया है।"
TEXT_HINGLISH = ("Good morning sir. Saat baj gaye hain, "
                 "uthne ka samay ho gaya hai.")

# PowerShell ka ek-liner: offline TTS. `-WindowStyle Hidden` + CREATE_NO_WINDOW
# dono lagte hain taaki console na khule.
_SAPI = (
    "Add-Type -AssemblyName System.Speech; "
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
    "$s.Rate = 0; $s.Volume = 100; $s.SetOutputToDefaultAudioDevice(); "
    "$s.Speak($args[0])"
)

# `System.Media.SoundPlayer` — WAV ke liye, offline, alag process nahi chahiye.
_PLAYER = (
    "Add-Type -AssemblyName System.Windows.Forms; "
    "$p = New-Object System.Media.SoundPlayer $args[0]; "
    "$p.PlaySync()"
)


def alarm_wav(first: str = "Alarm01.wav") -> str:
    """Windows ka apna alarm wav — `''` agar dhoondh na mile."""
    want = WINDOWS_MEDIA / first
    if want.exists():
        return str(want)
    found = sorted(WINDOWS_MEDIA.glob("Alarm*.wav"))
    return str(found[0]) if found else ""


def edge_tts(text: str, voice: str = VOICE) -> bytes:
    """edge-tts se MP3 bytes. Fail (internet nahi) par `b''` — crash nahi."""
    try:
        import edge_tts
    except ImportError:
        log.warning("edge_tts module nahi hai")
        return b""

    async def run():
        out = b""
        comm = edge_tts.Communicate(text, voice)
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                out += chunk["data"]
        return out

    try:
        data = asyncio.run(run())
    except Exception as exc:                      # noqa: BLE001 - koi bhi net error
        log.warning("edge-tts fail: %s: %s", type(exc).__name__, exc)
        return b""
    log.info("edge-tts audio: %d bytes", len(data))
    return data


def sapi_speak(text: str) -> bool:
    """Windows ki apni offline awaaz (SAPI). -> chala ya nahi."""
    try:
        done = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-WindowStyle", "Hidden", "-Command", _SAPI, text],
            shell=False, capture_output=True, timeout=60, creationflags=HIDE,
        )
    except Exception as exc:                      # noqa: BLE001
        log.warning("SAPI fail: %s: %s", type(exc).__name__, exc)
        return False
    ok = done.returncode == 0
    log.info("SAPI bol diya: %s", ok)
    return ok


def play_bytes(audio: bytes) -> bool:
    """MP3/WAV bytes -> speaker (sounddevice + miniaudio, offline)."""
    if not audio:
        return False
    try:
        import miniaudio
        import numpy as np
        import sounddevice as sd
        decoded = miniaudio.decode(
            audio, output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=1, sample_rate=32000)
        pcm = np.asarray(decoded.samples, dtype="<i2")
        sd.play(pcm, samplerate=32000)
        sd.wait()
    except Exception as exc:                      # noqa: BLE001
        log.warning("speaker fail: %s: %s", type(exc).__name__, exc)
        return False
    return True


def play_wav(path: str) -> bool:
    """WAV file chalao. `System.Media.SoundPlayer` — bina extra package ke."""
    if not path or not Path(path).exists():
        log.warning("alarm wav nahi mila: %r", path)
        return False
    try:
        done = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-WindowStyle", "Hidden", "-Command", _PLAYER, path],
            shell=False, capture_output=True, timeout=120, creationflags=HIDE,
        )
    except Exception as exc:                      # noqa: BLE001
        log.warning("wav player fail: %s: %s", type(exc).__name__, exc)
        return False
    log.info("alarm wav bajaya: %s (%d bytes)", path, Path(path).stat().st_size)
    return done.returncode == 0


def speak(text: str, sapi_text: str = "") -> str:
    """Bolo — edge-tts pehle, na chala to SAPI. -> kaunsa chala ('none' agar dono fail)."""
    if play_bytes(edge_tts(text)):
        return "edge-tts"
    if sapi_speak(sapi_text or text):
        return "sapi"
    log.error("dono TTS fail - sirf baj rahe hain")
    return "none"


if __name__ == "__main__":                        # sirf check: python -m tools.alarm_audio
    print(f"wav = {alarm_wav()}")
    print(f"python = {sys.executable}")
