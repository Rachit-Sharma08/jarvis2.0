"""`python -m desktop.open_hud` - Desktop shortcut aur hotkey dono ka raasta.

Sirf ek kaam: **server zinda hai to HUD window khol do.**

- Server chalu hai -> `desktop/hud_window.py` ka `--app` window (wahi profile,
  wahi URL). Doosri baar bulao to naya window nahi banta, purana focus ho
  jaata hai - is liye shortcut aur hotkey dono safe hain.
- Server nahi hai -> kuch nahi khulta, magar user ko pata chal jaata hai.
  `pythonw.exe` se chalta hai (console nahi dikhta), is liye message
  **message box** me jaata hai + `logs/jarvis.log`.

Ye alag process hai, is liye app ke `STATE` ko chhua nahi - DESKTOP pill
app wale process me hi rehta hai.
"""

import sys

import config
from desktop import hud_window
from desktop.single import http_alive
from log_setup import get_logger

log = get_logger("open_hud")

EXIT_OK = 0
EXIT_NO_BROWSER = 1
EXIT_SERVER_DOWN = 2

DOWN_MESSAGE = (
    "%s abhi chal nahi raha.\n\n"
    "Pehle %s\\start_jarvis.bat chalao (wahi rakha hai), phir ye "
    "shortcut dobara dabao." % (config.ASSISTANT_NAME, config.BASE_DIR)
)
NO_BROWSER_MESSAGE = (
    "HUD kholne ke liye Edge ya Chrome nahi mila.\n\n"
    "Ek inme se install karo, phir ye shortcut dobara dabao."
)


def plan(server_up: bool) -> tuple:
    """Sirf faisla, koi side effect nahi - test yahi check karta hai.
    -> (action, message) jahan action 'open' ya 'down'."""
    return ("open", "") if server_up else ("down", DOWN_MESSAGE)


def tell(message: str) -> None:
    """`pythonw` par console nahi hota - message box dikhao. Na mile to print."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, config.TRAY_NAME, 0x40)
    except Exception as exc:
        log.warning("message box nahi khula: %s", exc)
        print(message, flush=True)


def main() -> int:
    up = http_alive(config.SERVER_ORIGIN)
    action, message = plan(up)
    if action == "down":
        log.warning("HUD nahi khuli - server %s par nahi hai", config.SERVER_ORIGIN)
        tell(message)
        return EXIT_SERVER_DOWN
    window = hud_window.HudWindow()
    if not window.available():
        log.error("Edge/Chrome nahi mila - HUD nahi khulegi")
        tell(NO_BROWSER_MESSAGE)
        return EXIT_NO_BROWSER
    if not window.open():
        log.error("HUD kholne me dikkat aayi")
        tell(NO_BROWSER_MESSAGE)
        return EXIT_NO_BROWSER
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())