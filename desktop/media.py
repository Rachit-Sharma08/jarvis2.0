"""Command ke waqt system media pause — aur jawab ke baad wapas play.

**Kyun:** laptop ka built-in mic speaker ki awaaz bhi sunta hai. Gaana/video
chalta ho to Whisper usi ko command samajh leta hai — `logs/jarvis.log` me
`1000 chunk = 30000ms` wale capture aur ek film ka dialogue transcript isi ki
nishani hain (30-Oct).

**Kaise:** Windows ka media key (`VK_MEDIA_PLAY_PAUSE`) — wahi jo keyboard par
hota hai, is liye koi naya package nahi. Key sirf **tab** bhejte hain jab humne
khud pause kiya ho (`_paused`), warna user ka apna paused gaana chal padta.

Config: `config.MEDIA_PAUSE` (`JARVIS_MEDIA_PAUSE=0` se band).
Test me `_send_key` badal do — asli key kabhi mat bhejo.
"""

import ctypes
import time

import config
from log_setup import get_logger

log = get_logger("desktop_media")

VK_MEDIA_PLAY_PAUSE = 0xB3
KEYEVENTF_KEYUP = 0x0002
# Media app ko key maanne me ~0.1-0.2 s lagta hai; itna ruk kar capture shuru
# karte hain warna pehla aadha second phir bhi gaana hi hota hai.
SETTLE_SECONDS = 0.25

_paused = False


def _send_key() -> None:
    user32 = ctypes.windll.user32
    user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
    user32.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)


def for_command(start: bool) -> bool:
    """`start=True` = media pause, `False` = wapas play. -> kuch kiya?"""
    global _paused
    if not config.MEDIA_PAUSE:
        return False
    if start and not _paused:
        _paused = True
        _send_key()
        time.sleep(SETTLE_SECONDS)
        log.info("media pause (command ke liye)")
        return True
    if not start and _paused:
        _paused = False
        _send_key()
        log.info("media play (command ke baad)")
        return True
    return False


def reset() -> None:
    """Sirf test ke liye — module ka `_paused` bhoola do."""
    global _paused
    _paused = False
