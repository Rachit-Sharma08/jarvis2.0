"""'So jao' — battery ke liye bhaari sab band, sirf mic + gate chalu.

Mic ka stream kabhi band nahi hota (AGENTS ka duty-cycle niyam), is liye battery
ka bachat "sunao band karke" nahi, **baaki sab band karke** milta hai:

| | Jaga hai | Bhaari hissa |
|---|---|---|
| Normal | sab | HUD window (browser), stats pump, weather, brain |
| **So jao** | mic + gate + tray | HUD band, `asleep=True`, brain nahi |

Wake word phir bhi chalta hai — `desktop/callbacks.on_wake()` sleep hatakar
wahi purana kaam kar deta hai (HUD khulta hai + command chalta hai). Is liye
"Jarvis" bolte hi app jaag jaata hai.

**Poora band (CPU 0) sirf tray ke Quit se** — uske baad "Jarvis" kaam nahi
karega, kyunki sunne wala koi nahi bachega. Mic sunna band karna = "Hlo Jarvis"
ka feature hi jaa jaana.

`matches()` pure hai (test me bina app ke), baaki do kaam `enter`/`wake_up`
haalaat badalte hain — dono ek hi jagah se (`STATE`).
"""

import config
from desktop.state import STATE
from log_setup import get_logger

log = get_logger("desktop_sleep")


def matches(text: str) -> bool:
    """'So jao' / 'sone jao' / 'band ho jao' hai kya? Pure — `config.SLEEP_WORDS`.

    Chhota guard: text chhota ho (sirf 3 shabd se kam), warna "band ho jao kya
    matlab hai" jaisa vaakya galti se app sone ki taraf le jaaye.
    """
    low = (text or "").strip().lower()
    if not low or len(low.split()) > 4:
        return False
    return any(word in low for word in config.SLEEP_WORDS)


def enter(app=None) -> bool:
    """So jao — HUD band, haalat set. -> sach me badla ya nahi.

    Brain/JHUD ki koi nayi shuruaat nahi hoti; sirf HUD window band hoti hai
    (wohi asli bhaari hissa hai — browser ka apna CPU).
    """
    hud = getattr(app, "hud", None)
    if hud is not None:
        try:
            hud.close()
        except Exception as exc:      # band na bhi ho to so jana rehna chahiye
            log.warning("sleep me HUD band nahi hua: %s: %s", type(exc).__name__, exc)
    changed = STATE.set_asleep(True)
    STATE.set_hud(False)
    log.info("SO GAYA (mic + gate chalu, baaki band)")
    return changed


def wake_up(app=None) -> bool:
    """Jaag gaya — sirf flag hatta hai. HUD/command ka kaam `on_wake` karta hai."""
    changed = STATE.set_asleep(False)
    if changed:
        log.info("jaag gaya (asleep OFF)")
    return changed


def toggle(app=None) -> bool:
    """Tray ka item — abhi so raha hai to jaag jao, warna so jao. -> naya haalat
    (`True` = ab so raha hai)."""
    if STATE.asleep():
        wake_up(app)
        return False
    enter(app)
    return True