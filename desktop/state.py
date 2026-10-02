"""Desktop shell ki ek hi jagah se haalat — tray, HUD aur wake worker teeno
yahan se padhte hain.

Teenon ko alag rakhne ka matlab: tray ka rang aur HUD ka mic pill alag-alag
ho sakte hain. Is liye ek hi `STATE` hai aur sab usi se padhte hain.

`publish()` WebSocket hub par `desktop` event bhejta hai — `ui/hud_desktop.js`
use karta hai. Ye sirf state hai (mic on/mute/error, tools, HUD window),
koi secret nahi.
"""

import threading

from log_setup import get_logger
from server.hub import HUB

log = get_logger("desktop_state")

MIC_STATES = ("off", "idle", "listening", "muted", "error")


class DesktopState:
    def __init__(self):
        self._lock = threading.Lock()
        self._mic = "off"
        self._mic_reason = ""
        self._muted = False
        self._tools_on = False
        self._hud_open = False
        self._wake_state = "off"     # Step 1 me stub; baad me wake worker bharega
        self._version = 0

    # ---- padhna ----
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "mic": self._mic,
                "mic_reason": self._mic_reason,
                "muted": self._muted,
                "tools_on": self._tools_on,
                "hud_open": self._hud_open,
                "wake": self._wake_state,
                "version": self._version,
            }

    def mic(self) -> str:
        with self._lock:
            return self._mic

    def muted(self) -> bool:
        with self._lock:
            return self._muted

    def version(self) -> int:
        """Badlav hua ya nahi — tray icon sirf tab refresh karta hai jab badle."""
        with self._lock:
            return self._version

    # ---- badalna ----
    def set_mic(self, state: str, reason: str = "") -> bool:
        """Mic ka haalat. `state` MIC_STATES me se hona chahiye."""
        if state not in MIC_STATES:
            raise ValueError(f"bad mic state: {state}")
        with self._lock:
            changed = self._mic != state or self._mic_reason != reason
            self._mic, self._mic_reason = state, reason
            if changed:
                self._version += 1
        if changed:
            log.info("mic: %s%s", state, f" ({reason})" if reason else "")
        self.publish()
        return changed

    def set_muted(self, on: bool) -> bool:
        with self._lock:
            changed = self._muted != bool(on)
            self._muted = bool(on)
            if changed:
                self._version += 1
        if changed:
            log.info("mute: %s", "ON" if self._muted else "OFF")
        self.publish()
        return changed

    def toggle_muted(self) -> bool:
        """Mute palat de. -> mute ke baad ka naya haalat (True = ab mute hai)"""
        self.set_muted(not self.muted())
        return self.muted()

    def set_tools(self, on: bool) -> bool:
        with self._lock:
            changed = self._tools_on != bool(on)
            self._tools_on = bool(on)
            if changed:
                self._version += 1
        self.publish()
        return changed

    def set_hud(self, is_open: bool) -> bool:
        with self._lock:
            changed = self._hud_open != bool(is_open)
            self._hud_open = bool(is_open)
            if changed:
                self._version += 1
        self.publish()
        return changed

    def set_wake(self, value: str) -> bool:
        """Wake worker ki apni halaat (off / listening / heard / busy / error)."""
        with self._lock:
            changed = self._wake_state != value
            self._wake_state = value
            if changed:
                self._version += 1
        self.publish()
        return changed

    # ---- HUD tak bhejna ----
    def event(self) -> dict:
        """WebSocket ka `desktop` event. Naye client ko bhi yahi bhejte hain."""
        return {"type": "desktop", "data": self.snapshot()}

    def publish(self) -> None:
        """WebSocket clients ko `desktop` event. Exception kabhi nahi uthata."""
        try:
            HUB.publish(self.event())
        except Exception as exc:      # hub band ho to app bhi na gire
            log.warning("desktop publish fail: %s: %s", type(exc).__name__, exc)


STATE = DesktopState()
