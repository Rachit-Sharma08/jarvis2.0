"""Asli app — server + tray + HUD + wake, sab ek process me.

Layout:
  - main thread      : intezaar + shutdown
  - "server" thread  : uvicorn (FastAPI) — wahi `server.app`
  - "lockwatch"      : Win+L ka pata
  - "wake" thread    : `wake/worker.py` (Step 3a me stub)
  - pystray thread   : tray menu

Ek hi process is liye ki engine ek hi rahe (`server/state.py`) — browser,
quick button aur wake teeno ka mode aur gatekeeper state ek jaisa.

Supervisor alag hai (`desktop/launcher.py`): crash par wahi dobara chala
deta hai. Yahan crash ka Exit code `config.EXIT_RESTART` se jaata hai.
"""

import sys
import threading
import time

import uvicorn

import config
from core import sysstats
from desktop import hud_window, lockwatch, micperm, single as single_mod
from desktop.state import STATE
from desktop.tray import Tray
from gatekeeper import keeper
from log_setup import get_logger
from wake import worker as wake_worker

log = get_logger("app")


class Actions:
    """Tray ke 5 button. Faisla yahan hota hai, `desktop/tray.py` dumb hai."""

    def __init__(self, app: "SundayApp"):
        self.app = app

    def toggle_mute(self) -> None:
        muted = STATE.toggle_muted()
        STATE.set_mic(config.TRAY_MUTED if muted else config.TRAY_OFF, "user ne mute kiya")
        log.info("tray: mic mute=%s", muted)

    def open_hud(self) -> None:
        self.app.hud.open()
        STATE.set_hud(True)

    def toggle_tools(self) -> None:
        on = keeper.set_tools(not keeper.tools_on())
        STATE.set_tools(on)
        log.info("tray: TOOLS=%s (auto-OFF %d min me)", on, config.TOOLS_AUTO_OFF_MINUTES)

    def restart(self) -> None:
        log.info("tray: restart maanga")
        self.app.stop(config.EXIT_RESTART)

    def quit(self) -> None:
        log.info("tray: quit maanga")
        self.app.stop(config.EXIT_QUIT)


class SundayApp:
    def __init__(self, open_hud_at_start: bool = False):
        self.hud = hud_window.HudWindow()
        self.tray = Tray(Actions(self))
        self.lock = single_mod.Single()
        self.server = None
        self._stop = threading.Event()
        self._code = config.EXIT_QUIT

    # ---- chalana ----
    def run(self) -> int:
        config.ensure_workspace()
        try:
            self.lock.acquire()
        except single_mod.AlreadyRunning as exc:
            log.warning("app pehle se chal raha hai: %s", exc)
            return config.EXIT_ALREADY_RUNNING

        try:
            self._preflight()
            self._start_server()
            self._start_tray()
            self._start_watchers()
            if not self.hud.available():
                log.error("Edge/Chrome nahi mila — HUD nahi khulega (baaki sab chalega)")
            if config.HUD_OPEN_AT_START or open_hud_at_start:
                self.tray_actions().open_hud()
            self._wait()
        finally:
            self._shutdown()
        return self._code

    def stop(self, code: int = None) -> None:
        self._code = config.EXIT_QUIT if code is None else code
        self._stop.set()

    def tray_actions(self) -> Actions:
        return self.tray.actions

    # ---- hisse ----
    def _preflight(self) -> None:
        allowed, reason = micperm.status(sys.executable)
        if not allowed:
            STATE.set_mic(config.TRAY_ERROR, micperm.explain(reason))
            log.error("mic band hai: %s", reason)
        else:
            log.info("mic permission: %s", reason or "theek hai")

    def _start_server(self) -> None:
        from server.app import app as fastapi_app      # import late: config ready ho

        sysstats.prime()
        self.server = uvicorn.Server(uvicorn.Config(
            fastapi_app, host=config.SERVER_HOST, port=config.SERVER_PORT,
            log_level="warning", access_log=False,
        ))
        threading.Thread(target=self.server.run, name="server", daemon=True).start()
        log.info("server thread shuru: %s", config.SERVER_ORIGIN)

    def _start_tray(self) -> None:
        if not self.tray.start():
            log.warning("tray nahi chala — app chal raha hai, sirf icon nahi dikhega")
        # Tools ka asli haalat (env se ON ho sakta hai) state me daalo.
        STATE.set_tools(keeper.tools_on())

    def _start_watchers(self) -> None:
        lockwatch.watch(on_lock=self._on_lock)
        wake_worker.start(on_wake=self._on_wake, on_state=STATE.set_wake)

    def _wait(self) -> None:
        last = STATE.version()
        while not self._stop.wait(0.5):
            if STATE.version() != last:      # state badli → tray icon refresh
                last = STATE.version()
                self.tray.refresh()

    def _shutdown(self) -> None:
        log.info("band ho raha hai (code=%s)", self._code)
        wake_worker.stop()
        self.tray.stop()
        self.hud.close()
        STATE.set_hud(False)
        if self.server is not None:
            self.server.should_exit = True
            time.sleep(0.6)
        self.lock.release()
        log.info("band")

    # ---- callbacks ----
    def _on_lock(self) -> None:
        """Win+L — sirf baat-cheet. TOOLS apne aap OFF. ALLOW ka raasta badalta
        nahi: card ka jawab sirf UI button se aata hai, wake se nahi."""
        if keeper.tools_on():
            keeper.set_tools(False)
            STATE.set_tools(False)
            log.warning("Windows lock hua — TOOLS apne aap OFF")
        STATE.set_mic(config.TRAY_OFF, "PC lock hai")

    def _on_wake(self, phrase: str) -> None:
        log.info("WAKE HIT: %r", phrase)
        self.hud.open()
        STATE.set_hud(True)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    return SundayApp(open_hud_at_start="--hud" in argv).run()


if __name__ == "__main__":
    sys.exit(main())
