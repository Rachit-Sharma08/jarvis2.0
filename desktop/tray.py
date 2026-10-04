"""Tray icon + menu (pystray).

Menu chhota hai, jaisa user ne kaha tha:
  - halaat ki ek line (badge, click nahi hota)
  - Mute
  - Open HUD
  - TOOLS ON / OFF
  - Restart
  - Quit

Tray apna faisla **khud nahi** leta. Har item `actions` object ka method
bulaata hai (`desktop/app.py` banata hai). Is liye ye file test me bina
pystray chalu kiye pure logic check ho jaati hai.

Icon ka rang `desktop/state.py` se aata hai — mic ka nishaan har state me
rehta hai, sirf rang badalta hai.
"""

import threading
import time

import pystray
from pystray import Menu, MenuItem

import config
from desktop import hotkey as hotkey_mod
from desktop import trayicon
from desktop.state import STATE
from log_setup import get_logger

log = get_logger("tray")


def retry_start(tray, attempts: int = 3, delay: float = 1.5, sleep=None) -> bool:
    """`tray.start()` ko `attempts` baar try karo — beech me `delay` ruko.

    `pystray` kabhi kabhi pehli koshish me chhoot deta hai (Explorer restart, D:
    slow disk). Ye alag function is liye hai ki test me `sleep` daal kar
    bina asli wait kiye check ho jaaye.
    """
    wait = time.sleep if sleep is None else sleep
    for n in range(1, max(1, attempts) + 1):
        if tray.start():
            return True
        if n < attempts:
            log.warning("tray koshish %d/%d fail - %s second baad phir",
                        n, attempts, delay)
            wait(delay)
    return False


class Tray:
    def __init__(self, actions, state=None):
        self.actions = actions
        self.state = state or STATE
        self._icon = None
        self._lock = threading.Lock()

    # ---- menu ----
    def build(self) -> Menu:
        state = self.state
        keys = hotkey_mod.describe(config.HUD_HOTKEY)
        return Menu(
            MenuItem(
                lambda item: config.tray_title(state.mic()),
                None, enabled=False,
            ),
            Menu.SEPARATOR,
            MenuItem(
                "Mic Mute",
                self._toggle_mute,
                checked=lambda item: state.muted(),
            ),
            MenuItem(
                # ZAROORI: `default=True` sirf **ek** item par hona chahiye.
                # pystray left-click (WM_LBUTTONUP) par default item chalata
                # hai (`_win32.py:200` -> `_base.py:108`). `Quit` par default
                # tha to **ek click = app band** (4-Oct ko hua bhi). Ab click
                # se HUD khulta hai; Quit sirf menu se.
                "Open HUD", self._open_hud, default=True),
            # Hotkey dikhana zaroori hai - warna user ko pata hi nahi chalta
            # ki ek aur raasta hai. Sirf text, click se kuch nahi hota.
            MenuItem("  ya phir %s" % (keys or "koi shortcut nahi"),
                     None, enabled=False),
            # Battery: "so jao" = sirf mic chalu. Jaagta hai wake word se.
            MenuItem(
                config.SLEEP_FROM_TRAY if not state.asleep() else "JAAG JAAO",
                self._toggle_sleep,
            ),
            MenuItem(
                "TOOLS",
                self._toggle_tools,
                checked=lambda item: state.snapshot()["tools_on"],
            ),
            Menu.SEPARATOR,
            MenuItem("Restart", self._restart),
            MenuItem("Quit", self._quit),
        )

    # ---- chalao ----
    def start(self) -> bool:
        """Tray message loop alag thread me. Main thread azaad rehta hai."""
        with self._lock:
            if self._icon is not None:
                return True
            # pystray ka teesra argument tooltip hai — wo user ko dikhta hai,
            # isliye naam `config.TRAY_TITLE` se aata hai (Step 1: Jarvis).
            self._icon = pystray.Icon(
                config.TRAY_NAME, trayicon.image(self.state.mic()),
                config.tray_title(self.state.mic()), self.build(),
            )
        try:
            self._icon.run_detached(setup=self._on_setup)
        except Exception as exc:
            log.error("tray start nahi hua: %s: %s", type(exc).__name__, exc)
            self._icon = None
            return False
        log.info("tray shuru (%s)", config.TRAY_NAME)
        return True

    def start_retry(self, attempts: int = 3, delay: float = 1.5) -> bool:
        """Icon pehli koshish me na bane to 2-3 baar phir try karo."""
        return retry_start(self, attempts, delay)

    def stop(self) -> None:
        with self._lock:
            icon, self._icon = self._icon, None
        if icon is not None:
            try:
                icon.stop()
            except Exception as exc:
                log.warning("tray stop: %s", exc)

    def refresh(self) -> bool:
        """Icon + menu dobara banao. State badli ho tabhi (version check)."""
        with self._lock:
            if self._icon is None:
                return False
            try:
                self._icon.icon = trayicon.image(self.state.mic())
                self._icon.menu = self.build()
                self._icon.update_menu()
            except Exception as exc:
                log.warning("tray refresh: %s", exc)
                return False
        return True

    # ---- item callbacks (pystray thread) ----
    def _on_setup(self, icon) -> None:
        # ZAROORI: pystray tabhi `visible = True` khud karta hai jab `setup`
        # callback na diya ho. `setup` diya to sirf `setup(icon)` chalta hai -
        # icon **invisible** reh jaata hai: `NIM_ADD` chala tha (registry entry
        # banti hai) par shell use taskbar me render **nahi** karta.
        # Isi wajah se tray menu kuch bhi karne par band lagta tha.
        icon.visible = True
        log.info("tray ready")

    def _toggle_mute(self, icon, item) -> None:
        self._guard(self.actions.toggle_mute)

    def _open_hud(self, icon, item) -> None:
        self._guard(self.actions.open_hud)

    def _toggle_tools(self, icon, item) -> None:
        self._guard(self.actions.toggle_tools)

    def _toggle_sleep(self, icon, item) -> None:
        self._guard(self.actions.toggle_sleep)

    def _restart(self, icon, item) -> None:
        self._guard(self.actions.restart)

    def _quit(self, icon, item) -> None:
        self._guard(self.actions.quit)

    def _guard(self, func) -> None:
        """Tray crash kare to app na gire — sirf log."""
        try:
            func()
        except Exception as exc:
            log.error("tray item fail: %s: %s", type(exc).__name__, exc, exc_info=True)
        self.refresh()
