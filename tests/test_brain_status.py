"""GET /brain/status — fields, masking aur security (Host -> Origin -> Token).

Koi API call nahi. `brain.router.status()` fake kiya gaya hai jisme jaan-boojh
kar ek fake API key daali hai — dekhna ye hai ki wo response me na nikle.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from fastapi.testclient import TestClient

import config
from brain import router as brain_router
from server import security
from server.app import app

FAILED = []
FAKE_NV = "nvapi-FAKEFAKEFAKEFAKE1234567890"
FAKE_GROQ = "gsk_FAKEFAKEFAKEFAKE1234567890"
FAKE_AQ = "AQ.FAKEFAKEFAKEFAKEFAKEFAKEFAKE"

# Koi bhi asli env value is test me nahi jaani chahiye.
os.environ["NVIDIA_API_KEY"] = FAKE_NV
os.environ["GROQ_API_KEY"] = FAKE_GROQ


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


FAKE_STATUS = {
    "active_tier": 2,
    "active_provider": "nvidia",
    "provider": "nvidia",
    "model": "nvidia/nemotron-3-super-120b-a12b",
    "cooldowns": {"gemini": "12 min baad", "nvidia": "credits khatam — nayi key chahiye"},
    "last_fail_reasons": {"openrouter": "429 rate limit"},
    "gone_models": ["qwen/qwen3.8-27b:free"],
    "providers": [
        {"name": "nvidia", "tier": 2, "key": FAKE_NV, "has_key": True,
         "model": "nvidia/nemotron-3-super-120b-a12b"},
        {"name": "groq", "tier": 1, "key": FAKE_GROQ, "has_key": True,
         "model": "openai/gpt-oss-120b"},
        {"name": "cartesia", "tier": 2, "api_key": FAKE_AQ, "has_key": False,
         "model": "simi"},
    ],
}

client = TestClient(app)
HOST = sorted(config.allowed_hosts())[0]
ORIGIN = f"http://{HOST}"
GOOD = {"Origin": ORIGIN, "Host": HOST, security.TOKEN_HEADER: security.token()}


print("ROUTE SHAAMIL HAI")
paths = app.openapi()["paths"]
check("/brain/status mojood", "/brain/status" in paths, True)
check("GET method", "get" in paths.get("/brain/status", {}), True)
check("pooled brain route alag", len(paths) >= 9, True)

print("SECURITY — Host -> Origin -> Token")
saved = brain_router.status
brain_router.status = lambda: dict(FAKE_STATUS)
try:
    check("token ke bina 401",
          client.get("/brain/status", headers={"Origin": ORIGIN, "Host": HOST}).status_code, 401)
    check("galat token 401",
          client.get("/brain/status", headers={**GOOD, security.TOKEN_HEADER: "wrong"}).status_code, 401)
    check("khaali origin 403",
          client.get("/brain/status", headers={**GOOD, "Origin": ""}).status_code, 403)
    check("bahar ka origin 403",
          client.get("/brain/status", headers={**GOOD, "Origin": "http://evil.com"}).status_code, 403)
    check("galat host 400",
          client.get("/brain/status", headers={**GOOD, "Host": "attacker.com"}).status_code, 400)

    reply = client.get("/brain/status", headers=GOOD)
    check("sahi token par 200", reply.status_code, 200)
    data = reply.json()

    print("FIELDS")
    for field in ("active_tier", "provider", "model", "cooldowns", "last_fail_reasons"):
        check(f"{field} mojood", field in data, True)
    check("active_tier number", data["active_tier"], 2)
    check("provider", data["provider"], "nvidia")
    check("model", data["model"], "nvidia/nemotron-3-super-120b-a12b")
    check("cooldowns dict", isinstance(data["cooldowns"], dict), True)
    check("cooldown ki gali text", "12 min baad" in data["cooldowns"].get("gemini", ""), True)
    check("credits wali gali text", "credits khatam" in data["cooldowns"].get("nvidia", ""), True)
    check("last_fail me reason", "429" in json.dumps(data["last_fail_reasons"]), True)
    check("gone_models list", isinstance(data["gone_models"], list), True)

    print("MASKING — koi key nahi bahar")
    raw = reply.text
    for name, key in (("nvidia", FAKE_NV), ("groq", FAKE_GROQ), ("AQ", FAKE_AQ)):
        check(f"{name} ki fake key nahi nikli", key in raw, False)
    check("key field poora hata diya",
          all("key" not in row and "api_key" not in row for row in data["providers"]), True)
    check("has_key boolean bachi", data["providers"][0].get("has_key"), True)
    check("koi '***' bhi nahi chahiye tha",
          all("***" not in str(v) for row in data["providers"] for v in row.values()), True)
    check("providers list bachi", len(data["providers"]), 3)
    check("tier number bacha", data["providers"][0]["tier"], 2)
    check("cooldowns strings bachi", isinstance(data["cooldowns"], dict), True)

    print("ROUTE / BRAIN KE BAAHAR KOI ROUTE NAHI")
    check("sirf brain/status", [p for p in paths if "brain" in p], ["/brain/status"])
finally:
    brain_router.status = saved
    os.environ.pop("NVIDIA_API_KEY", None)
    os.environ.pop("GROQ_API_KEY", None)

print()
if FAILED:
    print(f"{len(FAILED)} fail: {FAILED}")
    sys.exit(1)
print("Saare brain-status test pass.")
