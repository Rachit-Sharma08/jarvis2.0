"""Brain pool, hissa 2: cooldown, credits/quota band, free-only, sab-fail message.

Sab fake — koi asli API call nahi. Failover/retry ke liye `test_pool.py`.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import brain.pool as pool
import brain.pool_config as pc
from brain import health
from poolhelp import HIST, check, finish, p, raiser, restore, use

def test_cooldown():
    print("COOLDOWN / RETRY-AFTER")
    fake = (p("nv", 1), p("other", 2))
    use(fake, raiser("busy", "429 rate limit", retry_after=45))
    try:
        pool.ask(HIST, "p")
        left = int(health.UNTIL["nv"] - time.monotonic())
        check("Retry-After 45s", 40 <= left <= 46, True)
        check("last_fail me 429", "429" in health.last_fail("nv"), True)
        check("status me cooldown", "nv" in pool.status()["cooldowns"], True)
    finally:
        restore()

    use(fake, raiser("busy", "503 overloaded"))
    try:
        pool.ask(HIST, "p")
        left = int(health.UNTIL["nv"] - time.monotonic())
        check("bina Retry-After 10 min", 595 <= left <= 601, True)
    finally:
        restore()

    # Khaali jawab par chhota rest (45s), 10 min nahi.
    use(fake, raiser("empty", "khaali jawab"))
    try:
        pool.ask(HIST, "p")
        left = int(health.UNTIL["nv"] - time.monotonic())
        check("khaali par 45s", 40 <= left <= 46, True)
    finally:
        restore()

    # 401 = nayi key tak seedha band.
    use(fake, raiser("auth", "401 Unauthorized"))
    try:
        pool.ask(HIST, "p")
        check("401 BAND", "BAND" in health.blocked_reason("nv"), True)
        check("key chahiye bataya", "key chahiye" in health.blocked_reason("nv"), True)
    finally:
        restore()
    health.reset_provider("nv")

def test_credits_lock():
    print("CREDITS KHATAM — nayi key tak")
    fake = (p("nv", 1), p("other", 2))
    use(fake, raiser("billing", "402 Cloud credits expired"))
    try:
        pool.ask(HIST, "p")
        reason = health.blocked_reason("nv")
        check("BAND", "BAND" in reason, True)
        check("nayi key chahiye bataya", "nayi key" in reason, True)
        check("agle din tak NAHI", "agle din tak" in reason, False)
        check("last_fail me credits", "credits expired" in health.last_fail("nv"), True)
        check("warning me bhi", any("nv" in w for w in health.warnings()), True)
    finally:
        restore()

    health.reset_provider("nv")
    check("reset (nayi key) se khula", health.blocked_reason("nv"), "")

    # 402 insufficient credits bhi wahi rule.
    use(fake, raiser("billing", "402 insufficient_credits"))
    try:
        pool.ask(HIST, "p")
        check("insufficient credits = nayi key", "nayi key" in health.blocked_reason("nv"), True)
    finally:
        restore()
    health.reset_provider("nv")

    # Daily quota ALAG — apne aap agle din theek ho jaata hai.
    use(fake, raiser("quota", "429 exceeded your daily quota"))
    try:
        pool.ask(HIST, "p")
        reason = health.blocked_reason("nv")
        check("quota BAND", "BAND" in reason, True)
        check("quota = agle din tak", "agle din tak" in reason, True)
        check("quota me 'nayi key' nahi", "nayi key" in reason, False)
    finally:
        restore()
    health.reset_provider("nv")

    # Band provider dubara call nahi hota.
    calls = []

    def _count(provider, history, persona, model, **kw):
        calls.append(provider["name"])
        return " jawab"

    fake = (p("nv", 1), p("other", 2))
    use(fake, _count)
    try:
        health.lock_credits("nv", "402 Cloud credits expired")
        pool.ask(HIST, "p")
        check("band provider skip", calls, ["other"])
    finally:
        restore()

def test_free_only():
    print("FREE-ONLY")
    fake = (p("nv", 1), p("other", 2))
    use(fake, raiser("billing", "insufficient_credits"))
    try:
        pool.ask(HIST, "p")
        check("billing par band", "BAND" in health.blocked_reason("nv"), True)
    finally:
        restore()
    health.reset_provider("nv")

    check("nvidia free-only", "nvidia" in pc.FREE_ONLY, True)
    check("openrouter free-only", "openrouter" in pc.FREE_ONLY, True)
    check("groq free-only nahi", "groq" in pc.FREE_ONLY, False)
    check("gemini free-only nahi", "gemini" in pc.FREE_ONLY, False)
    check("openrouter sirf :free",
          all(m.endswith(":free") for m in pc.by_name()["openrouter"]["models"]), True)
    check("nvidia model :free nahi lag chahiye",
          all(not m.endswith(":free") for m in pc.by_name()["nvidia"]["models"]), True)

    print("BILLING WORD — chhota response hi")
    check("short billing hit", pc.billing_hit("payment required"), "payment required")
    check("billing word", pc.billing_hit("Insufficient credits"), "insufficient credit")
    check("credits expired", pc.billing_hit("Your cloud credits expired"), "credits expired")
    check("normal jawab safe", pc.billing_hit("payment karna hai to bank jaao " * 5), "")
    check("lamba jawab safe", pc.billing_hit("Aap payment ki baat kar rahe ho, " * 20), "")
    check("khaali billing hit", pc.billing_hit(""), "")
    check("sirf 'payment' nahi (chhota)", pc.billing_hit("payment"), "")

    # Free-only na ho tab bhi credits wala text nayi-key lock lagata hai —
    # kyunki "402 Cloud credits expired" credit ki kami hai, quota nahi.
    fake = (p("groqlike", 1), p("other", 2))
    use(fake, raiser("billing", "402 Cloud credits expired"))
    try:
        pool.ask(HIST, "p")
        check("credits text har provider par lock karta hai",
              "nayi key" in health.blocked_reason("groqlike"), True)
    finally:
        restore()
    health.reset_all()


def test_all_fail():
    print("SAB FAIL — saaf message")
    fake = (p("p1", 1), p("p2", 2))
    use(fake, raiser("busy", "429 pehla busy"))
    try:
        ans, name = pool.ask(HIST, "p")
        check("brain none", name, "none")
        check("ek hi message", ans.count("Abhi koi brain"), 1)
        check("har provider ka reason", "p1" in ans and "p2" in ans, True)
        check("har problem apni line par", len(ans.splitlines()), 3)
        check("koi secret nahi", "fake-key" in ans, False)
        check("duplicate problem nahi", ans.count("p1"), 1)
    finally:
        restore()

    # Key na ho to bhi message aani chahiye.
    fake = (p("nokey", 1, key="", models=("m",)),)
    use(fake, raiser("busy", "kabhi use nahi hoga"))
    try:
        ans, name = pool.ask(HIST, "p")
        check("key na ho par message", name, "none")
        check("key wala reason", "key nahi hai" in ans, True)
    finally:
        restore()

    # Kuch bhi na ho (empty pool) ya sab 404 — crash nahi, message aayi.
    use((), raiser("busy", "x"))
    try:
        ans, name = pool.ask(HIST, "p")
        check("empty pool par crash nahi", name, "none")
        check("message phir bhi aayi", ans.startswith("Abhi koi brain"), True)
    finally:
        restore()
    fake = (p("d1", 1, models=("a",)), p("d2", 2, models=("b",)))
    use(fake, raiser("gone", "404 model_not_found"))
    try:
        ans, name = pool.ask(HIST, "p")
        check("saare 404 par message", name, "none")
        check("404 bataya", "404" in ans, True)
    finally:
        restore()

for fn in (test_cooldown, test_credits_lock, test_free_only, test_all_fail):
    fn()

finish("pool billing")
