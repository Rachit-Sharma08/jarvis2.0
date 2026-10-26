"""tools/media.py — YouTube resolve aur media keys, network/keys mocked.

Asli network ya keyboard yahan nahi chalta: `_fetch` aur `_send_key` patch hote hain.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from tools import media

HTML = 'junk "videoId":"dQw4w9WgXcQ" aur "videoId":"aaaaaaaaaaa" junk'


class MediaTest(unittest.TestCase):
    def test_first_video_id(self):
        self.assertEqual("dQw4w9WgXcQ", media._first_video_id(HTML))
        self.assertEqual("", media._first_video_id("yahan koi video nahi"))
        self.assertEqual("", media._first_video_id(""))

    def test_play_media_opens_brave_watch_url(self):
        opened = []
        with mock.patch.object(media, "_fetch", return_value=HTML), \
                mock.patch.object(media, "open_app",
                                  side_effect=lambda name, url="": opened.append((name, url)) or "khol diya"):
            out = media.play_media("mahabharat title song")
        self.assertEqual([("brave", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")], opened)
        self.assertIn("play", out)

    def test_play_media_empty_query(self):
        self.assertIn("Kya play", media.play_media("   "))

    def test_play_media_search_fallback(self):
        opened = []
        with mock.patch.object(media, "_fetch", side_effect=OSError("no net")), \
                mock.patch.object(media, "open_app",
                                  side_effect=lambda name, url="": opened.append((name, url)) or "khol diya"):
            out = media.play_media("mahabharat")
        self.assertEqual(1, len(opened))
        self.assertEqual("brave", opened[0][0])
        self.assertIn("search_query=mahabharat", opened[0][1])
        self.assertIn("search", out.lower())

    def test_play_media_brave_missing(self):
        with mock.patch.object(media, "_fetch", return_value=HTML), \
                mock.patch.object(media, "open_app", return_value="brave.exe is PC par nahi mila."):
            out = media.play_media("mahabharat")
        self.assertIn("nahi mila", out)

    def test_media_control_keys(self):
        sent = []
        with mock.patch.object(media, "_send_key",
                               side_effect=lambda key: sent.append(key) or "ok"):
            self.assertIn("aage", media.media_control("forward"))
            self.assertIn("peeche", media.media_control("back"))
            media.media_control("play_pause")
            media.media_control("next")
            media.media_control("prev")
        self.assertEqual(["l", "j", "k", "+n", "+p"], sent)

    def test_media_control_rejects_unknown(self):
        with mock.patch.object(media, "_send_key") as send:
            out = media.media_control("rm -rf")
        self.assertIn("action", out)
        send.assert_not_called()

    def test_media_control_no_browser(self):
        with mock.patch.object(media, "_send_key", return_value="no-window"):
            self.assertIn("browser window nahi mili", media.media_control("forward"))

    def test_send_key_reports_window(self):
        with mock.patch.object(media, "_ps", return_value="no-window"):
            self.assertEqual("no-window", media._send_key("l"))
        with mock.patch.object(media, "_ps", return_value="ok"):
            self.assertEqual("ok", media._send_key("l"))


if __name__ == "__main__":
    unittest.main(verbosity=1)
