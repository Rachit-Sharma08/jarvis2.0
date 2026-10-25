"""Owner ka chehra register karo — `python -m vision.enroll`.

Ye **ek hi raasta** hai registration ka. Koi doosra raasta nahi banaya gaya
(taaki kabhi do alag enrollment na ho sakein, jinke beech ka owner kabhi na
mile — bilkul `wake/` ka "mic ka ek hi owner" wala pakkaura).

Chalane ka tareeka:
    .\\.venv\\Scripts\\python.exe -m vision.enroll
    .\\.venv\\Scripts\\python.exe -m vision.enroll --forget

**Pehle ye zaroori hai:** `opencv-python` + `insightface` install ho, warna
seedha "backend nahi hai" bolkar ruk jaata hai (aur kuch bhi likhta nahi).

---

## Privacy ke 4 pakkaure

1. **Recording disk par kabhi nahi jaati.** Frame sirf `bytearray` me memory
   me hai. Enrollment khatam ya cancel hone par wo `bytearray` **khali** kar
   di jaati hai. Ye `.env` wali niyam hai — camera par bhi.
2. **Sirf embedding bachti hai**, photo nahi. 128 float ka ek vector, jisse
   photo **reconstruct nahi** hoti. File `data/owner_face.npz` me hai —
   gitignored, aur `SECRET_FILE_NAMES` me BLOCKED.
3. **Internet par kuch nahi jaata.** Model pehli baar khud download hota hai
   (`.insightface/`), uske baad sab offline.
4. **Raw frame log me bhi nahi** — sirf "kitne sample mila" likha jaata hai.

`--forget` sab mita deta hai (`store.forget()`). User ka haq hai.

---

## Registration kaisi hoti hai

Camera khulti hai, aur jitne frames me **chehra milta hai** (chaaron andaaron
kaam karte hain — do alag model embedding nahi de sakte, warna match kabhi
nahi hoga), unka embedding `store.save()` me **jod** diya jaata hai. Jodta
hai, is liye 2-3 baar enroll karne se accuracy behtar hoti hai (alag
roshni/angle).

`ENROLL_SAMPLES` (default 15) tak **rukta nahi** — jitne mile utne le leta
hai. Is ka matlab: agar roshni kharab hai aur 2 hi sample mile, wo bhi save
ho jaate hain (behtar hai 2 se kuch nahi).
"""

import sys
import time

import config_vision
from log_setup import get_logger

log = get_logger("vision.enroll")

MAX_WAIT_SECONDS = 90        # isse zyada wait karne ka koi matlab nahi


def capture_frames(cap, wanted, on_frame=None):
    """Camera se embedding ke liye frames jodo. -> list of embeddings.

    `cap` = khuli `cv2.VideoCapture`. Har frame: detect karo, chehra ho to
    embed karo. Ye `on_frame(count)` ko bhejta hai taaki CLI progress dikha
    sake (test me `None`).

    Embedding **kahin store ya disk me nahi** jaati yahan — sirf list me,
    aur caller turant `store.save()` karta hai.
    """
    got, out = [], []
    started = time.monotonic()
    while len(out) < wanted and (time.monotonic() - started) < MAX_WAIT_SECONDS:
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        faces = _backend().detect(frame) if _backend() else []
        if not faces:
            continue
        box = faces[0].get("box")
        if not box or len(box) != 4:
            continue
        x, y, w, h = [int(v) for v in box]
        crop = frame[max(0, y): y + h, max(0, x): x + w]
        if getattr(crop, "size", 0) == 0:
            continue
        vec = _backend().embed(crop)
        if vec is None:
            continue
        out.append(vec)
        if on_frame:
            on_frame(len(out))
    log.info("enroll: %d/%d sample", len(out), wanted)
    return out


def _backend():
    """Ek hi backend, har call par (backend `None` ho to skip)."""
    from vision import backend
    return backend.get_backend()


def _open_camera():
    """Khuli camera. Nahi khuli to `None`."""
    try:
        import cv2
    except Exception as exc:
        print("opencv-python install nahi hai. "
              "pip install opencv-python insightface onnxruntime")
        log.info("cv2 nahi: %s", type(exc).__name__)
        return None
    cap = cv2.VideoCapture(config_vision.CAMERA_INDEX)
    if not cap.isOpened():
        cap.release()
        print("camera nahi khul rahi (index %d). Camera busy hai ya "
              "permission nahi?" % config_vision.CAMERA_INDEX)
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config_vision.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config_vision.CAMERA_HEIGHT)
    return cap


def enroll() -> int:
    """Registration ka main flow. -> 0 = hua, 1 = nahi hua."""
    from vision import store

    be = _backend()
    if be is None or not be.available():
        print("CV backend nahi hai (library/model missing) — kuch nahi hua.")
        print("Pehle: pip install opencv-python insightface onnxruntime")
        return 1

    cap = _open_camera()
    if cap is None:
        return 1

    wanted = max(1, config_vision.ENROLL_SAMPLES)
    print("Camera khul gayi. Seedha dekho — %d sample lene hain." % wanted)
    print("Beech me Esc daba do ya band kar do — kuch bhi nahi bachega.")

    buf = []
    try:
        buf = capture_frames(cap, wanted, on_frame=lambda n: print(
            "  sample %d/%d" % (n, wanted)))
    except KeyboardInterrupt:
        print("\nRuka. Kuch bhi save nahi hua.")
        return 1
    finally:
        # Camera hamesha chhod do — warna agli baar "busy" milega.
        try:
            cap.release()
        except Exception:
            pass

    if not buf:
        print("Koi chehra nahi mila — kuch nahi hua. Roshni check karo.")
        return 1

    n = store.save(buf, meta={"when": time.strftime("%Y-%m-%d %H:%M")})
    buf = []                      # memory se hata do (privacy)
    if n:
        print("\nHo gaya: %d sample save (data/owner_face.npz)." % n)
        print("Ab .env me likho:  JARVIS_VISION=1")
        print("Phir Jarvis restart. HUD par VISION: ON dikhna chahiye.")
        return 0
    print("Save nahi hua (sample galat size ka tha).")
    return 1


def forget() -> int:
    from vision import store
    store.forget()
    print("Owner ki face embedding mita di. (VISION ON rakhna ho to "
          "dobara enroll karo.)")
    return 0


def status() -> int:
    from vision import backend, store
    st = store.status()
    bs = backend.status()
    print("enrolled : %s (%d sample, dim %s)" % (
        st["enrolled"], st["count"], st["dim"] or "-"))
    print("backend  : %s" % bs.get("backend", "none"))
    print("JARVIS_VISION = %s (default 0 = OFF)" % config_vision.VISION_ENABLED)
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--forget" in argv:
        return forget()
    if "--status" in argv:
        return status()
    return enroll()


if __name__ == "__main__":
    sys.exit(main())