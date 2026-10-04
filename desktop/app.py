"""Asli app — server + tray + HUD + hotkey + wake, sab ek process me.

Ek hi process is liye ki engine ek hi rahe (`server/state.py`). Thread: main
= intezaar/shutdown · "server" = uvicorn · "lockwatch" = Win+L · "hotkey" =
Ctrl+Alt+S · "wake" = `wake/worker.py` · pystray = tray menu.

Supervisor alag hai (`desktop/launcher.py`): crash par wahi dobara chala deta
hai. Yahan crash ka Exit code `config.EXIT_RESTART` se jaata hai.

Yahan sirf **kab kya chalta hai** likha hai. Callback ke andar ka faisla
`desktop/callbacks.py` me hai, haalaat `desktop/state.py` me.
"""

import sys
import threading
import time

import uvicorn

import config
from core import sysstats
from desktop import actions as actions_mod
from desktop import callbacks
from desktop import hud_window, hotkey as hotkey_mod
from desktop import lockwatch, micperm, single as single_mod, startup, tray_watch
from desktop.state import STATE
from desktop.tray import Tray
from gatekeeper import keeper
from log_setup import get_logger
from server.hub import HUB
from wake import ask as wake_ask, worker as wake_worker

log = get_logger("app")


class SundayApp:   # naam Step 1 me user-facing hua, class id wahi rakha
    def __init__(self, open_hud_at_start: bool = False):
        self.open_hud_at_start = bool(open_hud_at_start)
        self.hud = hud_window.HudWindow()
        self.hotkey = hotkey_mod.Hotkey(config.HUD_HOTKEY, on_press=self._on_hotkey)
        self.tray = Tray(actions_mod.Actions(self))
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
            # `diagnose()` ne check kiya hai: PID zinda + GET / 200. Is liye ye
            # message abhi bharosemand hai. Console par bhi — bat ka user yahi
            # padhega, log nahi.
            log.warning("%s", exc)
            print(str(exc), flush=True)
            return config.EXIT_ALREADY_RUNNING

        try:
            self._preflight()
            self._start_server()
            self._start_tray()
            if self._stop.is_set():          # tray nahi bana — aage mat chalo
                return self._code
            self._await_hud()
            self._start_watchers()
            if not self.hud.available():
                log.error("Edge/Chrome nahi mila — HUD nahi khulega (baaki sab chalega)")
            if config.HUD_OPEN_AT_START or self.open_hud_at_start:
                self.tray_actions().open_hud()
            self._wait()
        finally:
            self._shutdown()
        return self._code

    def stop(self, code: int = None) -> None:
        self._code = config.EXIT_QUIT if code is None else code
        self._stop.set()

    def tray_actions(self) -> actions_mod.Actions:
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
        # Naye browser ko abhi ka mic/tools haalat bhejne ka raasta.
        HUB.set_welcome(lambda: [STATE.event()])
        threading.Thread(target=self.server.run, name="server", daemon=True).start()
        startup.say(config.STARTUP_SERVER, config.SERVER_ORIGIN)

    def _start_tray(self) -> None:
        """Tray icon ke bina app **chalte nahi rehne** dega.

        Kabhi kabhi `pystray` pehli koshish me chhoot deta hai (Explorer restart,
        D: slow disk). Is liye 3 koshish. phir bhi na bane to `EXIT_NO_TRAY` se
        saaf exit — chup-chaap bina tray chalta hua app sabse bura hai, kyunki
        usse band karne ka koi raasta hi nahi hota.
        """
        if not self.tray.start_retry(config.TRAY_START_ATTEMPTS):
            startup.say(config.STARTUP_TRAY,
                        "FAILED - %d koshish ke baad bhi icon nahi bana"
                        % config.TRAY_START_ATTEMPTS)
            log.error("tray icon nahi bana - app ko %d se band kar raha hoon",
                      config.EXIT_NO_TRAY)
            self.stop(config.EXIT_NO_TRAY)
            return
        startup.say(config.STARTUP_TRAY, config.TRAY_NAME)
        # pystray `NIM_ADD` bhej chuka hai, par icon taskbar me dikh raha hai ya
        # `^` me chhupa hai - ye koi nahi pata karta. Watchdog roz registry se
        # dekh kar **sirf log** karta hai (roadmap T-01, S6 step 3+5).
        tray_watch.start()
        # Tools ka asli haalat (env se ON ho sakta hai) state me daalo.
        STATE.set_tools(keeper.tools_on())
        # TOOLS kahin se bhi badle - UI button, tray, lock, auto-off timer -
        # sab ka ek hi raasta: `Limiter` se hook, phir STATE (tray+HUD dono).
        keeper.LIMITER.set_on_change(self._on_tools_change)

    def _await_hud(self) -> None:
        """Server sach me 200 de raha hai? Tabhi 'HUD ready'. Port busy ya
        crash ho to 'FAILED' bol kar app aage badh jaata hai — chup-chaap na
        reh kar, taaki crash ki wajah console par dikhe (line `startup.py`)."""
        ok, reason = startup.await_http(config.SERVER_ORIGIN, config.STARTUP_HTTP_TIMEOUT)
        startup.say_hud(ok, reason)

    def _start_watchers(self) -> None:
        lockwatch.watch(on_lock=self._on_lock)
        if self._start_wake():
            STATE.set_mic(config.TRAY_LISTENING, "wake word sun raha hai")
        self.hotkey.start()

    def _start_wake(self) -> bool:
        """Wake word worker (Step 1) — sirf **sunta** hai, kuch bolta nahi.

        Mic khula reh kar sunta hai (duty cycle nahi), is liye mic ka pill
        'listening' ho jaata hai. Na chalne par bhi startup ki 4th line bolti
        hai — wajah chhoti, user ko dikhani hai (model missing / mic band)."""
        started = wake_worker.start(on_wake=self._on_wake, on_state=STATE.set_wake)
        _, reason = config.wake_available()
        startup.say_wake(started, "" if started else micperm.explain(reason))
        wake_ask.prewarm_async()
        return started

    def _wait(self) -> None:
        last = STATE.version()
        while not self._stop.wait(0.5):
            if STATE.version() != last:      # state badli → tray icon refresh
                last = STATE.version()
                self.tray.refresh()

    def _shutdown(self) -> None:
        log.info("band ho raha hai (code=%s)", self._code)
        wake_worker.stop()
        self.hotkey.stop()
        tray_watch.stop()
        self.tray.stop()
        self.hud.close()
        STATE.set_hud(False)
        if self.server is not None:
            self.server.should_exit = True
            time.sleep(0.6)
        self.lock.release()
        log.info("band")

    # ---- callbacks (asli kaam `desktop/callbacks.py` me) ----
    def _on_lock(self) -> None:
        callbacks.on_lock(self)

    def _on_tools_change(self, on: bool) -> None:
        callbacks.on_tools_change(on, self)

    def _on_wake(self, phrase: str, mic=None, stop=None) -> None:
        callbacks.on_wake(phrase, mic, stop, self)

    def _on_hotkey(self) -> None:
        callbacks.on_hotkey(self)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    return SundayApp(open_hud_at_start="--hud" in argv).run()


if __name__ == "__main__":
    sys.exit(main())
