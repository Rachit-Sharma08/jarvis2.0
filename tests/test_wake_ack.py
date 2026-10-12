"""Speed fix round 2 (4-Oct) — ack skip + chhoti awaaz.

Pehle ka hisa (`tests/test_speed_fix.py`) warm-up overlap + 1.2 s ki chuppi
pakda tha. Is file me do naye fix:

1. **Ack skip** (`listen.peek_speech`) — user "Jarvis" ke saath hi bolna shuru
   kar deta hai. Pehle hamari "Ji, boliye" uske **upar** bol di, command ka
   pehla shabd kat gaya aur use laga "sun nahi pa raha". Ab 0.18 s me pata chal
   jaata hai: bol raha hai to ack chhoot jaata hai, aur wahi 0.18 s mic ka
   settle + pehli awaaz pakadne ka kaam kar deta hai.
2. **Chhoti awaaz** (`tts.clip_answer`) — brain ka poora jawab HUD par rehta
   hai, par awaaz 220 char se zyada nahi boli jaati. 500 char ka playback hi
   4.3 s le raha tha.

Asli mic/TTS/speaker **kabhi nahi**: fake mic queue (`tests/wakehelp.py`) +
`say` ka spy (`tests/wakecmdhelp.py`).
"""

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tests.wakehelp import check, finish, quiet, truthy  # noqa: E402
from tests.wakecmdhelp import CHUNKS, patch, talk  # noqa: E402

import config  # noqa: E402
from voice import tts  # noqa: E402
from wake import command, listen  # noqa: E402


def test_peek_sees_speech():
    """Bol raha hai? -> True + RMS. Chunks wapas queue me (capture ke liye)."""
    from tests.wakehelp import FakeMic

    mic = FakeMic([CHUNKS[0]] * 3)
    talking, peak = listen.peek_speech(mic, threading.Event(), seconds=0.05)
    truthy("awaaz pakdi", talking)
    truthy("rms > 0", peak > 0)
    check("chunks wapas", mic.chunks.qsize(), 3)


def test_peek_silence():
    """Khamoshi -> False. Isi liye normal raasta (ack + warm-up) chalta hai."""
    from tests.wakehelp import FakeMic

    mic = FakeMic([quiet(1)] * 3)
    talking, peak = listen.peek_speech(mic, threading.Event(), seconds=0.05)
    check("khamoshi me bol nahi raha", talking, False)
    check("rms 0", peak, 0.0)


def test_peek_empty_mic():
    """Koi chunk hi nahi aaya (mic late) -> crash nahi, ack normal raasta."""
    from tests.wakehelp import FakeMic

    talking, peak = listen.peek_speech(FakeMic([]), threading.Event(), seconds=0.03)
    check("khaali queue", talking, False)
    check("peak 0", peak, 0.0)


def test_peek_stop_event():
    """App band ho raha hai to peek bhi turant ruk jaata hai."""
    from tests.wakehelp import FakeMic

    stop = threading.Event()
    stop.set()
    talking, _peak = listen.peek_speech(FakeMic([CHUNKS[0]] * 5), stop, seconds=2.0)
    check("ruk gaya", talking, False)


def drain_six(mic, stop=None):
    """Sirf 6 chunk phenko — asli app me `drain()` ka kaam sirf wake shabd ki
    goonj hataana hai. Ye zaroori hai: agar drain sab phenk de to user ki
    "Hlo Jarvis ke saath boli hui" awaaz chhoot jayegi hi nahi (pehle ka bug)."""
    dropped = 0
    while dropped < 6:
        try:
            mic.chunks.get_nowait()
        except Exception:
            break
        dropped += 1
    return dropped


