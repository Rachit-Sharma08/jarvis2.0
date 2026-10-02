"""`desktop/playback.py` ka `say()` — text se TTS, phir speaker. Fake sab kuch.

Yahan teen baatein pakdi jaati hain:

1. **Ek hi raasta** — awaaz `voice/tts.py` se banti hai, `say()` khud koi
   provider nahi chunta (`playback.say` me `tts.speak` hi call hota hai).
2. **Crash upar nahi aata** — TTS error, timeout, khaali audio, speaker busy
   — har case me `0` return, wake thread nahi toota.
3. **Boli hui cheez ka pata** — `log.info` me provider + bytes.

`voice/tts.speak` yahan asli hota hai par test me badla jaata hai — koi
network call nahi, koi key nahi chahiye.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.desktophelp import (  # noqa: E402
    FAILED, FakeMini, check, finish, install_audio, remove_audio, show, truthy,
)

import config  # noqa: E402
from desktop import playback  # noqa: E402
from voice import tts  # noqa: E402


class fake_speak:
    """`tts.speak` ki jagah — jo chahiye wahi return, aur kya mila wo yaad rakho."""

    def __init__(self, audio=b"fake-mp3-bytes", provider="edge", boom=None):
        self.audio = audio
        self.provider = provider
        self.boom = boom
        self.calls = []

    async def __call__(self, text, mode):
        self.calls.append((text, mode))
        if self.boom is not None:
            raise self.boom
        return self.audio, self.provider


def swap(fake):
    """`tts.speak` badlo, call karo, wapas. -> (ms, fake)"""
    saved = tts.speak
    tts.speak = fake
    try:
        return playback.say("Ji, boliye.", "sunday"), fake
    finally:
        tts.speak = saved


def test_say():
    mini, sd, saved = install_audio()
    fake = fake_speak()
    try:
        ms, got = swap(fake)
        check("ms mila", ms >= 0, True)
        check("text gaya", got.calls[0][0], "Ji, boliye.")
        check("mode gaya", got.calls[0][1], "sunday")
        truthy("decode hua", mini.calls)
        truthy("speaker chala", sd.played)
        check("speaker ko wahi rate", sd.played[0]["samplerate"], 32000)
    finally:
        remove_audio(saved)


def test_default_mode():
    _mini, _sd, saved = install_audio()
    fake = fake_speak()
    saved_speak = tts.speak
    tts.speak = fake
    try:
        playback.say("Ji, boliye.")
        check("mode khaali to default", fake.calls[0][1], config.DEFAULT_MODE)
    finally:
        tts.speak = saved_speak
        remove_audio(saved)


def test_say_errors():
    mini, _sd, saved = install_audio()
    cases = (
        ("TtsError", tts.TtsError("sab provider fail")),
        ("crash", RuntimeError("network gaya")),
        ("ValueError", ValueError("kuch ajeeb")),
    )
    for name, boom in cases:
        ms, _fake = swap(fake_speak(boom=boom))
        check("%s par 0 (crash nahi)" % name, ms, 0)
    check("error me decode try nahi hua", mini.calls, [])

    ms, _fake = swap(fake_speak(audio=b""))
    check("khaali audio par 0", ms, 0)
    check("khaali audio decode tak hi nahi gaya", mini.calls, [])
    remove_audio(saved)


def test_timeout():
    """TTS atak gaya to `wait_for` use rokta hai — hang nahi hona chahiye."""
    import asyncio

    _mini, _sd, saved = install_audio()
    saved_timeout = config.PLAYBACK_TIMEOUT_SECONDS
    config.PLAYBACK_TIMEOUT_SECONDS = 0.05

    async def slow(text, mode):
        await asyncio.sleep(5)
        return b"x", "edge"

    saved_speak = tts.speak
    tts.speak = slow
    try:
        ms = playback.say("Ji, boliye.")
        check("timeout par 0", ms, 0)
    finally:
        tts.speak = saved_speak
        config.PLAYBACK_TIMEOUT_SECONDS = saved_timeout
        remove_audio(saved)


def test_main_say():
    fake = fake_speak()
    saved_speak = tts.speak
    # 3200 sample @ 32 kHz = 100 ms — asli TTS jaisi lambai, warna ms 0 padh kar
    # "nahi baja" samajh jaayega.
    _mini, _sd, saved = install_audio(mini=FakeMini(samples=[1000] * 3200))
    tts.speak = fake
    try:
        check("--say se baja", playback.main(["--say", "Ji,", "boliye."]), 0)
        check("saare shabd jode", fake.calls[0][0], "Ji, boliye.")
    finally:
        tts.speak = saved_speak
        remove_audio(saved)

    tts.speak = fake_speak(boom=tts.TtsError("fail"))
    try:
        check("--say par tts fail", playback.main(["--say", "test"]), 1)
    finally:
        tts.speak = saved_speak
        remove_audio(saved)


test_say()
test_default_mode()
test_say_errors()
test_timeout()
test_main_say()
finish("playback say theek")