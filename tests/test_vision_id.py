"""Face matching ka pure hissa — bina camera, bina CV package.

`identity.py` sirf `numpy` chhuta hai, is liye ye test bina `opencv` /
`insightface` ke chalta hai. Ye jaan-boojh kar rakha gaya hai: ek feature ka
**core** (math + faisla) tabhi sahi maana jaata hai jab usse pakda ja sake —
baaki integration ek baar me sahi hone ki guarantee nahi.

Ye teen baatein pin karta hai:
1. **Fail-safe DENY** — `NO_FACE`/`ERROR`/`UNKNOWN` teeno deny karte hain.
2. **Koi chehra nahi = owner nahi** — `live` khaali ya `reference` khaali ho
   to kabhi `OWNER` nahi (naive code me yahi bug hota hai).
3. **`normalise` magic** — magnitude change kare to bhi same verdict (cosine
   ki wajah — ye property hi embedding ko kaam karati hai).
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tests.pcmhelp import FAILED, check  # noqa: E402
from vision import identity  # noqa: E402


def vec(*vals):
    """Deterministic test vector banao (random flaky test banata hai)."""
    return np.array(vals, dtype=np.float32)


def base(n=8, seed=1.0):
    """Ek fixed shape — sab test isi par derivatives banate hain."""
    return np.linspace(seed, seed + 1.0, n, dtype=np.float32)


def test_same_person_matches():
    """Wahi chehra (chhota farak) -> OWNER."""
    ref = [base(8, 1.0)]
    live = base(8, 1.0) + 0.001              # bilkul wahi
    r = identity.decide(ref, live)
    check("wahi = OWNER", r["verdict"], identity.OWNER)
    check("score ~1", round(r["score"], 2), 1.0)


def test_different_person_rejected():
    """Alag direction -> UNKNOWN (score low)."""
    ref = [base(8, 1.0)]
    live = np.array([1, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32) * 0.3
    r = identity.decide(ref, live)
    check("alag = UNKNOWN", r["verdict"], identity.UNKNOWN)


def test_magnitude_does_not_matter():
    """Gain badalne par bhi same verdict — ye `normalise` ki wajah hai.

    Face embedding ka magnitude mic/roshni se badalta hai; sirf direction
    shakal batata hai. Agar ye na hota to tez recording "alag" lagti."""
    ref = [base(8, 1.0)]
    quiet = base(8, 1.0) * 0.01
    loud = base(8, 1.0) * 50.0
    v_quiet = identity.decide(ref, quiet)["verdict"]
    v_loud = identity.decide(ref, loud)["verdict"]
    check("dheemi = OWNER", v_quiet, identity.OWNER)
    check("zor bhi = OWNER", v_loud, identity.OWNER)


def test_no_face_denies():
    """Chehra nahi mila (embedding khaali) -> NO_FACE + DENY."""
    r = identity.decide([base(8, 1.0)], [])
    check("khaali live = NO_FACE", r["verdict"], identity.NO_FACE)
    check("NO_FACE deny karta hai", identity.allows(r["verdict"]), False)


def test_no_enrollment_denies():
    """Enroll hi nahi hua -> UNKNOWN + DENY (OWNER kabhi nahi)."""
    r = identity.decide([], base(8, 1.0))
    check("khaali ref = UNKNOWN", r["verdict"], identity.UNKNOWN)
    check("UNKNOWN deny karta hai", identity.allows(r["verdict"]), False)


def test_none_inputs_safe():
    """`None` aaye to crash nahi, deny."""
    check("None ref", identity.decide(None, base())["verdict"], identity.UNKNOWN)
    check("None live", identity.decide([base()], None)["verdict"], identity.NO_FACE)
    check("None dono", identity.decide(None, None)["verdict"], identity.NO_FACE)


def test_length_mismatch_is_unknown():
    """Alag lambai ke vectors compare nahi ho sakte -> 0 score, deny.

    Chehra mila hai (embedding valid hai, sirf lambai alag — yaani shayad **do
    alag model** chal rahe hain), is liye `UNKNOWN`, `NO_FACE` nahi. Dono DENY
    karte hain, par user ko dikhne wali wajah alag hai."""
    ref = [base(8, 1.0)]
    live = base(16, 1.0)                  # valid, par 8 ke bajaye 16 lambai
    check("length mismatch score 0", identity.similarity(ref[0], live), 0.0)
    check("length mismatch = UNKNOWN",
          identity.decide(ref, live)["verdict"], identity.UNKNOWN)


def test_best_of_many_references():
    """Kayi reference me se sabse achha — ek badla sample poora feature tod
    na de. Ye `min` nahi, `max` hai."""
    good = base(8, 1.0)
    bad = base(8, 1.0) * -1.0               # bilkul ulat
    ref = [bad, good]
    live = good + 0.002
    check("best of many = OWNER", identity.decide(ref, live)["verdict"],
          identity.OWNER)
    check("sab match karne wala bhi OWNER",
          identity.decide([good, good], live)["verdict"], identity.OWNER)


def test_zero_vector_is_not_a_match():
    """Zero vector (sab 0) kisi se bhi match nahi hona chahiye.

    Ye sneaky case hai: `0/0 = nan` aa kar comparison chhoot jaata hai. Is liye
    `normalise()` zero vector ko **khali** bana deti hai, jisse verdict
    `NO_FACE` aata hai ("koi valid embedding nahi") — jo DENY hai.

    Naive code me ye `nan` banna hai aur `>=` comparison `False` dekar
    chup-chaap deny kar deta hai — sahi nateeja, galat wajah. Ya worse, koi
    `not (x >= t)` likh de to `nan` par **allow** ho jaata."""
    ref = [base(8, 1.0)]
    zeros = np.zeros(8, dtype=np.float32)
    check("zero vector khaali ho gaya", identity.normalise(zeros).size, 0)
    check("zero vector score", identity.similarity(ref[0], zeros), 0.0)
    check("zero vector deny", identity.allows(
        identity.decide(ref, zeros)["verdict"]), False)
    check("zero vector = NO_FACE",
          identity.decide(ref, zeros)["verdict"], identity.NO_FACE)


def test_only_owner_allows():
    """`allows()` sirf OWNER. Ye ek jagah hai — naya verdict yahin dikhe."""
    for v in (identity.OWNER, identity.UNKNOWN, identity.NO_FACE, identity.ERROR):
        check("allows(%s)" % v, identity.allows(v), v == identity.OWNER)
    check("ERROR deny me hai", identity.ERROR in identity.DENY_VERDICTS, True)
    check("sab deny me hain",
          all(v in identity.DENY_VERDICTS
              for v in (identity.UNKNOWN, identity.NO_FACE, identity.ERROR)), True)


def main():
    for fn in (test_same_person_matches, test_different_person_rejected,
               test_magnitude_does_not_matter, test_no_face_denies,
               test_no_enrollment_denies, test_none_inputs_safe,
               test_length_mismatch_is_unknown, test_best_of_many_references,
               test_zero_vector_is_not_a_match, test_only_owner_allows):
        print(f"       {fn.__name__}")
        fn()
    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        return 1
    print("face matching (pure, bina camera) theek")
    return 0


if __name__ == "__main__":
    sys.exit(main())