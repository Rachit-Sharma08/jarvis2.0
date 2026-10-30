"""Command ke waqt system media pause — asli wajah 30-Oct ko logs se mili.

`logs/jarvis.log` me 25 capture me se 13 baar `1000 chunk = 30000ms` tha
(lagatar awaaz, khamoshi kabhi nahi) aur ek transcript film ka dialogue tha.
Matlab laptop ka built-in mic background ka gaana/video bhi sun raha tha.

(`tests/test_media.py` pehle se `tools/media.py` ka hai — YouTube play. Ye file
`desktop/media.py` ke liye alag hai.)

Ye test **asli media key kabhi nahi bhejta** (`_send_key` fake hai, warna
chalte hue gaane band ho jate), aur `SETTLE_SECONDS=0` se koi wait nahi.
Sirf do cheezein pakdi jaati hain:

1. Key **tabhi** jaati hai jab humne khud pause kiya ho — warna user ka apna
   paused gaana chal padta (aur command ke baad dobara pause ho jaata).
2. Command flow me pause **ek** baar aur play **ek** baar — chahe beech me
   fail ho jaaye (`finally`), aur blocked/no-mic par kuch bhi nahi.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tests.wakecmdhelp import patch, talk  # noqa: E402
from tests.wakehelp import check, finish, truthy  # noqa: E402

import config  # noqa: E402
from desktop import media  # noqa: E402


def fresh():
    """Har test se pehle module ka `_paused` saaf, key fake, wait 0."""
    media.reset()
    keys = []

    def fake_key():
        keys.append(1)

    return keys, patch(media, "_send_key", fake_key), patch(media, "SETTLE_SECONDS", 0)


def test_pause_then_resume():
    keys, p1, p2 = fresh()
    with p1, p2:
        check("pause = kuch kiya", media.for_command(True), True)
        check("ek key gayi", len(keys), 1)
        check("play = kuch kiya", media.for_command(False), True)
        check("doosri key", len(keys), 2)


def test_no_double_send():
    """Do baar pause bolne par doosri key nahi — warna gaana chalu ho jaata."""
    keys, p1, p2 = fresh()
    with p1, p2:
        media.for_command(True)
        check("dobara pause = kuch nahi", media.for_command(True), False)
        check("phir bhi ek hi key", len(keys), 1)
        media.for_command(False)
        check("bina pause ke play = kuch nahi", media.for_command(False), False)
        check("kul do key", len(keys), 2)


def test_play_without_pause_sends_nothing():
    """App shuru hote hi play key bhejna = user ka paused gaana chal jaana."""
    keys, p1, p2 = fresh()
    with p1, p2:
        check("shuru me play", media.for_command(False), False)
        check("koi key nahi", len(keys), 0)


def test_flag_off_does_nothing():
    keys, p1, p2 = fresh()
    with p1, p2, patch(config, "MEDIA_PAUSE", False):
        check("band hai to pause nahi", media.for_command(True), False)
        check("band hai to play nahi", media.for_command(False), False)
        check("koi key nahi", len(keys), 0)


def test_reset_clears_state():
    keys, p1, p2 = fresh()
    with p1, p2:
        media.for_command(True)
        media.reset()
        check("reset ke baad pause phir chalta hai", media.for_command(True), True)
        check("do key", len(keys), 2)
    media.reset()


def test_command_pauses_once_and_resumes():
    """Poora flow: `on_media` ek baar True, ek baar False."""
    seen = []
    got, _said, _hub, _engine = talk(on_media=seen.append)
    check("command chala", got, "ok")
    check("pause phir play", seen, [True, False])


def test_command_blocked_touches_nothing():
    """Mute/lock par media bilkul nahi chhuna — na gaana rukna chahiye."""
    seen = []
    got, _said, _hub, _engine = talk(allowed=lambda: False, on_media=seen.append)
    check("blocked", got, "blocked")
    check("koi media call nahi", seen, [])


def test_command_failure_still_resumes_media():
    """Beech me crash ho to bhi gaana wapas chale (`finally` ka kaam)."""
    seen = []

    def boom(*_a, **_k):
        raise RuntimeError("mic gaya")

    try:
        talk(on_media=seen.append, capture=boom)
    except RuntimeError:
        pass
    check("pause chala", seen[:1], [True])
    check("play bhi chala", seen[1:], [False])


def test_flag_exists():
    truthy("config.MEDIA_PAUSE hai", hasattr(config, "MEDIA_PAUSE"))


for fn in (test_pause_then_resume, test_no_double_send,
           test_play_without_pause_sends_nothing, test_flag_off_does_nothing,
           test_reset_clears_state, test_command_pauses_once_and_resumes,
           test_command_blocked_touches_nothing,
           test_command_failure_still_resumes_media, test_flag_exists):
    try:
        fn()
    except Exception as exc:
        print("CRASH:", fn.__name__, type(exc).__name__, exc)

media.reset()
finish("media pause (command ke waqt)")
