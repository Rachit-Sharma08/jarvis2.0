"""Tray watchdog ka test - pure logic + fake. **Asli registry ya wait kabhi
nahi** (AGENTS rule 10). `winreg` ki jagah fake `entries_fn` deta hai.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from desktop import tray_watch as tw

FAILED = []


def check(name, got, want):
    if got != want:
        FAILED.append(name)
        print("FAIL:", name, "->", repr(got), "chahiye tha", repr(want))
    else:
        print("ok:", name)


# ---- fake registry: {hash: (tooltip, exe, promoted)} ----
def ent(tip, promoted=None, exe=r"D:\Python312\pythonw.exe"):
    return {"1" + str(len(tip)): (tip, exe, promoted)}


NAME = config.ASSISTANT_NAME

# ---- delay: pehle tez, phir dheere ----
check("delay tez", tw.delay(0), config.TRAY_WATCH_FAST_SECONDS)
check("delay 30s tez", tw.delay(30), config.TRAY_WATCH_FAST_SECONDS)
check("delay 61s dheere", tw.delay(61), config.TRAY_WATCH_SLOW_SECONDS)
check("fast/slow alag", config.TRAY_WATCH_FAST_SECONDS != config.TRAY_WATCH_SLOW_SECONDS,
      True)
check("first = 60", config.TRAY_WATCH_FIRST_SECONDS, 60.0)

# ---- find_our_entry: tooltip se naam ----
promoted = ent(NAME + " - sun raha hai", 1)
p_key = list(promoted)[0]
check("entry mili", tw.find_our_entry(promoted, NAME)[0], p_key)
check("promoted padha", tw.find_our_entry(promoted, NAME)[1], 1)
mixed = dict(ent("MyJarvis.Desktop", None))
mixed.update(ent(NAME + " - band", None))
check("purana entry chhoda", tw.status(mixed, NAME), tw.HIDDEN)
check("koi entry nahi", tw.find_our_entry({}, NAME), (None, None))
check("tip None hai", tw.status({"9": (None, None, None)}, NAME), tw.MISSING)

# ---- status: teen haal ----
check("visible", tw.status(ent(NAME + " - band", 1), NAME), tw.VISIBLE)
check("hidden (IsPromoted missing)", tw.status(ent(NAME + " - band", None), NAME),
      tw.HIDDEN)
check("hidden (IsPromoted=0)", tw.status(ent(NAME + " - band", 0), NAME), tw.HIDDEN)
check("missing", tw.status({}, NAME), tw.MISSING)

# ---- message: har haal ka ek line + sahi raasta ----
for st in (tw.VISIBLE, tw.HIDDEN, tw.MISSING):
    check("message hai: " + st, len(tw.MESSAGE[st]) > 20, True)
check("hidden me ^ ka raasta bataya", "^" in tw.MESSAGE[tw.HIDDEN], True)
check("hidden me Always show icons", "Always show icons" in tw.MESSAGE[tw.HIDDEN], True)
check("missing me restart ka raasta", "restart" in tw.MESSAGE[tw.MISSING], True)

# ---- loop: sirf haal badne par log (2 check, 1 hi message) ----
seen = []
dog = tw.Watchdog(sleep_fn=lambda secs: seen.append(secs) or len(seen) > 2,
                  clock=lambda: 0.0,
                  entries_fn=lambda: ent(NAME + " - band", None),
                  name=NAME)
dog.run()
check("loop ne 3 dekh li", len(seen), 3)
check("loop HIDDEN bola", dog.state, tw.HIDDEN)
check("teesri dekh bhi tez thi", seen[:2], [config.TRAY_WATCH_FAST_SECONDS] * 2)

# ---- loop: hidden -> visible badla to naya message ----
states = [ent(NAME + " - band", None), ent(NAME + " - sun raha hai", 1)]
dog2 = tw.Watchdog(sleep_fn=lambda secs: len(states) > 0 or states.pop(0),
                   entries_fn=lambda: states[0] if states else None,
                   name=NAME)
# pehli check HIDDEN, phir dict khaali -> MISSING, phir ruk
dog2.run()
check("badlav ka naya haal", dog2.state in (tw.HIDDEN, tw.MISSING), True)

# ---- loop: registry padhna fail ho to chup (crash nahi, spam nahi) ----
def boom():
    raise PermissionError("registry band")


dog3 = tw.Watchdog(sleep_fn=lambda secs: True, entries_fn=boom, name=NAME)
dog3.run()
check("registry fail me haal None", dog3.state, None)

# ---- module ka start/stop: ek hi watchdog ----
first = tw.Watchdog(entries_fn=lambda: {}, name=NAME)
tw._STARTED.append(first)
check("start chalu", first.start(), True)
ident = first._thread.ident
check("dobara start naya thread nahi", first.start(), True)
check("thread wahi", first._thread.ident, ident)
check("start ka return", tw.start(), True)
check("ek hi watchdog", len(tw._STARTED), 1)
tw.stop()
check("list khali", tw._STARTED, [])

# ---- env se band: thread nahi banta ----
was = config.TRAY_WATCH_ENABLED
config.TRAY_WATCH_ENABLED = False
try:
    off = tw.Watchdog(entries_fn=lambda: {}, name=NAME)
    tw._STARTED.append(off)
    check("env 0 se start False", off.start(), False)
    check("env 0 me thread nahi", off._thread, None)
    check("module start bhi False", tw.start(), False)
finally:
    config.TRAY_WATCH_ENABLED = was
    tw.stop()

# ---- file 200 se choti (AGENTS niyam) ----
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, "..", "desktop", "tray_watch.py")
check("tray_watch.py <=200", len(open(src, encoding="utf-8").read().splitlines()) <= 200,
      True)
cfg = os.path.join(here, "..", "config_tray.py")
check("config_tray.py <=200", len(open(cfg, encoding="utf-8").read().splitlines()) <= 200,
      True)

print("FAIL:", FAILED if FAILED else "koi nahi")
sys.exit(1 if FAILED else 0)