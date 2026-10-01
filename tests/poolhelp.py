"""test_pool.py aur test_pool_billing.py ka shared scaffolding.

Koi test yahan se chalta hai — sirf helper. `check()` fail hone par FAILED me
naam daalti hai, test file ke end par summary print hoti hai.
"""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brain.openai_pool as oa          # noqa: E402
import brain.pool as pool               # noqa: E402
import brain.pool_config as pc          # noqa: E402
import time                             # noqa: E402

FAILED = []
HIST = [{"role": "user", "content": "hi"}]
SAVED = (pc.POOL, oa.chat)


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def p(name, tier, models=("m1",), **kw):
    """Fake provider entry. 'latest' jaisa koi naam nahi — model list se order."""
    kw.setdefault("key", "fake-key-not-real")
    return pc._p(name=name, tier=tier, models=models, **kw)


def use(fake_pool, fake_chat):
    """Pool + adapter fake. Koi network call nahi ho sakti."""
    pc.POOL, oa.chat = fake_pool, fake_chat
    pool.reset()


def restore():
    pc.POOL, oa.chat = SAVED
    pool.reset()


def no_sleep(fn):
    """fn chalate waqt 1 second ka retry-sleep skip karo."""
    orig = time.sleep
    time.sleep = lambda _s: None
    try:
        return fn()
    finally:
        time.sleep = orig


def raiser(kind, message="fail", retry_after=0):
    def _chat(provider, history, persona, model, **kw):
        raise oa.CallError(kind, message, retry_after)
    return _chat


def finish(title="pool"):
    """Test file ke ant me call karo. Fail ho to exit code 1."""
    print()
    if FAILED:
        print(f"{len(FAILED)} {title} test fail: {FAILED}")
        sys.exit(1)
    print(f"Saare {title} test pass.")
