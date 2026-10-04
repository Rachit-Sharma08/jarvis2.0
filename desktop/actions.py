"""Tray ke 5 button — `desktop/app.py` se alag, kyunki ye sirf faisla (decision)
karta hai aur app ke haath se kaam karwata hai. `desktop/tray.py` dumb hai.

Yahi class `desktop/tray.py` ko menu deti hai.
"""

import config
from desktop import sleep as sleep_mod
from desktop.state import STATE
from gatekeeper import keeper
from log_setup import get_logger
from wake import worker as wake_worker

log = get_logger("actions")


class Actions:
    def __init__(self, app):
        self.app = app

    def toggle_mute(self) -> None:
        """Mute palat de. Ek hi raasta: pehle `STATE`, phir wake worker ko
        pause, phir mic ka haalat wahi hisaab se — mic ka asli owner wake
        worker hai (Step 1), is liye unmute par 'listening' hi sahi hai."""
        muted = STATE.toggle_muted()
        wake_worker.set_paused(muted)
        if muted:
            mic_state, reason = config.TRAY_MUTED, "user ne mute kiya"
        elif wake_worker.listening():
            mic_state, reason = config.TRAY_LISTENING, "wake sun raha hai"
        else:
            mic_state, reason = config.TRAY_OFF, "mic band"
        STATE.set_mic(mic_state, reason)
        log.info("tray: mic mute=%s", muted)

    def open_hud(self) -> None:
        self.app.hud.open()
        STATE.set_hud(True)

    def toggle_tools(self) -> None:
        on = keeper.set_tools(not keeper.tools_on())
        # Auto-off ab band hai (0), is liye 'X min me OFF' jaisa text sirf tab
        # sahi hoga jab user `.env` me PRABH_TOOLS_AUTOOFF de rakhe ho.
        log.info("tray: TOOLS=%s%s", on,
                 "" if not config.TOOLS_AUTO_OFF_MINUTES
                 else " (auto-OFF %d min me)" % config.TOOLS_AUTO_OFF_MINUTES)

    def toggle_sleep(self) -> None:
        """'So jao' palat de. Sirf mic + gate chalta rahega, HUD band. Jaagne ka
        ek hi raasta: wake word (ya ye same item) — `desktop/sleep.py`."""
        asleep = sleep_mod.toggle(self.app)
        log.info("tray: so jao=%s", asleep)

    def restart(self) -> None:
        log.info("tray: restart maanga")
        self.app.stop(config.EXIT_RESTART)

    def quit(self) -> None:
        log.info("tray: quit maanga")
        self.app.stop(config.EXIT_QUIT)