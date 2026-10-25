"""Alarm ki **awaaz** aur flag file — koi asli awaaz nahi.

`test_wake_alarm.py` (loop + ruke) ka saathi. Raat hai, is liye PowerShell,
edge-tts aur speaker **sab fake**:

- edge-tts crash / khaali audio par SAPI par fallback
- dono fail par `'none'` (alarm phir bhi bajta rahe)
- `C:\Windows\Media\Alarm*.wav` sirf **path** tak check
- `data/alarm_ack` temp path par (asli `data/` kabhi nahi)
- system volume code se **nahi** chheda jaata

SPLIT ki wajah: ek file 331 lines ho gayi thi (AGENTS ka 200-line niyam).
"""

import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.wakehelp import check, finish
from tests.wakecmdhelp import patch
from tools import alarm_audio, alarm_loop
from tools import alarm as alarm_tool
from tools import wake_alarm

class TestAudioFallback(unittest.TestCase):
    """edge-tts fail → SAPI → 'none'. Sab fake (asla PowerShell nahi)."""

    def test_edge_first(self):
        with patch(alarm_audio, "play_bytes", lambda a: bool(a)), \
                patch(alarm_audio, "edge_tts", lambda t, v=None: b"AUDIO"), \
                patch(alarm_audio, "sapi_speak", lambda t: True):
            check("edge chala", alarm_audio.speak("namaste", "morning"), "edge-tts")

    def test_sapi_fallback_on_empty_audio(self):
        """edge-tts ne khaali audio diya (internet nahi) → SAPI."""
        seen = []
        with patch(alarm_audio, "play_bytes", lambda a: False), \
                patch(alarm_audio, "edge_tts", lambda t, v=None: b""), \
                patch(alarm_audio, "sapi_speak",
                      lambda t: seen.append(t) or True):
            who = alarm_audio.speak("सुबह हो गई है", "Good morning sir")
        check("SAPI par gaya", who, "sapi")
        check("Hinglish wala text SAPI ko gaya",
              seen and seen[0], "Good morning sir")

    def test_both_fail_returns_none(self):
        with patch(alarm_audio, "play_bytes", lambda a: False), \
                patch(alarm_audio, "edge_tts", lambda t, v=None: b""), \
                patch(alarm_audio, "sapi_speak", lambda t: False):
            check("dono fail", alarm_audio.speak("x", "y"), "none")

    def test_edge_tts_never_raises(self):
        """edge-tts crash kare to `b''` — poora loop nahi toot-na chahiye."""
        def boom(*_a, **_k):
            raise RuntimeError("network down")
        with patch("edge_tts", "Communicate", boom):
            check("crash par khaali", alarm_audio.edge_tts("x"), b"")

    def test_sapi_never_raises(self):
        def boom(*_a, **_k):
            raise OSError("powershell missing")
        with patch("subprocess", "run", boom):
            check("crash par False", alarm_audio.sapi_speak("x"), False)



class TestAckFile(unittest.TestCase):
    """`data/alarm_ack` — asli data/ chhuate hue path TEST karo."""

    def test_default_path_under_data(self):
        check("ack file data/ me hai",
              alarm_loop.ack_file().parent.resolve(), config.DATA_DIR.resolve())

    def test_clear_ack_removes(self):
        tmp = Path("D:/jarvis-test-ack-clear.txt")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text("purana", encoding="utf-8")
        check("tha hata diya", alarm_loop.clear_ack(tmp), True)
        check("ab nahi bana", tmp.exists(), False)
        check("dobara call = kuch nahi", alarm_loop.clear_ack(tmp), False)

    def test_main_clears_stale_ack(self):
        """Purana ack bana ho to shuru me hat jaata hai (alarm na ruke)."""
        tmp = Path("D:/jarvis-test-ack-stale.txt")
        tmp.write_text("purana", encoding="utf-8")
        try:
            with patch(alarm_loop, "ack_file", lambda: tmp), \
                    patch(alarm_loop, "REPEAT_SECONDS", 0.0), \
                    patch(alarm_loop, "MAX_MINUTES", 0.0001):
                wake_alarm.main(["--no-audio"])
            check("stale ack hata diya", tmp.exists(), False)
        finally:
            tmp.unlink(missing_ok=True)

    def test_keep_ack_flag(self):
        tmp = Path("D:/jarvis-test-ack-keep.txt")
        tmp.write_text("purana", encoding="utf-8")
        try:
            with patch(alarm_loop, "ack_file", lambda: tmp), \
                    patch(alarm_loop, "REPEAT_SECONDS", 0.0), \
                    patch(alarm_loop, "MAX_MINUTES", 0.0001):
                wake_alarm.main(["--no-audio", "--keep-ack"])
            check("--keep-ack ne bachaya", tmp.exists(), True)
        finally:
            tmp.unlink(missing_ok=True)




class TestWav(unittest.TestCase):
    """Windows ka apna alarm wav — sirf path check, bajao nahi."""

    def test_wav_exists_or_reported(self):
        wav = alarm_audio.alarm_wav()
        check("wav dhoondha ya saaf message",
              bool(wav) and Path(wav).exists() or wav == "", True)

    def test_missing_wav_returns_false(self):
        check("galat path par koi awaaz nahi",
              alarm_audio.play_wav("D:/nahi/hai/alarm.wav"), False)

    def test_play_wav_never_raises(self):
        def boom(*_a, **_k):
            raise OSError("no powershell")
        with patch("subprocess", "run", boom):
            check("crash par False",
                  alarm_audio.play_wav("C:/Windows/Media/Alarm01.wav"), False)

    def test_no_volume_change(self):
        """System volume code se **nahi** chhedna (Rachit ne 70% rakha)."""
        src = (ROOT / "tools" / "alarm_audio.py").read_text(encoding="utf-8")
        for bad in ("SetVolume", "volume.SetMasterVolumeLevel",
                    "AudioFile", "waveOutSetVolume"):
            check(f"{bad} nahi hai", bad in src, False)
        # SAPI sirf apna awaz 100 rakhta hai (uska apna), system ka nahi.
        check("SAPI Volume=100 hai (apni awaaz)", "$s.Volume = 100" in src, True)


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("alarm logic theek" if result.wasSuccessful() else "FAIL")
