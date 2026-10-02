"""Desktop ke 4 callback — Win+L, TOOLS badlav, wake word, Ctrl+Alt+S.

Ye `desktop/app.py` se alag kyun: app.py orchestration hai (kya kab chalta
hai), ye **haalaat ka matlab** hai (callback aaya to kya badlav hoga). Chaaron
ka ek hi raasta hai — app ka object pass hota hai aur ye usi ke haath se kaam
karwate hain, koi naya Engine/STATE nahi banata.

Test me inhe seedha call kiya ja sakta hai (asli tray/hotkey/wake nahi chalti).
"""

import config
from desktop.state import STATE
from gatekeeper import keeper
from log_setup import get_logger
from wake import worker as wake_worker

log = get_logger("desktop_callbacks")


def on_lock(_app=None) -> None:
    """Win+L — sirf baat-cheet. TOOLS apne aap OFF. ALLOW ka raasta badalta
    nahi: card ka jawab sirf UI button se aata hai, wake se nahi.

    Wake **chalta rehta** hai (AGENTS.md ka niyam) — sirf kaam band hota hai.
    Is liye pill tab bhi 'listening' dikhta hai, sirf wajah badal jaati hai."""
    if keeper.tools_on():
        keeper.set_tools(False)             # STATE hook khud update karega
        log.warning("Windows lock hua - TOOLS apne aap OFF")
    STATE.set_mic(
        config.TRAY_LISTENING if wake_worker.listening() else config.TRAY_OFF,
        "PC lock hai")


def on_tools_change(on: bool, _app=None) -> None:
    """`gatekeeper.Limiter` ka hook — TOOLS kahin se bhi badle (tray, HUD
    button, lock, 30-min timer), haalat yahin se jaata hai. `app.py` ka loop
    is state ke badlav par tray icon refresh kar deta hai."""
    STATE.set_tools(bool(on))


def on_wake(phrase: str, _app=None) -> None:
    """Wake mila. Step 1 me sirf HUD kholta hai — command sunna, TTS se
    'Ji, boliye' bolna aur uske baad brain Step 2 ka kaam hai.

    Shortcut aur wake dono ka ek hi raasta: `hud.open()`."""
    log.info("WAKE HIT: %r", phrase)
    hud = getattr(_app, "hud", None)
    if hud is not None:
        hud.open()
    STATE.set_hud(True)


def on_hotkey(app=None) -> None:
    """Global hotkey (default Ctrl+Alt+S) — wake jaisa hi kaam: HUD kholo."""
    log.info("HOTKEY HIT: %s", config.HUD_HOTKEY)
    hud = getattr(app, "hud", None)
    if hud is not None:
        hud.open()
    STATE.set_hud(True)
