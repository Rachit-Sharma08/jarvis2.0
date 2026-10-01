"""Brain pool, hissa 1: tier failover, khaali jawab + retry, 404 permanent.

Sab fake — koi asli API call nahi. `openai_pool.chat` fake hai, isliye
`pool._ask_with_retry` (retry + token badhana) asli tarah se test hota hai.
Cooldown/credits ke liye dekho `test_pool_billing.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import brain.openai_pool as oa
import brain.pool as pool
from brain import health
from poolhelp import HIST, check, finish, no_sleep, p, restore, use


def test_tier_failover():
    print("TIER FAILOVER")
    fake = (p("t1only", 1), p("t2only", 2))
    calls = []

    def _chat(provider, history, persona, model, **kw):
        calls.append(provider["name"])
        return provider["name"] + " ka jawab"

    use(fake, _chat)
    try:
        ans, name = pool.ask(HIST, "persona")
        check("T1 se jawab", name, "t1only")
        check("T2 tak nahi gaya", calls, ["t1only"])
        check("tier 1 yaad", pool.status()["active_tier"], 1)
        check("model bhi yaad", pool.status()["model"], "m1")
        check("jawaab mila", ans, "t1only ka jawab")
    finally:
        restore()

    calls.clear()
    use(fake, _chat)
    try:
        health.skip("t1only", "429 busy", seconds=300)
        ans, name = pool.ask(HIST, "p")
        check("T1 rest par T2 chala", name, "t2only")
        check("sirf T2 call hua", calls, ["t2only"])
        check("tier 2 yaad", pool.status()["active_tier"], 2)
    finally:
        restore()

    # Teen providers: T1 ke do, phir T2 ka pehla.
    fake = (p("a", 1), p("b", 1), p("c", 2), p("d", 2))
    calls = []

    def _chat2(provider, history, persona, model, **kw):
        calls.append(provider["name"])
        if provider["name"] != "c":
            raise oa.CallError("busy", "429 busy")
        return "c se jawab"

    def go2():
        ans, name = pool.ask(HIST, "p")
        check("order follow hua", calls, ["a", "b", "c"])
        check("T2 ka pehla winner", name, "c")

    use(fake, _chat2)
    try:
        no_sleep(go2)
    finally:
        restore()

def test_empty_retry():
    print("KHAALI JAWAB + RETRY")
    fake = (p("khali", 1), p("solid", 2))
    seen = []

    def _chat(provider, history, persona, model, **kw):
        seen.append((provider["name"], kw.get("max_tokens")))
        if provider["name"] == "khali":
            raise oa.CallError("empty", "content khaali")
        return " asli jawab"

    def go():
        ans, name = pool.ask(HIST, "p")
        check("retry ke baad agla provider", name, "solid")
        check("khali provider 2 baar", [n for n, _ in seen].count("khali"), 2)
        check("pehli call 2500 token", seen[0][1], 2500)
        check("retry 5000 token", seen[1][1], 5000)
        check("jawaab mila", ans, " asli jawab")

    use(fake, _chat)
    try:
        no_sleep(go)
    finally:
        restore()

    # Length par bhi 'empty' hi count hona chahiye — retry mile.
    fake = (p("cut", 1), p("after", 2))
    calls = []

    def _chat2(provider, history, persona, model, **kw):
        calls.append(provider["name"])
        if provider["name"] == "cut":
            raise oa.CallError("empty", "token khatam (length)")
        return " agla"

    def go2():
        ans, name = pool.ask(HIST, "p")
        check("length par retry hua", calls.count("cut"), 2)
        check("phir agla provider", name, "after")

    use(fake, _chat2)
    try:
        no_sleep(go2)
    finally:
        restore()

    # 429 par retry nahi — seedha agla provider.
    fake = (p("busy", 1), p("next", 2))
    calls = []

    def _chat3(provider, history, persona, model, **kw):
        calls.append(provider["name"])
        if provider["name"] == "busy":
            raise oa.CallError("busy", "429")
        return " agla"

    def go3():
        pool.ask(HIST, "p")
        check("429 par retry nahi", calls.count("busy"), 1)
        check("429 par agla provider chala", calls, ["busy", "next"])

    use(fake, _chat3)
    try:
        no_sleep(go3)
    finally:
        restore()

def test_404_next_model():
    print("404 PERMANENT + AGLA MODEL")
    fake = (p("nv", 1, models=("m1", "m2", "m3")), p("later", 2))
    tried = []

    def _chat(provider, history, persona, model, **kw):
        tried.append((provider["name"], model))
        if model in ("m1", "m2"):
            raise oa.CallError("gone", "404 model_not_found")
        return "m3 se jawab"

    use(fake, _chat)
    try:
        ans, name = pool.ask(HIST, "p")
        check("404,404 ke baad m3", [m for _, m in tried], ["m1", "m2", "m3"])
        check("jawaab usi provider se", name, "nv")
        check("m1 GONE", health.is_gone("m1"), True)
        check("m2 GONE", health.is_gone("m2"), True)
        check("m3 GONE nahi", health.is_gone("m3"), False)
        check("status me gone_models", "m1" in pool.status()["gone_models"], True)

        tried.clear()
        pool.ask(HIST, "p")
        check("doosri baar 404 wale skip", [m for _, m in tried], ["m3"])
    finally:
        restore()

    # Saare 404 ho to agle provider.
    fake = (p("dead", 1, models=("d1", "d2")), p("alive", 2))
    tried = []

    def _chat2(provider, history, persona, model, **kw):
        tried.append(provider["name"])
        if provider["name"] == "dead":
            raise oa.CallError("gone", "404")
        return " zinda"

    use(fake, _chat2)
    try:
        ans, name = pool.ask(HIST, "p")
        check("saare 404 par agla provider", name, "alive")
        check("dead ke dono model try", tried, ["dead", "dead", "alive"])
    finally:
        restore()

    # 404 par cooldown nahi — sirf model GONE. Provider turant doosre model par.
    fake = (p("nv", 1, models=("x1", "x2")), p("o", 2))

    def _chat3(provider, history, persona, model, **kw):
        if model == "x1":
            raise oa.CallError("gone", "404")
        return " x2 se"

    use(fake, _chat3)
    try:
        pool.ask(HIST, "p")
        check("404 par provider rest nahi", "nv" in pool.status()["cooldowns"], False)
    finally:
        restore()
for fn in (test_tier_failover, test_empty_retry, test_404_next_model):
    fn()

finish("pool failover")
