"""Arc theme test ka SHARED plumbing — sirf helpers, koi check nahi.

Ye file 14-Oct raat me bani (`arccheck.py` 200 cross kar gaya). Do wajah
se split kiya, dono se behtar hui:

1. **Circular import.** `arccheck` (theme) aur `arc_layout` (geometry) dono ko
   `check`/`FAILED` chahiye. Ye dono ek doosre se import karte to circle
   banta. Is liye common hissa yahan hai aur dono aise import karte hain:
   `from arclib import FAILED, check` — list wahi hai (same object), is liye
   `from arccheck import FAILED` se runner ko bhi wahi milega.

**Naya niyam:** test helper kabhi **bade module me chhod ke** function ke
andar mat rakh do — doosri file use karegi to `NameError` aayega aur test
**chup-chaap** kuch kam karega ya crash hoga.

`FAILED` **module level** par hai (function ke andar nahi). Jo bhi `check()`
call karta hai, wo isi list me `append` karta hai.
"""

import tempfile
from pathlib import Path

# Fail kiye hue check ke naam. `check()` yahin append karta hai.
FAILED = []


def check(name, got, want=True):
    """Ek check — pass par OK, fail par `FAILED` me naam + line."""
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def shots_dir() -> Path:
    """Screenshot ka folder — `%TEMP%\\opencode\\hudshots`, repo ke BAHAR.

    Repo me screenshot nahi (rule: proof `%TEMP%` me).
    """
    base = Path(tempfile.gettempdir()) / "opencode" / "hudshots"
    base.mkdir(parents=True, exist_ok=True)
    return base


def wait_ready(page):
    """Arc tab POORA boot ho jaaye.

    `arc_load.js` `<head>` me hai aur CSS/JS DOMContentLoaded par lagata hai,
    is liye `load` ke turant baad `window.PRABH_ARC` shayad na bana ho. Ek
    fixed `wait_for_timeout` guess tha aur 1920x1080 par boot miss ho gaya —
    is liye ab hum **condition** ka intezaar karte hain, time ka nahi.
    """
    page.wait_for_function(
        "() => !!window.PRABH_ARC && !!document.querySelector('.a-reactor')",
        timeout=15000)
    page.wait_for_timeout(250)      # ek frame CSS/animation ke liye


def set_state(page, state):
    """Asli `setState` se call — DOM ko haath se nahi badalte.

    Neeche wale test ka asli kaam hi ye hai: ki **app ka apna** state badalne
    par UI ka label badle. DOM se `textContent` likhna sahi cheez nahi hai —
    wo sirf ye prove karega ki `textContent` kaam karta hai.
    """
    page.evaluate("(s) => window.PRABH_ARC_LIVE.setState(s)", state)


def visible_css(page, sel):
    """CSS se batao element **dikh** raha hai ya nahi.

    DOM me hona kaafi nahi — `display:none` wala bhi DOM me rehta hai. Ye
    teen hissa deta hai: `"absent"` (element hi nahi), `"none"` (style se
    chhupa), `"shown"` (dikh raha hai).
    """
    return page.evaluate(
        "() => { const el = document.querySelector(%r);"
        " if (!el) return 'absent';"
        " const d = getComputedStyle(el).display;"
        " return d === 'none' ? 'none' : 'shown'; }" % sel)