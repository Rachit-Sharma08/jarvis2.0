"""Sunne ka end-to-end saboot - asli awaaz, asli model, asli text.

**Kyun:** baaki STT tests fake model par chalte hain. Wo chain to pakadte hain,
par "JARVIS sach me sun raha hai?" ka jawab nahi dete. Ye suite Windows SAPI se
ek vaakya bolwati hai, usko `stt.transcribe()` se guzarti hai, aur shabd milate
hain.

Model ya SAPI na ho to **SKIP** (suite fail nahi hota) - CI/doosre PC par bhi
green rahe. Asli model ek baar load hota hai (~4 s), phir 2-3 s audio ~6 s.
"""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import asyncio  # noqa: E402

import config  # noqa: E402
from tests.wakehelp import FAILED, check, finish  # noqa: E402
from voice import stt, stt_local  # noqa: E402

PHRASE = "Jarvis open WhatsApp and send a message"
# SAPI jo shabd bolti hai wahi wapas aane chahiye. Chhote shabd (and/the) chhod
# diye - Whisper unhe kabhi jodta hai kabhi nahi, aur test flaky ho jata.
WANT = ("jarvis", "open", "whatsapp", "send", "message")


def say(text: str) -> bytes | None:
    """Windows SAPI se WAV. SAPI na ho to None."""
    path = os.path.join(tempfile.gettempdir(), "jarvis_hear_e2e.wav")
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.SetOutputToWaveFile('{path}'); "
        f"$s.Speak('{text}'); $s.Dispose()"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       check=True, capture_output=True, timeout=60)
        data = Path(path).read_bytes()
        Path(path).unlink(missing_ok=True)
        return data or None
    except Exception:
        return None


def words(text: str) -> set:
    return {w.strip(".,!?").lower() for w in text.split()}


def main() -> None:
    if not stt_local.available():
        print("SKIP: local model nahi mila (models/faster-whisper-small)")
        finish("e2e hearing skip")

    audio = say(PHRASE)
    if not audio:
        print("SKIP: Windows SAPI nahi chala")
        finish("e2e hearing skip")

    saved = config.STT_LOCAL
    config.STT_LOCAL = "local"
    try:
        start = time.perf_counter()
        text = asyncio.run(stt.transcribe(audio, duration_ms=4000))
        took = time.perf_counter() - start
    finally:
        config.STT_LOCAL = saved

    print(f"  suna: {text!r} ({took:.1f}s)")
    got = words(text)
    missing = [w for w in WANT if w not in got]
    check(f"saare shabd mile (missing: {missing or 'koi nahi'})", missing, [])
    # 30 s ka ceiling hai; asli audio 3 s ka hai, to 20 s se zyada = kuch galat.
    check(f"20s se tez ({took:.1f}s)", took < 20, True)

    if FAILED:
        finish("e2e hearing FAIL")
    finish("e2e hearing theek - asli awaaz se asli text")


if __name__ == "__main__":
    main()
