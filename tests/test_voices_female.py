"""Female voice chain: dono mode ki awaaz female honi chahiye.

Ye test koi awaaz nahi banata — sirf chain ka faisla jaanta hai (female allowlist
+ fallback order). Asli `speak()` call fake kiya gaya hai.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import asyncio
import os
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from brain import health
from voice import tts, tts_female

FAILED = []
SAVED_ENV = {k: os.environ.get(k) for k in
             ("ELEVENLABS_VOICE_SUNDAY", "ELEVENLABS_VOICE_PRABH",
              "CARTESIA_VOICE_SUNDAY", "CARTESIA_VOICE_PRABH")}

# Fake ids jo allowlist me hain, taaki gender check jaan sakein bina API ke.
FAKE_OK = {"ELEVENLABS_VOICE_SUNDAY": tts_female.next(list(tts_female.ELEVENLABS_FEMALE)),
           "ELEVENLABS_VOICE_PRABH": tts_female.next(list(tts_female.ELEVENLABS_FEMALE))}
FAKE_MALE = "MALE-VOICE-NOT-ALLOWED"
FAKE_CART = "fake-cartesia-id"


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def put(**kw):
    for key, val in kw.items():
        os.environ[key] = val


def try_run(text, mode):
    """TtsError ya (audio, provider) — test crash na ho."""
    try:
        return run(tts.speak(text, mode))
    except tts.TtsError as exc:
        return ("error", str(exc))


def _make(name, calls):
    async def speak(text, mode):
        calls.append((name, mode, text))
        return b"RIFFfake-audio"
    return SimpleNamespace(speak=speak)


def _raiser(calls, exc):
    async def speak(text, mode):
        calls.append(("fail", mode, text))
        raise exc
    return SimpleNamespace(speak=speak)


print("ALLOWLIST — female hi allowed")
check("khaali id nahi", tts_female.is_allowed("elevenlabs", ""), False)
check("jhooti/male id nahi", tts_female.is_allowed("elevenlabs", FAKE_MALE), False)
check("sunday ki id allowed", tts_female.is_allowed("elevenlabs", FAKE_OK["ELEVENLABS_VOICE_SUNDAY"]), True)
check("prabh ki id allowed", tts_female.is_allowed("elevenlabs", FAKE_OK["ELEVENLABS_VOICE_PRABH"]), True)
check("allowlist me 2 elevenlabs ids", len(tts_female.ELEVENLABS_FEMALE), 2)
check("cartesia me 1 female id (Skylar)", len(tts_female.CARTESIA_FEMALE), 1)
check("skylar allowed", tts_female.is_allowed(
    "cartesia", "db6b0ed5-d5d3-463d-ae85-518a07d3c2b4"), True)
check("cartesia id skip hogi", tts_female.is_allowed("cartesia", FAKE_CART), False)
check("edge swara allowed", tts_female.is_allowed("edge", "hi-IN-SwaraNeural"), True)
check("edge male nahi", tts_female.is_allowed("edge", "en-US-GuyNeural"), False)
check("check() theek par khali", tts_female.check("edge", "hi-IN-SwaraNeural"), "")
check("check() galat par reason", bool(tts_female.check("elevenlabs", FAKE_MALE)), True)
check("report me sirf aakhri 4",
      all(len(x) == 4 for ids in tts_female.allowlist_report().values() for x in ids), True)
check("report me jhanda id nahi",
      FAKE_MALE[-4:] not in tts_female.allowlist_report().get("elevenlabs", []), True)

print("MODE KE HISAAB SE AWAAZ (dono female)")
for mode, key in (("sunday", "ELEVENLABS_VOICE_SUNDAY"), ("prabh", "ELEVENLABS_VOICE_PRABH")):
    put(**{key: FAKE_OK[key]})
    check(f"{mode}: edge Swara (female)", config.voice_for("edge", mode), "hi-IN-SwaraNeural")
    check(f"{mode}: elevenlabs female allowlist me",
          tts_female.is_allowed("elevenlabs", config.voice_for("elevenlabs", mode)), True)
    check(f"{mode}: edge Swara hi maango",
          tts_female.is_allowed("edge", config.EDGE_VOICES[mode]), True)
    put(**{key: FAKE_MALE})
    check(f"{mode}: male id reject hogi",
          tts_female.is_allowed("elevenlabs", config.voice_for("elevenlabs", mode)), False)
    os.environ.pop(key, None)
    check(f"{mode}: id na ho to khaali (male default nahi)",
          config.voice_for("elevenlabs", mode), "")

print("SPEAK — sabse pehla provider, dono mode")
calls = []
orig = dict(tts.PROVIDERS)
try:
    for name in orig:
        tts.PROVIDERS[name] = _make(name, calls)
    for mode, key in (("sunday", "ELEVENLABS_VOICE_SUNDAY"), ("prabh", "ELEVENLABS_VOICE_PRABH")):
        put(**{key: FAKE_OK[key]})
        calls.clear()
        audio, used = run(tts.speak("namaste, kya haal hai", mode))
        check(f"{mode}: elevenlabs pehla chala", used, "elevenlabs")
        check(f"{mode}: sirf ek call", len(calls), 1)
        check(f"{mode}: audio mila", bool(audio), True)

    print("SPEAK - male id par elevenlabs chalta hi nahi")
    calls.clear()
    put(ELEVENLABS_VOICE_SUNDAY=FAKE_MALE, CARTESIA_VOICE_SUNDAY="")
    audio, used = run(tts.speak("namaste", "sunday"))
    check("allowlist ke bahar = edge", used, "edge")
    check("elevenlabs bilkul call nahi hua", "elevenlabs" not in [c[0] for c in calls], True)

    print("SPEAK — elevenlabs fail to edge (cartesia id nahi hai)")
    calls.clear()
    put(ELEVENLABS_VOICE_SUNDAY=FAKE_OK["ELEVENLABS_VOICE_SUNDAY"])
    os.environ.pop("CARTESIA_VOICE_SUNDAY", None)
    tts.PROVIDERS["elevenlabs"] = _raiser(calls, RuntimeError("500 server error"))
    audio, used = run(tts.speak("namaste", "sunday"))
    check("edge par gaya", used, "edge")
    check("cartesia skip (id nahi)", "cartesia" not in [c[0] for c in calls], True)
    health.reset_provider("elevenlabs")

    print("SPEAK — teeno fail = saaf error")
    calls.clear()
    for name in orig:
        tts.PROVIDERS[name] = _raiser(calls, RuntimeError("500 down"))
    out = try_run("namaste", "prabh")
    check("error aaya", out[0], "error")
    check("error me kaaran bataya", "Awaaz nahi ban paayi" in out[1], True)
    check("har provider ka naam", all(n in out[1] for n in config.TTS_CHAIN), True)
    health.reset_all()
finally:
    tts.PROVIDERS.clear()
    tts.PROVIDERS.update(orig)
    for key, val in SAVED_ENV.items():
        if val is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = val

print()
if FAILED:
    print(f"{len(FAILED)} fail: {FAILED}")
    sys.exit(1)
print("Saare female-voice test pass.")
