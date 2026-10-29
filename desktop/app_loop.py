"""App ka "chal raha hoon" hissa — mic preflight + main wait loop.

Ye file 14-Oct raat me bani (`desktop/app.py` 207 line par 200 cross kar gaya).
Sirf wahi do method yahan aaye jo **kisi test ke source-scan me nahi** hain.

**Ye split kyun aise kiya:** `desktop/app.py` ke bahut se hisse test me
source-text se check hote hain (jaise `test_desktop.py` `config.STARTUP_SERVER`
aur `startup.say_hud(` dhoondta hai, `test_desktop_guard.py` `start_retry(`,
`test_desktop_shortcut.py` `self.hotkey.start()`). Un strings ko hatate to wo
test **chup-chaap fail** ho jaate — split ke baad fake/reference shift karna
padta. Is liye sirf ye do (koi test nahi dhoondta) bahar nikale gaye, baaki
asar me hai.

Ek file, ek kaam: app shuru hone se thoda pehle mic ka haal, aur uske baad ka
main loop (state change + reminder broadcast). Baaki startup/shutdown ka faisla
`desktop/app.py` me hai — ye sirf **chalte rehne** ka hissa hai.
"""

import sys
import threading

import config
from core import sysstats
from desktop import micperm, playback
from desktop.state import STATE
from log_setup import get_logger
from server import hud_reminders
from tools import reminders

log = get_logger("app")


class AppLoop:
    """Mixin — `SundayApp` ke saath milta hai. App ka steady-state hissa.

    Mixin is liye, inheritance nahi: `SundayApp` ka MRO/naam badla nahi jata,
    is liye koi test `isinstance` ya `SundayApp` par nahi toota. `run()` wahi
    `self._preflight()`/`self._wait()` call karta hai — bas definition jagah
    badli hai.
    """

    def _preflight(self) -> None:
        """Server shuru karne se pehle mic permission ka haal.

        Mic band ho to `STATE` me error daalte hain taaki **tray aur HUD dono**
        dikhaaye (niyam: mic ki galti chupchaap nahi). App phir bhi chalta
        hai — sirf sun nahi sakta.
        """
        allowed, reason = micperm.status(sys.executable)
        if not allowed:
            STATE.set_mic(config.TRAY_ERROR, micperm.explain(reason))
            log.error("mic band hai: %s", reason)
        else:
            log.info("mic permission: %s", reason or "theek hai")

    def _wait(self) -> None:
        """Main loop — jab tak app band na ho.

        Har 0.5s: state badli to tray icon refresh. Har ~5s: reminder ka
        broadcast (HUD par reminder text dikhta hai).

        Reminder broadcast ka `except Exception: pass` jaan-boojh kar hai —
        reminder na bhej paaye to app **bilkul** mat ruke. Ye sirf ek
        convenience tick hai, core kaam nahi.
        """
        last = STATE.version()
        ticks = 0
        while not self._stop.wait(0.5):
            ticks += 1
            if STATE.version() != last:      # state badli + tray icon refresh
                last = STATE.version()
                self.tray.refresh()
            if ticks % 20 == 0:  # ~10s: due reminder bolo + HUD ko batao
                try:
                    self._fire_reminders()
                except Exception:
                    pass
            if ticks % 10 == 0:  # ~5s
                try:
                    hud_reminders.broadcast()
                except Exception:
                    pass

    def _fire_reminders(self) -> None:
        """Due reminder ek hi baar bolo (speaker thread par, loop na ruke).

        `mark_done()` **bolne se pehle** — warna TTS 10s se zyada le to wahi
        reminder agle tick par dobara bolta. TTS fail ho to reminder chup ho
        jaata hai, par `logs/jarvis.log` me "reminder baj raha hai" line rehti
        hai (shortcut: awaaz fail par retry nahi, chahiye to yahan add karo).

        Quiet hours me **kuch nahi** — reminder pending rehta
        hai, HUD par overdue dikhta hai, aur subah pehle tick par khud bolta
        hai (Endgame: alarm nahi bajta, par baat bhi nahi bhoole).
        """
        if config.quiet_now():
            return
        items = reminders.due()
        if not items or not reminders.mark_done([x.get('id') for x in items]):
            return
        lines = ["Sir, reminder: " + str(x.get('text') or 'Reminder') for x in items]
        log.info("reminder baj raha hai: %s", ", ".join(
            "#%s" % x.get('id') for x in items))
        threading.Thread(target=_speak_all, args=(lines,), daemon=True).start()
        hud_reminders.broadcast()


def _speak_all(lines: list) -> None:
    """Ek hi thread me saare lines (do thread ek saath bolne lag jaate)."""
    for line in lines:
        playback.say(line)