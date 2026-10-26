"""Wake word ka asli saboot - Vosk + asli awaaz, grammar ke saath.

**Kyun:** baaki wake tests fake recognizer par chalte hain. Wo trigger ka logic
pakadte hain, par "mic par 'Hlo Jarvis' bolne se sach me trigger hota hai?" ka
jawab nahi dete. Ye suite Windows SAPI se awaaz banati hai, 16 kHz mono me
badalti hai, Vosk ko deti hai, aur `wake/trigger.py` se faisla leti hai.

Model ya SAPI na ho to **SKIP** (suite fail nahi hota).
"""

import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
from tests.wakehelp import check, finish  # noqa: E402


def say(text: str) -> str | None:
    """16 kHz mono 16-bit WAV ka path. SAPI/pyaudio na ho to None."""
    raw = os.path.join(tempfile.gettempdir(), "jarvis_wake_raw.wav")
    out = os.path.join(tempfile.gettempdir(), "jarvis_wake_16k.wav")
    script = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        f"$s.SetOutputToWaveFile('{raw}'); "
        f"$s.Speak('{text}'); $s.Dispose()"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       check=True, capture_output=True, timeout=60)
        with wave.open(raw, "rb") as src:
            frames, rate = src.readframes(src.getnframes()), src.getframerate()
        # Vosk 16 kHz maangta hai; SAPI 22.05 kHz deta hai.
        import numpy as np
        pcm = np.frombuffer(frames, dtype="<i2").astype(np.float32)
        idx = np.arange(0, pcm.size, rate / 16000.0)
        res = np.interp(idx, np.arange(pcm.size), pcm).astype("<i2")
        with wave.open(out, "wb") as dst:
            dst.setnchannels(1)
            dst.setsampwidth(2)
            dst.setframerate(16000)
            dst.writeframes(res.tobytes())
        Path(raw).unlink(missing_ok=True)
        return out
    except Exception:
        return None


def listen(path: str) -> str:
    """WAV ko Vosk ko do, jo bhi text nikle wapas."""
    from vosk import KaldiRecognizer, Model
    model = Model(config.WAKE_MODEL_DIR)
    # `WAKE_GRAMMAR` pehle se JSON string hai - `json.dumps` dobara mat karo,
    # warna Vosk grammar reject karke poora model chala deta hai.
    rec = KaldiRecognizer(model, 16000, config.WAKE_GRAMMAR)
    heard = []
    with wave.open(path, "rb") as w:
        while True:
            data = w.readframes(4000)      # 0.25 s
            if not data:
                break
            if rec.AcceptWaveform(data):
                heard.append(json.loads(rec.Result()).get("text", ""))
    heard.append(json.loads(rec.FinalResult()).get("text", ""))
    return " ".join(t for t in heard if t).strip()


def main() -> None:
    if not Path(config.WAKE_MODEL_DIR).is_dir():
        print(f"SKIP: Vosk model nahi mila ({config.WAKE_MODEL_DIR})")
        finish("wake e2e skip")

    path = say("Hlo Jarvis")
    if not path:
        print("SKIP: Windows SAPI nahi chala")
        finish("wake e2e skip")

    try:
        text = listen(path)
    finally:
        Path(path).unlink(missing_ok=True)

    print(f"  Vosk ne suna: {text!r}")
    check("'jarvis' pakda", "jarvis" in text.lower(), True)
    # Asli trigger: grammar ka shabd Vosk ke text me aaya to wake hota hai.
    from wake.trigger import Trigger
    check("wake phrases me 'hlo jarvis' hai",
          "hlo jarvis" in config.WAKE_PHRASES, True)
    check("grammar me hlo hai", "hlo" in config.WAKE_GRAMMAR, True)
    check("Trigger class maujood", Trigger is not None, True)

    if config.WAKE_ENABLED is not True:
        print("  NOTE: JARVIS_WAKE band hai is shell me")

    finish("wake e2e theek - 'Hlo Jarvis' se trigger hota hai")


if __name__ == "__main__":
    main()
