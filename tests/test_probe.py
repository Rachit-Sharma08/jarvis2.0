"""brain/probe.py — strict JSON check, 2-call limit, 24 ghante ka cache.

Koi asli API call nahi. `openai_pool.chat` fake hai aur cache file temp folder me.
Startup par probe NAHI chalta — ye sirf tab, jab user jaan-boojh kar chalaye.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import brain.openai_pool as oa
import brain.pool_config as pc
import brain.probe as probe
from config import LOG_DIR

FAILED = []
SAVED = (oa.chat, probe.CACHE_FILE)
CALLS = []


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def set_chat(fn):
    oa.chat = fn


def use_temp_cache():
    probe.CACHE_FILE = Path(LOG_DIR) / "test_probe_cache.json"
    probe.CACHE_FILE.unlink(missing_ok=True)


print("STRICT JSON")
check("sahi JSON", probe.strict_json('{"text":"namaste","n":7,"ok":true}')[0], True)
check("markdown ke andar JSON", probe.strict_json('Here you go: {"text":"hi","n":1,"ok":false} done')[0], True)
check("khaali", probe.strict_json("")[0], False)
check("khaali reason", probe.strict_json("") == (False, "khaali content"), True)
check("sirf text", probe.strict_json("koi json nahi hai yahan")[0], False)
check("brace nahi", probe.strict_json("blah blah")[0], False)
check("toota hua JSON", probe.strict_json('{"text":"hi",')[0], False)
check("array hai", probe.strict_json('[1,2,3]')[0], False)
check("text missing", probe.strict_json('{"n":7,"ok":true}')[0], False)
check("n missing", probe.strict_json('{"text":"hi","ok":true}')[0], False)
check("ok missing", probe.strict_json('{"text":"hi","n":7}')[0], False)
check("n string hai", probe.strict_json('{"text":"hi","n":"7","ok":true}')[0], False)
check("ok number hai", probe.strict_json('{"text":"hi","n":7,"ok":1}')[0], False)
check("text number hai", probe.strict_json('{"text":7,"n":7,"ok":true}')[0], False)
check("number sahi", probe.strict_json('{"text":"hi","n":7,"ok":false}')[0], True)
check("float number", probe.strict_json('{"text":"hi","n":7.5,"ok":true}')[0], False)

print("HAR MODEL PAR 2 CALL")
CALLS.clear()
set_chat(lambda *a, **k: (CALLS.append(1), '{"text":"hi","n":1,"ok":true}')[1])
row = probe.probe_model({"name": "nv", "key": "k"}, "m1", calls=2)
check("2 hi call", len(CALLS), 2)
check("ok True", row["ok"], True)
check("calls field 2", row["calls"], 2)
check("latency diya", row["latency_ms"] is not None, True)
check("model naam", row["model"], "m1")

print("SAARE FAIL")
CALLS.clear()
set_chat(lambda *a, **k: (CALLS.append(1), (_ for _ in ()).throw(oa.CallError("gone", "404")))[1])
row = probe.probe_model({"name": "nv", "key": "k"}, "m2", calls=2)
check("404 par 2 call", len(CALLS), 2)
check("ok False", row["ok"], False)
check("gone reason", "gone" in row["reason"], True)

print("EK BAAR PASS, DUSRI BAAR FAIL")
state = {"n": 0}
CALLS.clear()


def _flaky(*a, **k):
    state["n"] += 1
    CALLS.append(state["n"])
    if state["n"] == 1:
        raise oa.CallError("busy", "429")
    return '{"text":"hi","n":1,"ok":true}'


set_chat(_flaky)
row = probe.probe_model({"name": "nv", "key": "k"}, "m3", calls=2)
check("retry se pass", row["ok"], True)
check("2 call lagi", len(CALLS), 2)
check("best latency mili", row["latency_ms"] is not None, True)

print("WINNER — sirf JSON pass + 8s se kam")
rows = [{"model": "slow", "ok": True, "latency_ms": 12000},
        {"model": "jsonfail", "ok": False, "latency_ms": 500},
        {"model": "good", "ok": True, "latency_ms": 1100}]
check("tez + JSON pass chuna", probe._pick(rows)["model"], "good")
check("sirf JSON fail koi nahi", probe._pick([{"model": "a", "ok": False, "latency_ms": 100}]), {})
check("sirf slow koi nahi", probe._pick([{"model": "a", "ok": True, "latency_ms": 9000}]), {})
check("koi row hi nahi", probe._pick([]), {})

print("CACHE 24 GHANTE")
check("TTL 24 ghante", probe.CACHE_TTL, 24 * 3600)
check("max 2 call", probe.MAX_CALLS, 2)
check("latency limit 8s", probe.LATENCY_LIMIT_MS, 8000)
check("fresh cache", probe._fresh({"ts": time.time() - 10}), True)
check("purana cache stale", probe._fresh({"ts": time.time() - 90000}), False)
check("khaali cache stale", probe._fresh(None), False)
check("bina ts stale", probe._fresh({}), False)

use_temp_cache()
CALLS.clear()


def _good(*a, **k):
    CALLS.append(a[3] if len(a) > 3 else k.get("model"))
    return '{"text":"hi","n":1,"ok":true}'


set_chat(_good)
first = probe.run("nvidia", limit=2, force=True)
check("pehli baar API gayi", len(CALLS) > 0, True)
check("4 call (2 model x 2)", len(CALLS), 4)
check("2 model probe hue", len(first["rows"]), 2)
check("winner mila", first["winner"].get("model"), pc.by_name()["nvidia"]["models"][0])
check("cache file bani", probe.CACHE_FILE.exists(), True)

CALLS.clear()
second = probe.run("nvidia", limit=2, force=False)
check("dusri baar cache se", len(CALLS), 0)
check("same winner", second["winner"], first["winner"])
check("rows bhi cache se", second["rows"], first["rows"])

CALLS.clear()
third = probe.run("nvidia", limit=2, force=True)
check("force par API phir gayi", len(CALLS) > 0, True)

probe._save({"nvidia": {"ts": time.time() - 90000, "rows": [], "winner": {}}})
CALLS.clear()
stale = probe.run("nvidia", limit=2, force=False)
check("purana cache dubara probe karta hai", len(CALLS) > 0, True)

print("KEY NA HO")
saved_key = pc.by_name()["nvidia"]["key"]
pc.by_name()["nvidia"]["key"] = ""
try:
    out = probe.run("nvidia", force=True)
    check("key nahi to error", "key nahi hai" in out.get("error", ""), True)
    out2 = probe.run("koi_aisa_provider", force=True)
    check("provider hi nahi to error", "pool me nahi" in out2.get("error", ""), True)
finally:
    pc.by_name()["nvidia"]["key"] = saved_key

probe.CACHE_FILE.unlink(missing_ok=True)
oa.chat, probe.CACHE_FILE = SAVED

print()
if FAILED:
    print(f"{len(FAILED)} fail: {FAILED}")
    sys.exit(1)
print("Saare probe test pass.")
