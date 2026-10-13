"""PCM/gain test ka shared helper — `check()` + `FAILED`.

Ye 14-Oct raat me bani jab `test_wake_resample.py` 200 cross kar gaya aur gain
ke test alag file me gaye. `check()` do jagah chahiye tha — agar dono file me
alag-alag likh dete to ek ka badlav doosre me na dikhta.

**Kaam: sirf `check()` + `FAILED` list.** Koi test, koi config, koi `.env`
nahi — is liye ye `logsafe` se PEHLE import ho sakta hai ( dono file me
`logsafe` pehle hi aa raha hai ).
"""

# Fail kiye hue check ke naam. `check()` yahin append karta hai.
FAILED = []


def check(name, got, want=True):
    """Ek check — pass par OK, fail par `FAILED` me naam + line."""
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def gain_value(g):
    """`RmsGain` ya `FixedGain` ka applied gain float me.

    `RmsGain.g` float hai, `FixedGain.applied` bhi — par test dono classes
    ek hi jagah pass karta hai, is liye ye chhota helper beech me rakha hai
    (test ke andar `if hasattr(...)` baar baar nahi).
    """
    return float(getattr(g, "g", None) if hasattr(g, "g") else g.applied)