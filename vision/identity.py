"""Face embedding ka **asli faisla** — pure, koi camera nahi, koi package nahi.

Ye module sirf do kaam karta hai:

1. Do embedding ki **similarity** nikalna (cosine — direction ka farq dekhta
   hai, magnitude ko nahi).
2. Us number se **verdict** dena: `OWNER` ya `UNKNOWN`.

Pure hai is liye `numpy` ke alaawa kuch nahi chahiye — yaani **bina OpenCV
install kiye poora test chal sakta hai** (jo `test_vision_id.py` karta hai).

---

## ASLI SURAKSHA KA SACH (ye padh ke hi aage badho)

Face match **asli security nahi hai.** Ek printout ya screen par dikhayi tera
photo bahut se model ko "owner" bana sakti hai — ye **anti-spoofing** ke
bina possible hai. Real raksha ke liye IR/depth ya challenge-response chahiye,
jo tere laptop ke webcam me nahi hai.

Ye feature is liye hai ki **ghar me koi aur jab computer chalu na ho**, ya
kahin aur uske saamne na baith sake — **suraksha ki ek a Layers par, asli
suraksha ki jagah nahi.**

Isi wajah se fail-safe **DENY** hai: koi bhi shak = `UNKNOWN`. Kabhi
"error aaya to chhod dete hain" nahi — wahi sabse buri galti hoti hai.

Tere project me **pehle se mazboot suraksha hai**: gatekeeper ka card, jisme
ALLOW sirf screen ka button deta hai. Wo **face se kahin zyada** mazboot hai,
kyunki awaaz ya photo se screen ka button nahi daba jaata. Dono saath chale to
sabse accha hai.
"""

import numpy as np

# Verdict — in chaar me se ek.
OWNER = "OWNER"
UNKNOWN = "UNKNOWN"
NO_FACE = "NO_FACE"      # camera par koi chehra hi nahi mila
ERROR = "ERROR"          # backend crash / embedding nahi mili

# `NO_FACE` aur `ERROR` dono **deny** karte hain (fail-safe). Ye list isi liye
# bani hai ki koi naya verdict add kare to use yahan add karna hi pade —
# warna wo chup-chaap "allow" ban jayega.
DENY_VERDICTS = (UNKNOWN, NO_FACE, ERROR)

# Cosine similarity ka default cut-off.
#
# **Ye number tune karna hai, guess nahi.** Neeche jo comments hain wo
# *theory* hain, teri machine ka number nahi. `test_vision_id.py` ye value
# pin karta hai, par **asli webcam se enroll karke hi ise sahi karo** —
# warna koi bhi tez/patliya face-match model is number par galat bolega.
#
# Face recognition ke aksar cosine 0.3-0.5 ke beech hota hai (same person
# ~0.4+, alag log <0.2). 0.40 rakh kar **pakka** rakha gaya hai: thoda
# strict, kyunki fail-safe deny hai aur galti se "owner" bolna asli nuksaan
# hai.
DEFAULT_THRESHOLD = 0.40


def normalise(vec) -> np.ndarray:
    """Vector ko unit length par laao.

    Face embeddings ka magnitude awaaz ki moode se badalta hai (mic ki tarah),
    par **direction** wahi rehta hai jo chehre ki shakal batata hai. Is liye
    cosine ke liye normalise zaroori hai — warna tez aawaz wala recording
    "alag" lagega.

    **`None` / khaali / `NaN` par KHALI array** (crash nahi). Ye galti 15-Oct ki
    test ne pakdi: `np.asarray(None, dtype=float32)` crash nahi karta, `nan`
    ka 1-element array bana deta hai — jis se verdict `NO_FACE` ke bajaye
    `UNKNOWN` ho jaata tha. Dono DENY karte hain (suraksha salamat thi), par
    **user ko galat wajah** dikhti thi. Ab `NO_FACE` sahi milta hai.

    Zero vector (sab 0) bhi khali jaisa — `0/0 = nan` se bachne ke liye.
    """
    if vec is None:
        return np.zeros(0, dtype=np.float32)
    try:
        arr = np.asarray(vec, dtype=np.float32).reshape(-1)
    except (TypeError, ValueError):
        return np.zeros(0, dtype=np.float32)
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        return np.zeros(0, dtype=np.float32)
    norm = float(np.linalg.norm(arr))
    if norm < 1e-12:
        return np.zeros(0, dtype=np.float32)      # zero vector = "kuch nahi"
    return (arr / norm).astype(np.float32)


def similarity(a, b) -> float:
    """Do embedding ka cosine similarity, `-1.0 .. 1.0`.

    Length alag ho to `0.0` (yaani "bilkul alag") — kyunki unhe compare kar
    hi nahi sakte. Ye crash na karega, sirf bol dega ki pata nahi.
    """
    va, vb = normalise(a), normalise(b)
    if va.size == 0 or vb.size == 0 or va.size != vb.size:
        return 0.0
    return float(np.dot(va, vb))


def best_score(reference, live, limit: int = 20) -> float:
    """Kayi reference embedding me se sabse achha match.

    `reference` me ek se zyada nikal sakte hain (multiple photos, alag
    roshni/angle). **Sab me se best** lena sahi hai — "sab pass hone chahiye"
    nahi, warna ek buri roshni ka sample poora feature tod de.

    `limit=20` safety hai: agar kabhi koi runaway loop bana diya list se, to
    compare bounded rahega (battery ka wahi soch — `MAX_QUEUE_BLOCKS`).
    """
    try:
        vecs = list(reference or [])[:limit]
    except TypeError:
        return 0.0
    score = 0.0
    for ref in vecs:
        score = max(score, similarity(ref, live))
    return score


def decide(reference, live, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Asli faisla. -> `{"verdict": ..., "score": ..., "threshold": ...}`.

    `reference` khali hai ya `live` nahi mili to **deny** — kyunki "pata nahi"
    aur "allow" ka koi matlab nahi.
    """
    live_arr = normalise(live)
    result = {"verdict": ERROR, "score": 0.0, "threshold": threshold}

    if live_arr.size == 0:
        result["verdict"] = NO_FACE      # embedding aa hi nahi
        return result
    if not reference:
        result["verdict"] = UNKNOWN      # enroll hi nahi hua
        return result

    score = best_score(reference, live_arr)
    result["score"] = round(score, 4)
    result["verdict"] = OWNER if score >= threshold else UNKNOWN
    return result


def allows(verdict: str) -> bool:
    """Ye verdict command chalne dega? Sirf `OWNER`.

    Ye ek jagah hai — is liye naya verdict add karna ho to yahin dikhe, aur
    "deny" bhoolna ek jagah hona chahiye, poore code me nahi."""
    return verdict == OWNER