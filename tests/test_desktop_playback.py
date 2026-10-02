"""`desktop/playback.py` — bytes se PCM, PCM se speaker. Dono fake.

**Asli speaker kabhi nahi bajti.** `miniaudio` aur `sounddevice` ke fake
`tests/desktophelp.py` se `sys.modules` me lagte hain (`playback._modules()`
late import karta hai, is liye bas `sys.modules` se kaam chal jaata hai).

Sirf decode/play/device wala hissa — text se awaaz (`say`) doosri file
`test_desktop_play_say.py` me hai.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.desktophelp import (  # noqa: E402
    FAILED, FakeFormat, FakeMini, FakeSd, check, finish, install_audio,
    remove_audio, show, truthy,
)

import config  # noqa: E402
from desktop import playback  # noqa: E402

PCM = (1000, 2000, -3000, 4000)


def test_available():
    _mini, _sd, saved = install_audio()
    try:
        ok, reason = playback.available()
        truthy("speaker hai", ok)
        check("wajah khaali", reason, "")
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio(sd=FakeSd(outputs=0))
    try:
        ok, reason = playback.available()
        check("device nahi -> False", ok, False)
        truthy("wajah batayi", reason)
        show(reason)
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio(sd=FakeSd(devices_boom=True))
    try:
        ok, reason = playback.available()
        check("check crash par bhi False", ok, False)
        truthy("exception ka naam reason me", "RuntimeError" in reason)
    finally:
        remove_audio(saved)


def test_decode():
    mini, _sd, saved = install_audio(mini=FakeMini(samples=PCM))
    try:
        samples, rate = playback.decode(b"fake-mp3-bytes")
        check("int16 dtype", str(samples.dtype), "int16")
        check("sample count", int(samples.size), len(PCM))
        check("rate wapas mili", rate, 32000)
        call = mini.calls[0]
        check("poora buffer gaya", call["bytes"], len(b"fake-mp3-bytes"))
        check("16-bit maanga", call["output_format"], FakeFormat.SIGNED16)
        check("mono maanga", call["nchannels"], 1)
        check("config rate maangi", call["sample_rate"], config.OUTPUT_RATE)
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio()
    try:
        _samples, rate = playback.decode(b"x", rate=22050)
        check("rate override mili", rate, 22050)
    finally:
        remove_audio(saved)


def expect_error(name: str, want: str):
    """`PlaybackError` aana chahiye, aur message me `want` hona chahiye."""
    try:
        playback.decode(b"x")
    except playback.PlaybackError as exc:
        truthy(name, want in str(exc))
        return
    except Exception as exc:               # noqa: BLE001 - jaan-boojh kar check
        FAILED.append(name)
        print(f"  FAIL {name} -> PlaybackError ke bajaye {type(exc).__name__}")
        return
    FAILED.append(name)
    print(f"  FAIL {name} -> error aaya hi nahi")


def test_decode_errors():
    _mini, _sd, saved = install_audio()
    try:
        try:
            playback.decode(b"")
        except playback.PlaybackError as exc:
            truthy("khaali audio par error", "khaali" in str(exc))
        else:
            FAILED.append("khaali audio par error")
            print("  FAIL khaali audio par error")
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio(mini=FakeMini(samples=[]))
    try:
        expect_error("khali sample par error", "koi awaaz nahi")
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio(mini=FakeMini(boom=True))
    try:
        expect_error("decode crash par error", "ValueError")
    finally:
        remove_audio(saved)


def test_play():
    _mini, sd, saved = install_audio()
    try:
        ms = playback.play(b"fake-mp3")
        check("ms mila", ms >= 0, True)
        truthy("speaker ko mila", sd.played)
        got = sd.played[0]
        check("samplerate", got["samplerate"], 32000)
        check("device config se", got["device"], config.OUTPUT_DEVICE)
        check("blocking", got["blocking"], True)
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio(sd=FakeSd(boom=True))
    try:
        playback.play(b"fake-mp3")
    except playback.PlaybackError as exc:
        truthy("speaker busy par error", "RuntimeError" in str(exc))
    else:
        FAILED.append("speaker busy par error")
        print("  FAIL speaker busy par error")
    finally:
        remove_audio(saved)


def test_devices():
    _mini, _sd, saved = install_audio()
    try:
        rows = playback.devices()
        check("ek device", len(rows), 1)
        check("naam", rows[0][1], "Fake Speakers")
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio(sd=FakeSd(devices_boom=True))
    try:
        check("crash par khaali list", playback.devices(), [])
    finally:
        remove_audio(saved)


def test_main():
    _mini, _sd, saved = install_audio()
    try:
        check("--list par device", playback.main(["--list"]), 0)
        check("kuch argument nahi", playback.main([]), 2)
        check("--say bina shabd", playback.main(["--say"]), 2)
    finally:
        remove_audio(saved)

    _mini, _sd, saved = install_audio(sd=FakeSd(devices_boom=True))
    try:
        check("speaker na ho to --list", playback.main(["--list"]), 1)
        check("speaker na ho to --say", playback.main(["--say", "test"]), 1)
    finally:
        remove_audio(saved)


test_available()
test_decode()
test_decode_errors()
test_play()
test_devices()
test_main()
finish("playback decode + speaker theek")