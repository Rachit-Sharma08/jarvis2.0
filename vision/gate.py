"""Wake command ka **vision guard** — `desktop/callbacks.allowed()` ka teesra check.

Mute aur lock ke **baad** ye chalta hai (do rakshak pehle se hain). Ye wahi
interface hai — `(bool, reason)` — taaki `allowed()` me sirf do line lage.

---

## Fail-safe ka poora faisla (ye padh ke hi on karo)

| Halaat | Verdict | Command |
|---|---|---|
| `JARVIS_VISION=0` (default) | — | **CHALTI** (pehle jaisa) |
| Vision ON + camera khuli + owner match | `OWNER` | **CHALTI** |
| Vision ON + chehra hi nahi dikha | `NO_FACE` | ruk (`TOO_FAST`) |
| Vision ON + koi aur chehra | `UNKNOWN` | ruk (`NOT_OWNER`) |
| Vision ON + camera/library/model missing | `ERROR` | **ruk** |
| Vision ON + **koi bhi exception** | `ERROR` | **ruk** |

Do baatein jaan-boojh kar:
- **Exception bhi DENY hai** (`ERROR`). `except` me "chhod dete hain" likhna
  sabse buri galti hai — security tabhi security hai jab haar par bhi band rahe.
- **Default me feature OFF hai**, is liye `allowed()` par koi camera nahi khulta.
  Ek dict lookup ke baad wapas. Battery aur privacy dono safe.

Is module me `try/except` sirf **logging** ke liye hai, verdict ke liye nahi —
`vision.identity.decide()` hi ek hi jagah faisla leti hai.
"""

import config_vision
from log_setup import get_logger
from vision import backend, identity, store

log = get_logger("vision.gate")

# Wake ke turant baad har command pe camera check. Bahut tez hona chahiye —
# 2 s ka wait user ko "hang" lagega. `0.8` ek pichhla (live tune karo).
COOLDOWN_SECONDS = 0.8

_last_check = None          # (monotonic, verdict)
_capture = None             # test me inject karne ka raasta (closure)


def set_capture(fn):
    """Sirf test: camera capture badal do. `None` = wapas asli."""
    global _capture
    _capture = fn


def _grab():
    """Ek frame pakdo. `None` matlab camera/library nahi (ya error).

    Yahan `cv2.VideoCapture` khulta hai — aur **har** failure `None` deta hai
    (device busy, permission nahi, driver nahi). Exception nahi nikalti."""
    if _capture is not None:
        return _capture()
    try:
        import cv2
    except Exception:
        return None
    cap = None
    try:
        cap = cv2.VideoCapture(config_vision.CAMERA_INDEX)
        if not cap.isOpened():
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config_vision.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config_vision.CAMERA_HEIGHT)
        ok, frame = cap.read()
        return frame if ok and frame is not None else None
    except Exception as exc:
        log.warning("camera pakadte hue: %s", type(exc).__name__)
        return None
    finally:
        # Device hamesha chhod do — warna agli baar "busy" milega.
        try:
            if cap is not None:
                cap.release()
        except Exception:
            pass


def _embed(frame):
    """Frame se chehra ka embedding. Kuch na mile to `None`."""
    be = backend.get_backend()
    if be is None or not be.available():
        return None
    try:
        faces = be.detect(frame)
    except Exception:
        return None
    if not faces:
        return None
    box = faces[0].get("box")
    if not box or len(box) != 4:
        return None
    x, y, w, h = [int(v) for v in box]
    crop = frame[max(0, y): y + h, max(0, x): x + w]
    if getattr(crop, "size", 0) == 0:
        return None
    try:
        return be.embed(crop)
    except Exception:
        return None


def _reason_for(verdict):
    if verdict == identity.UNKNOWN:
        return config_vision.NOT_OWNER
    if verdict == identity.NO_FACE:
        return config_vision.TOO_FAST
    if verdict == identity.ERROR:
        return config_vision.NEEDS_CAMERA
    return ""


def check(force: bool = False) -> tuple:
    """Command chalega? -> `(bool, reason)` — `allowed()` ke wahi shape.

    `force=True` sirf test/enroll ke liye hai (cooldown skip)."""
    if not config_vision.VISION_ENABLED and not force:
        return True, ""                     # default: bilkul pehle jaisa

    reference, _meta = store.load()
    if not reference:
        return False, config_vision.NEEDS_ENROLL

    frame = _grab()
    if frame is None:
        log.info("vision: camera nahi mili -> DENY")
        return False, config_vision.NEEDS_CAMERA

    live = _embed(frame)
    if live is None:
        # Chehra mila hi nahi — `NO_FACE` (deny). `ERROR` nahi, kyunki camera
        # to chali; bas is frame par koi nahi tha.
        log.info("vision: koi chehra nahi -> DENY")
        return False, config_vision.TOO_FAST

    threshold = config_vision.VISION_THRESHOLD or identity.DEFAULT_THRESHOLD
    result = identity.decide(reference, live, threshold)
    if identity.allows(result["verdict"]):
        log.info("vision: owner match (score=%.3f)", result["score"])
        return True, ""
    log.info("vision: %s (score=%.3f < %.3f)", result["verdict"],
             result["score"], threshold)
    return False, _reason_for(result["verdict"])