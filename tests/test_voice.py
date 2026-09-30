import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import config
import core.modes as modes
from core import events
from server import security
from server.app import app
from voice import stt, tts

FAILED = []
GOOD_HOST = f"localhost:{config.SERVER_PORT}"
GOOD_ORIGIN = f"http://localhost:{config.SERVER_PORT}"


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


class Boom:
    def __init__(self):
        self.calls = []

    async def speak(self, text, mode):
        self.calls.append((text, mode))
        raise RuntimeError("limit khatam")


class Good:
    def __init__(self, audio=b"AUDIO", name="good"):
        self.audio = audio
        self.name = name
        self.calls = []

    async def speak(self, text, mode):
        self.calls.append((text, mode))
        return self.audio


def test_chain_order():
    print("TTS PROVIDER CHAIN")
    check("chain ka order", config.TTS_CHAIN, ("elevenlabs", "cartesia", "edge"))
    check("edge aakhri hai", config.TTS_CHAIN[-1], "edge")

    eleven, cart, edge = Boom(), Boom(), Good(b"EDGE")
    saved = dict(tts.PROVIDERS)
    tts.PROVIDERS.update(elevenlabs=eleven, cartesia=cart, edge=edge)
    try:
        audio, name = asyncio.run(tts.speak("Namaste", "sunday"))
        check("do fail hone par edge bola", name, "edge")
        check("edge ka audio mila", audio, b"EDGE")

        only = Good(b"ELEVEN")
        cart.calls.clear()
        tts.PROVIDERS["elevenlabs"] = only
        _, name = asyncio.run(tts.speak("hi", "sunday"))
        check("pehla provider chala", name, "elevenlabs")
        check("baaki provider nahi chala", cart.calls, [])

        tts.PROVIDERS.update(elevenlabs=Boom(), cartesia=Good(b"CART"))
        _, name = asyncio.run(tts.speak("hi", "prabh"))
        check("eleven fail par cartesia", name, "cartesia")
    finally:
        tts.PROVIDERS.update(saved)

    tts.PROVIDERS.update(elevenlabs=Boom(), cartesia=Boom(), edge=Boom())
    try:
        asyncio.run(tts.speak("hi", "sunday"))
        check("sab fail par saaf error", "error nahi mila", "error mila")
    except tts.TtsError as exc:
        check("sab fail par saaf error", "Awaaz nahi ban paayi" in str(exc), True)
    finally:
        tts.PROVIDERS.update(saved)


def test_text_cleaning():
    print("TEXT CLEANING (awaz se pehle)")
    check("markdown hat gaya", tts.clean("*bold* #tag `code` _x_ >y"), "bold tag code x y")
    check("URL hat gaya", tts.clean("Ye dekho https://x.com/a?b=1 aur phir"), "Ye dekho aur phir")
    check("www hat gaya", tts.clean("Ye dekho www.example.com"), "Ye dekho")
    check("emoji hat gaya", tts.clean("accha laga \U0001F600✨"), "accha laga")
    check("tir nahi bacha", "✔" in tts.clean("sab theek -> ✔"), False)
    check("kitna bhi lamba", len(tts.clean("**a**" * 400)), len("a" * 400 + " " * 399))


def test_char_limit():
    print("500 CHARACTER LIMIT")
    check("limit 500 hai", config.TTS_MAX_CHARS, 500)
    check("chhota text pura", tts.clip("chhota jawab"), "chhota jawab")
    long = "word " * 400
    cut = tts.clip(long)
    check("500 se kam bola", len(cut) <= 500, True)
    check("500 se zyada nahi", len(cut) >= 400, True)
    check("sentence pura nahi kata", cut.endswith("word"), True)
    check("limit badal sakte ho", len(tts.clip(long, 50)) <= 50, True)


def test_mode_aliases():
    print("MODE NAME VARIANTS")
    cases = [
        ("Sunday, hi", "sunday"), ("sunday hi", "sunday"),
        ("संडे kya haal", "sunday"), ("संडे, ok", "sunday"),
        ("Prabh, hi", "prabh"), ("PRABHU hi", "prabh"),
        ("प्रभ namaste", "prabh"), ("प्रभु namaste", "prabh"),
    ]
    for text, want in cases:
        check(f"'{text[:12]}' -> {want}", modes.detect_mode(text, "prabh" if want == "sunday" else "sunday")[0], want)
    check("bina naam wahi mode", modes.detect_mode("kya haal", "prabh")[0], "prabh")
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

    async def fake_transcribe(audio):
        return "sunaa"

    async def fake_speak(text, mode):
        return b"MP3DATA", "edge"

    saved_stt, saved_tts = stt_voice_mod.stt_voice.transcribe, stt_voice_mod.tts_voice.speak
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


test_chain_order()
test_text_cleaning()
test_char_limit()
test_mode_aliases()
test_transcribing_status()
test_stt_limits()
test_voice_endpoints()

print()
if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Saare voice test pass.")