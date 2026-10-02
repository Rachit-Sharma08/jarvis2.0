"""Vosk model ka ek hi raasta — load karna, aur saaf Hinglish error.

Model ka folder `config_wake.model_path()` se aata hai (`.env` se nahi). `vosk`
import late hota hai taaki app startup tez rahe aur test me model load hi na ho
(wahan fake model daala jaata hai).

Load karna ~1 second leta hai aur worker ke loop me bahut baar nahi chahiye —
is liye model cache hota hai. `clear()` sirf test ke liye hai.
"""

import config
from log_setup import get_logger

log = get_logger("wake_model")

_CACHE = {}


class ModelMissing(RuntimeError):
    """Model nahi hai ya khul nahi paaya. Ye reason user ko dikhana hai."""


def load(folder: str = ""):
    """Vosk `Model` object. Pehli baar banata hai, phir cache se wahi deta hai."""
    path = folder or config.model_path()
    if not path:
        raise ModelMissing(config.model_missing())
    if path in _CACHE:
        return _CACHE[path]
    try:
        from vosk import Model, SetLogLevel
        SetLogLevel(-1)
        model = Model(path)
    except ModelMissing:
        raise
    except Exception as exc:
        raise ModelMissing("Vosk model khul nahi paya (%s): %s"
                           % (path.replace("\\", "/").split("/")[-1], exc)) from exc
    _CACHE[path] = model
    log.info("vosk model ready: %s", path.replace("\\", "/").split("/")[-1])
    return model


def cached() -> bool:
    """Model abhi memory me hai? (log + `--wake-info` ke liye)"""
    return bool(_CACHE)


def clear() -> None:
    """Cache khaali karo. Sirf test me."""
    _CACHE.clear()