def test_ack_skipped_when_talking():
    """User "Jarvis" ke saath hi bol raha hai -> 'Ji, boliye' **nahi** boli.

    `drain_six` zaroori hai: asli `drain()` 400 chunk tak phenk deta hai, is liye
    test ki pre-loaded queue wahin khatam ho jati thi aur peek ko kuch nahi
    milta — yaani test har dafa 'ack bola' dikhata, jabki asli app me user ki
    awaaz drain ho jati thi (Step 2 ka 'sun nahi pa raha' wahi sach)."""
    with patch(listen, "drain", drain_six):
        got, said, _hub, _engine = talk(heard="whatsapp kholo",
                                        mic_chunks=[CHUNKS[0]] * 200)
    check("command chala", got, "ok")
    check("ack nahi bola", config.ACK_ON_WAKE in said.calls, False)
    check("sirf jawab bola", len(said.calls), 1)


def test_ack_still_spoken_when_silent():
    """Normal raasta — wake ke baad khamoshi to 'Ji, boliye' zaroori hai."""
    got, said, _hub, _engine = talk(heard="kya mausam hai",
                                    mic_chunks=[quiet(1)] * 200)
    check("command chala", got, "ok")
    check("ack bola", said.calls[0], config.ACK_ON_WAKE)


def test_answer_spoken_short_but_hud_full():
    """HUD (engine event) par poora jawab, awaaz me chhoti."""
    long_answer = ("Yeh bahut lambi baat hai. " * 12).strip()          # ~330 char
    out = [{"type": "message", "role": "assistant", "text": long_answer}]
    _got, said, _hub, _engine = talk(heard="kya mausam hai", out=out)
    check("poora text brain se aaya", len(long_answer) > config.VOICE_ANSWER_MAX_CHARS, True)
    check("brain ko poora gaya", _engine.calls[0][0], "kya mausam hai")
    spoken = said.calls[-1]
    check("spoken chhota (<=220)", len(spoken) <= config.VOICE_ANSWER_MAX_CHARS, True)
    check("spoken khaali nahi", len(spoken) > 20, True)
    check("poora text brain ke paas gaya", _engine.calls[0][0], "kya mausam hai")


def test_clip_answer_sentence_boundary():
    """Awaaz vaakya ke end par katni hai, beech se nahi."""
    text = ("Pehla vaakya yahan khatam. Doosra vaakya bhi yahan khatam. " * 4).strip()
    out = tts.clip_answer(text, 120)
    truthy("chhoti hui", len(out) <= 120)
    check("poora vaakya", out.endswith("."), True)
    check("vaakya ki shuruaat bachi", out.startswith("Pehla vaakya"), True)


def test_clip_answer_single_long_sentence():
    """Ek hi lambe vaakya me koi '. ' nahi — tab `clip()` (word boundary)."""
    text = "a" * 400
    out = tts.clip_answer(text, 100)
    check("100 se kam", len(out) <= 100, True)
    check("spaces nahi todi", " " in out, False)


def test_clip_answer_short_untouched():
    check("chhota jawab waisa hi", tts.clip_answer("Ji, mausam theek hai."), "Ji, mausam theek hai.")
    check("khaali", tts.clip_answer(""), "")


def test_config_defaults():
    check("peek 0.18 s", config.COMMAND_ACK_PEEK_SECONDS, 0.18)
    check("awaaz 220 char", config.VOICE_ANSWER_MAX_CHARS, 220)
    truthy("clip_answer config se limit leta hai",
           len(tts.clip_answer("x" * 400)) <= config.VOICE_ANSWER_MAX_CHARS)
    check("command.py me bhi wahi guard", command._is_sleep("so jao"), True)


for fn in (test_peek_sees_speech, test_peek_silence, test_peek_empty_mic,
           test_peek_stop_event, test_ack_skipped_when_talking,
           test_ack_still_spoken_when_silent,
           test_answer_spoken_short_but_hud_full,
           test_clip_answer_sentence_boundary, test_clip_answer_single_long_sentence,
           test_clip_answer_short_untouched, test_config_defaults):
    try:
        fn()
    except Exception as exc:
        print("CRASH:", fn.__name__, type(exc).__name__, exc)

finish("ack skip + chhoti awaaz")