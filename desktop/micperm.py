r"""Windows ka mic permission check — app se pehle.

Windows 11 me "Let desktop apps access your microphone" ek master switch hai
(registry: `HKCU\...\CapabilityAccessManager\ConsentStore\microphone`). Off
hone par sounddevice device khol hi nahi paata aur error aata hai —
"SounddeviceError: Error opening InputStream" — jo user ko kuch nahi batata.

Is liye hum pehle registry padhte hain aur saaf Hinglish error dete hain:
mic band hai, ya ek hi baar Allow kar do.

Do jagah dekhi jati hain:
1. Master switch (`...\microphone\Value`) — 'Deny' poora mic band
2. `NonPackaged\<exe path>` — hamare python ke liye apni entry. Kuch
   versions yahan 'Allow'/'Deny' likh kar rakhte hain.

Key na mile ya padhna na ho paye to `allowed=True` — hum block nahi karte,
sirf report karte hain (user ka niyam: detect na ho to block mat kar).
"""

import winreg

import config
from log_setup import get_logger

log = get_logger("micperm")

_DENY = ("deny", "denied", "blocked", "0")


def _read_value(path: str, name: str = "Value") -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
            return str(winreg.QueryValueEx(key, name)[0]).strip().lower()
    except FileNotFoundError:
        return ""
    except OSError as exc:
        log.warning("mic permission padhi nahi ja payi (%s): %s", path, exc)
        return ""


def _nonpackaged_key(exe: str = "") -> str:
    """NonPackaged ki key ka naam: `D##jarvis#.venv#Scripts#python.exe`."""
    if not exe:
        return ""
    return f"{config.MIC_CONSENT_KEY}\\NonPackaged\\" + exe.replace("\\", "#").replace(":", "#")


def status(exe: str = "") -> tuple:
    """-> (allowed: bool, reason_for_user: str)

    `allowed=True` ka matlab "rukne ki wajah nahi mili" — iska matlab ye nahi
    ki mic zaroor khulega. Asli test audio khol kar hi hoti hai.
    """
    master = _read_value(config.MIC_CONSENT_KEY)
    if master in _DENY:
        return False, (
            "Windows me mic ki permission bandi hai. Settings > Privacy & security > "
            "Microphone > 'Let desktop apps access your microphone' ON karo."
        )

    per_app = _read_value(_nonpackaged_key(exe)) if exe else ""
    if per_app in _DENY:
        return False, (
            f"Is python ke liye mic ki permission bandi hai: {exe}. "
            "Windows me ek baar mic ki permission de do."
        )

    if master == "allow" and not per_app:
        # Master allow hai, apni entry nahi bani — matlab abhi is app ne mic
        # maanga hi nahi. Windows pehli baar khud prompt dikhata hai.
        return True, "mic ki permission abhi baaki hai (pehli baar Windows poochega)"
    return True, ""


def explain(reason: str) -> str:
    """Reason chhota karo — tray/notice me line ek ki do line se lambi nahi."""
    return (reason or "").strip().split(". ")[0][:160]
