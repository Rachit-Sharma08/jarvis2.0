"""R-3 — sunne ki galtiyan: beep ack, turant capture, khaali STT skip.

Pehle jo hota tha (12-Oct ka live log): wake ke baad "Ji, boliye" ~5 s (ElevenLabs
401 + edge + speaker), phir 1 s warmup + drain user ki command phenk deta tha; aur
khaali STT text par bhi brain call chala tha. Ab: chhota beep, capture turant,
khaali text par brain nahi.

**Sirf fakes** — `FakeMic` (`tests/wakehelp.py`) + `patch/Spy/FakeEngine`
(`tests/wakecmdhelp.py`). Asli mic, Vosk, speaker ya brain kabhi nahi chalta
(`playback.say`/`playback.beep` dono spy hain). `data/` temp par (E-1b).
"""

import queue
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.datasafe import isolated_data                  # noqa: E402
from tests.wakehelp import check, finish, loud, quiet, truthy  # noqa: E402
from tests.wakecmdhelp import Spy, patch, talk            # noqa: E402

import config                                           # noqa: E402
from wake import listen                                  # noqa: E402

SPEECH = 40             # 40 x 30 ms = 1.2 s ki command


def drain_six(mic, stop=None):
    """Asli `drain()` ki jagah - sirf 6 chunk. Wajah `test_wake_ack.py` me hai:
    400 chunk ka asli drain test ki pre-loaded queue khaali kar deta tha."""
    for _ in range(6):
        try:
            mic.chunks.get_nowait()
        except (queue.Empty, AttributeError):
            break
    return 6


def make_capture(seen):
    """capture ka fake: queue ka saara audio nikaal kar `seen` me rakhta hai."""
    def capture(mic, stop=None):
        while True:
            try:
                seen.append(mic.chunks.get_nowait())
            except (queue.Empty, AttributeError):
                break
        return list(seen) or [loud(1)]
    return capture


def test_drop_seconds_measured():
    """(i) `drop_seconds` sirf beep ka hissa phenkta hai - 0.2 s = 7 chunk."""
    with isolated_data():
        mic = type("M", (), {})()
        mic.chunks = queue.Queue()
        for _ in range(60):
            mic.chunks.put_nowait(quiet(1))
        dropped = listen.drop_seconds(mic, None, config.ACK_BEEP_DROP_SECONDS)
        check("sirf beep wala phenka", dropped, 7)
        check("baaki 53 bache", mic.chunks.qsize(), 53)


def test_beep_then_capture_keeps_speech():
    """(i) ACK_BEEP=1: beep, boli hui ack nahi, warmup nahi, aur beep ke baad
    aayi 1.2 s ki command poori capture me."""
    with isolated_data():
        seen, warm = [], Spy(0)
        real_drop = listen.drop_seconds

        def drop_then_feed(mic, stop=None, seconds=0.2):
            """Beep ka audio phenko, phir user bolta hai (queue me daalo)."""
            gone = real_drop(mic, stop, seconds)
            for _ in range(SPEECH):
                mic.chunks.put_nowait(loud(1))
            return gone

        with patch(listen, "drop_seconds", drop_then_feed), \
                patch(listen, "warmup", warm), \
                patch(listen, "drain", drain_six):
            got, said, _hub, engine = talk(
                heard="mausam kaisa hai", mic_chunks=[], beep=True,
                capture=make_capture(seen))

        check("command chala", got, "ok")
        check("beep ek baar baja", len(said.beeps.calls), 1)
        check("koi boli hui ack nahi (sirf jawab)", len(said.calls), 1)
        check("warmup nahi chala", warm.calls, [])
        check("command poori capture hui", len(seen), SPEECH)
        check("brain chala", len(engine.calls), 1)


def test_one_breath_no_beep_no_drain():
    """(ii) User "Jarvis" ke saath hi bol raha hai -> beep bhi nahi, warmup/drop
    bhi nahi; queue me bachi speech capture tak pohunchti hai."""
    with isolated_data():
        seen, warm, drop = [], Spy(0), Spy(0)
        with patch(listen, "warmup", warm), patch(listen, "drop_seconds", drop), \
                patch(listen, "drain", drain_six), \
                patch(listen, "peek_speech", lambda *a, **k: (True, 0.5)):
            got, said, _hub, engine = talk(
                heard="mausam kaisa hai",
                mic_chunks=[loud(1)] * (SPEECH + 6), beep=True,
                capture=make_capture(seen))

        check("command chala", got, "ok")
        check("beep nahi", said.beeps.calls, [])
        check("sirf jawab bola", len(said.calls), 1)
        check("warmup nahi", warm.calls, [])
        check("drop_seconds nahi", drop.calls, [])
        check("bachi speech poori mili", len(seen), SPEECH)
        check("brain chala", len(engine.calls), 1)


def test_blank_stt_skips_brain():
    """(iii) STT ne sirf space diya -> brain call 0, 'samajh nahi aaya' bola."""
    with isolated_data():
        for heard in ("   ", "", "jarvis"):
            got, said, _hub, engine = talk(heard=heard, beep=True)
            check(f"'{heard}' par brain nahi ({len(engine.calls)})",
                  len(engine.calls), 0)
            check(f"'{heard}' par no-text", got, "no-text")
            check(f"'{heard}' par samajh nahi aaya bola",
                  config.NOT_UNDERSTOOD in said.calls, True)


def test_flag_off_keeps_old_path():
    """(iv) ACK_BEEP=0: purana raasta - boli hui ack + warmup, beep nahi."""
    with isolated_data():
        warm = Spy(0)
        with patch(listen, "warmup", warm):
            got, said, _hub, engine = talk(heard="mausam kaisa hai",
                                           mic_chunks=[quiet(1)] * 200,
                                           beep=False)
        check("command chala", got, "ok")
        check("beep nahi baja", said.beeps.calls, [])
        truthy("boli hui ack", said.calls and said.calls[0] in config.ACK_ON_WAKE)
        check("warmup chala", len(warm.calls), 1)
        check("brain chala", len(engine.calls), 1)


test_drop_seconds_measured()
test_beep_then_capture_keeps_speech()
test_one_breath_no_beep_no_drain()
test_blank_stt_skips_brain()
test_flag_off_keeps_old_path()
finish("listen flow (beep ack + turant capture + khaali STT skip) theek")