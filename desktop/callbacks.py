"""Desktop ke 4 callback — Win+L, TOOLS badlav, wake word, Ctrl+Alt+S.

Ye `desktop/app.py` se alag kyun: app.py orchestration hai (kya kab chalta
hai), ye **haalaat ka matlab** hai (callback aaya to kya badlav hoga). Chaaron
ka ek hi raasta hai — app ka object pass hota hai aur ye usi ke haath se kaam
karwate hain, koi naya Engine/STATE nahi banata.

Step 2c ke liye teen chhote helper bhi yahin hain: `allowed` (mute/lock ka
faisla), `_busy` (HUD ka WAKE pill) aur `on_wake` (command chalao).

Test me inhe seedha call kiya ja sakta hai (asli tray/hotkey/wake nahi chalti).
"""

import config
from desktop import lockwatch
from desktop.state import STATE
from gatekeeper import keeper
from log_setup import get_logger
from wake import command
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


def allowed() -> tuple:
    """Command (Step 2c) chalega ya nahi. -> (bool, reason).

    Do pakkaure: **mic MUTE** aur **PC lock**. Dono me na recording hoti hai na
    koi awaaz — chup-chaap kuch nahi, sirf `logs/prabh.log` me ek line.

    Ye `wake/command.py` me `desktop/` ka import nahi karwata — wake module ko
    halka rakhne ke liye faisla yahan se callback ke roop me bheja jaata hai."""
    if STATE.muted():
        return False, "mic mute hai"
    if lockwatch.is_locked():
        return False, "PC lock hai"
    return True, ""


def _busy(busy: bool) -> None:
    """Command chal raha hai -> HUD ka WAKE pill `busy`. Band -> wapas `listening`.

    Ye sirf **display** hai. Asli rokna `wake/worker.py` ka `hold_for_command()`
    karta hai — yahan se kuch control nahi hota, warna wake/desktop do jagah se
    control ho jaate (AGENTS.md: ek hi raasta)."""
    if busy:
        STATE.set_wake("busy")
    else:
        STATE.set_wake(config.TRAY_LISTENING if wake_worker.listening()
                       else config.TRAY_OFF)


def on_wake(phrase: str, mic=None, stop=None, _app=None) -> None:
    """Wake mila — Step 2c: HUD + poori command.

    Step 1 me yahan sirf HUD khulta tha. Ab `wake/command.py` poori flow chalata
    hai: "Ji, boliye" -> mic suno -> Groq STT -> shared ENGINE -> jawab ki awaaz.

    `mic` aur `stop` `wake/session.py` ke `_fire()` se aate hain. Teeno callback
    (`allowed`, `on_confirm`, `on_busy`) yahin se jaate hain — `wake/` ko
    `desktop/` ka import nahi karna padta."""
    log.info("WAKE HIT: %r", phrase)
    hud = getattr(_app, "hud", None)
    if hud is not None:
        hud.open()
    STATE.set_hud(True)
    command.run(mic, stop, allowed=allowed,
                on_confirm=lambda: on_hotkey(_app), on_busy=_busy)


def on_hotkey(app=None) -> None:
    """Global hotkey (default Ctrl+Alt+S) — wake jaisa hi kaam: HUD kholo."""
    log.info("HOTKEY HIT: %s", config.HUD_HOTKEY)
    hud = getattr(app, "hud", None)
    if hud is not None:
        hud.open()
    STATE.set_hud(True)
