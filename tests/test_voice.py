"""Voice side: STT guard, mode aliases aur /stt + /tts endpoints ka security.

TTS chain aur female allowlist ke test alag file me hain (test_voice_tts.py).
"""

import asyncio
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import config
import core.modes as modes
from core import events
from server import security
from server.app import app
from voice import stt

FAILED = []
GOOD_HOST = f"localhost:{config.SERVER_PORT}"
GOOD_ORIGIN = f"http://localhost:{config.SERVER_PORT}"


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def test_mode_aliases():
    print("MODE NAME VARIANTS")
    sunday_cases = [
        ("Sunday, hi", "sunday"), ("sunday hi", "sunday"),
        ("संडे kya haal", "sunday"), ("संडे, ok", "sunday"),
    ]
    prabh_cases = [
        ("Prabh, hi", "prabh"), ("PRABHU hi", "prabh"),
        ("प्रभ namaste", "prabh"), ("प्रभु namaste", "prabh"),
    ]
    # Phase 5: abhi sirf SUNDAY. Prabh bolne par bhi switch nahi hona chahiye.
    check("sirf sunday (config)", config.SUNDAY_ONLY, True)
    for text, want in sunday_cases:
        check(f"'{text[:12]}' -> {want}", modes.detect_mode(text, "prabh")[0], want)
    for text, _want in prabh_cases:
        check(f"'{text[:12]}' -> sunday (blocked)", modes.detect_mode(text, "sunday")[0], "sunday")
    # Text poora nahi katna — sirf mode nahi badla.
    mode, rest = modes.detect_mode("Prabh, kya haal batao", "sunday")
    check("blocked par text bacha", (mode, rest), ("sunday", "kya haal batao"))
    # Flag off karne par Prabh wapas chalu — code maarta nahi, sirf flag hai.
    config.SUNDAY_ONLY = False
    try:
        for text, want in prabh_cases:
            check(f"flag off: '{text[:12]}' -> {want}", modes.detect_mode(text, "sunday")[0], want)
        check("flag off par bina naam wahi", modes.detect_mode("kya haal", "prabh")[0], "prabh")
    finally:
        config.SUNDAY_ONLY = True
    check("aadha naam nahi maana", modes.detect_mode("sundaya kya", "sunday")[0], "sunday")
    check("6 naam config me", len(config.mode_aliases()), 6)


def test_transcribing_status():
    print("STATUS VALUES")
    check("transcribing add hua", "transcribing" in events.STATUS_VALUES, True)
    check("paanch status", len(events.STATUS_VALUES), 5)


def test_stt_limits():
    print("STT GUARD")
    check("limit 10 MB", config.AUDIO_MAX_BYTES, 10 * 1024 * 1024)
    check("limit 30 second", config.RECORD_MAX_SECONDS, 30)
    check("khaali audio", _stt_fails(b""), True)
    check("badi audio", _stt_fails(b"x" * (config.AUDIO_MAX_BYTES + 1)), True)


def _stt_fails(audio: bytes) -> bool:
    try:
        asyncio.run(stt.transcribe(audio))
    except stt.SttError:
        return True
    return False


def test_voice_endpoints():
    print("VOICE ENDPOINTS (security)")
    token = security.token()
    ok = {"host": GOOD_HOST, "origin": GOOD_ORIGIN, "x-prabh-token": token}
    client = TestClient(app)

    stt_voice_mod = __import__("server.voice_routes", fromlist=["stt_voice"])

    async def fake_transcribe(audio, *a, **kw):
        return "sunaa"

    async def fake_speak(text, mode):
        return b"MP3DATA", "edge"

    saved_stt = stt_voice_mod.stt_voice.transcribe
    saved_tts = stt_voice_mod.tts_voice.speak
    stt_voice_mod.stt_voice.transcribe = fake_transcribe
    stt_voice_mod.tts_voice.speak = fake_speak
    try:
        good = client.post("/stt", content=b"fake-audio", headers=ok)
        check("/stt sahi token se", good.status_code, 200)
        check("/stt text diya", good.json(), {"text": "sunaa"})

        good_tts = client.post("/tts", json={"text": "hi", "mode": "prabh"}, headers=ok)
        check("/tts sahi token se", good_tts.status_code, 200)
        check("/tts audio mila", good_tts.content, b"MP3DATA")
        check("/tts provider bataya", good_tts.headers.get("x-tts-provider"), "edge")

        no_token = {"host": GOOD_HOST, "origin": GOOD_ORIGIN}
        check("/stt bina token", client.post("/stt", content=b"x", headers=no_token).status_code, 401)
        check("/tts bina token", client.post("/tts", json={"text": "hi"}, headers=no_token).status_code, 401)
        check("/stt bahar se", client.post("/stt", content=b"x", headers={**ok, "origin": "https://evil.com"}).status_code, 403)
        check("/tts bahar se", client.post("/tts", json={"text": "hi"}, headers={**ok, "origin": "https://evil.com"}).status_code, 403)
        check("/stt fake host", client.post("/stt", content=b"x", headers={**ok, "host": "evil.com"}).status_code, 400)
        check("/tts fake host", client.post("/tts", json={"text": "hi"}, headers={**ok, "host": "evil.com"}).status_code, 400)
        check("/stt khali audio", client.post("/stt", content=b"", headers=ok).status_code, 400)
        check("/tts khali text", client.post("/tts", json={"text": "  "}, headers=ok).status_code, 400)
        big = {"content-length": str(config.AUDIO_MAX_BYTES + 1)}
        check("/stt badi audio", client.post("/stt", content=b"x", headers={**ok, **big}).status_code, 413)
    finally:
        stt_voice_mod.stt_voice.transcribe = saved_stt
        stt_voice_mod.tts_voice.speak = saved_tts


test_mode_aliases()
test_transcribing_status()
test_stt_limits()
test_voice_endpoints()

print()
if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Saare voice test pass.")