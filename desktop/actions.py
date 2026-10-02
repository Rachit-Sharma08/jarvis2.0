"""Tray ke 5 button — `desktop/app.py` se alag, kyunki ye sirf faisla (decision)
karta hai aur app ke haath se kaam karwata hai. `desktop/tray.py` dumb hai.

Yahi class `desktop/tray.py` ko menu deti hai.
"""

import config
from desktop.state import STATE
from gatekeeper import keeper
from log_setup import get_logger

log = get_logger("actions")


class Actions:
    def __init__(self, app):
        self.app = app

    def toggle_mute(self) -> None:
        muted = STATE.toggle_muted()
        STATE.set_mic(config.TRAY_MUTED if muted else config.TRAY_OFF,
                      "user ne mute kiya")
        log.info("tray: mic mute=%s", muted)

    def open_hud(self) -> None:
        self.app.hud.open()
        STATE.set_hud(True)

    def toggle_tools(self) -> None:
        on = keeper.set_tools(not keeper.tools_on())
        log.info("tray: TOOLS=%s (auto-OFF %d min me)",
                 on, config.TOOLS_AUTO_OFF_MINUTES)

    def restart(self) -> None:
        log.info("tray: restart maanga")
        self.app.stop(config.EXIT_RESTART)

    def quit(self) -> None:
        log.info("tray: quit maanga")
        self.app.stop(config.EXIT_QUIT)