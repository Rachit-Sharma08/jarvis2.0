"""Face backend — asal computer-vision library yahan aati hai, aur **sirf** yahan.

Is module ka ek kaam hai: `detect(frame)` se face bounding boxes, aur
`embed(face_img)` se 128-float ka vector. Baaki sab (`identity.py`,
`store.py`, `enroll.py`) in dono par sirf in do function ke upar tikka hai.

**Ye file jaan-boojh kar lazy import karti hai.** `import vision` karte hi
`cv2` load **nahi** hota — sirf jab sach me camera kholna ho tab. wajah: is
project me har test `import config` karta hai aur app startup par bhi CV nahi
chahiye; bhaari import har test me 1-2 s ghaata.

---

## Abhi ki haalat: package **install nahi** hai

Is PC par abhi `opencv-python`, `insightface`, `mediapipe`, `dlib` — koi bhi
nahi hai. Is liye `get_backend()` **pakka `None` deta hai** aur har verdict
`ERROR` jaata hai, jo **DENY** hai (fail-safe).

Ye jaan-boojh kar hai: "package nahi hai" ka matlab "sab chhod do" nahi, balki
**"kuch bhi allow mat karo"**. Warna ek laptop par camera nahi hone se feature
chalta hua dikhta aur security andar se khaali rehti.

Install (admin nahi chahiye, `D:\prabh\.venv` me):
    .\\.venv\\Scripts\\python.exe -m pip install opencv-python insightface onnxruntime
`insightface` + `onnxruntime` asli recognition dete hain; sirf `opencv` se
sirf **detection** hoti hai (koi hai ya nahi), "**WOHI** hai kya" — nahi.
"""

from log_setup import get_logger

log = get_logger("vision.backend")

# Baad me camera se kitne face ek frame me dekhne hain. Zyada = battery.
MAX_FACES = 1


class Backend:
    """Ek backend ka interface — teen method, teen ka matlab.

    Ye **protocol jaisa** hai (Python 3.8 me `typing.Protocol` bhi sahi hai,
    par simple class se zyada saaf rehta hai aur test me nakli banane me
    aasan hai).
    """

    name = "base"

    def available(self) -> bool:
        """Camera + library dono hain? Nahi to har call `False`."""
        return False

    def detect(self, frame):
        """Frame (numpy image) -> `[{"box": (x, y, w, h), "score": float}]`.

        Koi chehra nahi mila to **khali list** (crash nahi).
        """
        raise NotImplementedError

    def embed(self, face_img):
        """Chehre ka image -> 128-float embedding, ya `None`."""
        raise NotImplementedError

    def describe(self) -> str:
        """Log/HUD ke liye ek line."""
        return "backend nahi hai"


class OpenCvBackend(Backend):
    """`opencv-python` + `insightface` se FaceAnalysis.

    Ye sirf tab banega jab dono import ho sakein. `FaceAnalysis` **khud model
    download** karta hai pehli baar (~300 MB, `.insightface/` me, kabhi
    commit nahi hota) — is liye pehli baar internet chahiye, uske baad offline.
    """

    name = "opencv+insightface"

    def __init__(self, det_max_num: int = MAX_FACES):
        self._app = None
        self._det_max = det_max_num

    def available(self) -> bool:
        if self._app is None:
            try:
                from insightface.app import FaceAnalysis
            except Exception as exc:
                log.info("insightface nahi mila: %s", type(exc).__name__)
                return False
            try:
                self._app = FaceAnalysis(name="buffalo_l")
                # `ctx_id=-1` = CPU. CUDA maango ki GPU ho — i5 par CPU hi
                # theek hai aur crash se behtar.
                self._app.prepare(ctx_id=-1, det_size=(320, 320))
            except Exception as exc:
                log.warning("FaceAnalysis taiyar nahi hua: %s", type(exc).__name__)
                self._app = None
                return False
        return True

    def detect(self, frame):
        if not self.available():
            return []
        try:
            faces = self._app.get(frame, max_num=self._det_max)
        except Exception as exc:
            log.warning("detect crash: %s", type(exc).__name__)
            return []
        return [{"box": tuple(int(v) for v in f.bbox), "score": float(f.det_score)}
                for f in faces]

    def embed(self, face_img):
        if not self.available():
            return None
        try:
            faces = self._app.get(face_img, max_num=self._det_max)
        except Exception:
            return None
        for f in faces:
            vec = getattr(f, "normed_embedding", None)
            if vec is not None:
                return [float(v) for v in vec]
        return None

    def describe(self) -> str:
        return ("opencv+insightface (CPU)" if self.available()
                else "opencv+insightface — library ya model missing")


_BACKEND = None
_TRIED = False


def get_backend():
    """Ek hi backend banao. Install nahi hai ya crash hua to **None**.

    Result cache hota hai (`_TRIED`) — taaki har `allowed()` par dobara
    import na lage. `reset()` sirf **test** ke liye hai.
    """
    global _BACKEND, _TRIED
    if not _TRIED:
        _TRIED = True
        try:
            import cv2  # noqa: F401  (import hi kaafi hai — link check)
        except Exception:
            log.info("opencv-python install nahi hai — vision band rahega (DENY)")
            _BACKEND = None
        else:
            _BACKEND = OpenCvBackend()
    return _BACKEND


def reset() -> None:
    """Sirf test ke liye — cache saaf, agli baar dobara try."""
    global _BACKEND, _TRIED
    _BACKEND = None
    _TRIED = False


def status() -> dict:
    """HUD/debug: library hai? backend bana? enrolled? (koi raw data nahi)"""
    backend = get_backend()
    ready = bool(backend and backend.available())
    return {"library": ready, "backend": backend.describe() if backend else "none",
            "ready": ready}