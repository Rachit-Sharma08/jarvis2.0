"""Computer vision — owner ko pehchan, taki koi aur na bol kar kaam karwa sake.

Ye package 15-Oct raat me bana (owner ka plan: "computer vision add karo jisse
ye mujhe owner ko pehchan sake"). Char file, har ek kaam alag:

| File | Kaam |
|---|---|
| `identity.py` | **pure** matching + verdict (koi camera nahi) |
| `store.py`    | embedding ka ghar — `data/owner_face.npz` (gitignored) |
| `backend.py`  | asal CV library (OpenCV/InsightFace) — lazy, optional |
| `enroll.py`   | registration ka flow (ek hi raasta) |

---

## ⚠️ TEENO SACH — inhe padh ke hi use karna

**1. Ye ASLI SECURITY nahi hai.** Ek printout ya screen par dikhayi photo
bahut se model ko "owner" bana sakti hai (anti-spoofing bina). Asli raksha ke
liye IR/depth chahiye jo laptop me nahi. Ye ek **aLayers par suraksha** hai.

**2. Tere project me pehle se isse MAZBOOT suraksha hai** — gatekeeper ka card,
jahan ALLOW sirf screen ka button deta hai. Photo se wo button nahi daba jaata.
Face ko **aLayers par** rakhna, card ke **upar** karna galat hoga.

**3. Fail-safe DENY hai.** Koi chehra nahi, backend crash, store kharab — sab
me se kuch bhi shak ho to `UNKNOWN`/`ERROR`, aur dono **deny** karte hain.
Kabhi "error aaya to chhod dete hain" nahi — wahi sabse buri galti hai.

Aur ek plain baat: **abhi ye kaam nahi kar sakta.** Is PC par `opencv-python`
/ `insightface` install nahi hain, is liye har command **deny** hoti hai (jo
theek hai — koi allow to ho nahi rahi). Install ke baad `enroll()` se tera
chehra register karna hoga. Details `enroll.py` ke docstring me.
"""

from vision.identity import (  # noqa: F401  (re-export — ek hi import darwaza)
    DEFAULT_THRESHOLD, DENY_VERDICTS, ERROR, NO_FACE, OWNER, UNKNOWN,
    allows, best_score, decide, normalise, similarity,
)
from vision.store import (  # noqa: F401
    enrolled, forget, load, save, status,
)

__all__ = [
    "OWNER", "UNKNOWN", "NO_FACE", "ERROR", "DENY_VERDICTS",
    "DEFAULT_THRESHOLD", "allows", "decide", "similarity", "best_score",
    "normalise", "save", "load", "enrolled", "forget", "status",
]