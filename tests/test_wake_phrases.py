"""Wake phrase + Vosk grammar — naam ke test ka doosra hissa (5-Oct split).

`tests/test_name_jarvis.py` 200 cross kar gaya, is liye ye hissa alag file me.
Yahan teen baatein pakdi hain:

1. **Trigger** — "jarvis", "hello jarvis", "hey jarvis" sab hit; "jarvisly"/
   "jervis"/"sunday" nahi.
2. **Grammar me shabd, poori phrase nahi** — Vosk/Kaldi multi-word phrase ko
   apne lexicon se map nahi kar pata. 5-Oct ke live log me `sun liya: 'hello'`
   phir `sun liya: 'yo'` alag finals aaye the (trigger nahi hua); ab grammar
   me har shabd alag hai (`config_name.grammar_words()`).
3. **Legacy "sunday" default band** — list me maujood, grammar me nahi;
   `PRABH_WAKE_LEGACY=1` par aa jaata hai.

Koi asli Vosk/mic nahi — `config_name` aur `wake.phrase` pure functions hain.
"""

import json
import os
import sys
import unittest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
import config_name
from wake import phrase


class TestWakePhrases(unittest.TestCase):
    """Vosk grammar + phrase matching."""

    def test_variants_hit(self):
        for text in ("jarvis", "hello jarvis", "hey jarvis", "Hello, Jarvis!",
                     "jarvis kholo", "hey jarvis whatsapp kholo"):
            self.assertTrue(phrase.hit(text), text)
            self.assertTrue(phrase.phrase(text), text)

    def test_near_misses_do_not_hit(self):
        for text in ("sun", "sunday", "jarvisly", "jervis", "sunay"):
            self.assertFalse(phrase.hit(text), text)

    def test_grammar_has_words_and_unk(self):
        words = json.loads(config.WAKE_GRAMMAR)
        for want in ("hello", "hey", "jarvis", "[unk]"):
            self.assertIn(want, words)
        for bad in ("hello jarvis", "hey jarvis"):
            self.assertNotIn(bad, words, "multi-word phrase grammar me nahi")
        self.assertEqual(words[-1], "[unk]", "[unk] aakhri hona chahiye")
        self.assertEqual(len(words), len(set(words)), "duplicate shabd")

    def test_legacy_off_by_default(self):
        self.assertFalse(config_name.legacy_enabled())
        self.assertTrue(config_name.LEGACY_WAKE_PHRASES)   # list me maujood
        words = json.loads(config.WAKE_GRAMMAR)
        self.assertNotIn("sunday", words)
        self.assertFalse(phrase.hit("hey sunday"))          # trigger nahi
        self.assertEqual(config.WAKE_WORDS, ("jarvis",))

    def test_legacy_can_be_switched_on(self):
        # `legacy_enabled()` env har call par padhta hai, is liye test me
        # `os.environ` badal kar turant dekh sakte hain.
        os.environ["PRABH_WAKE_LEGACY"] = "1"
        try:
            words = json.loads(config_name.wake_grammar())
            self.assertIn("sunday", words)
            self.assertIn("jarvis", words)
            self.assertNotIn("hey sunday", words)     # shabd alag-alag
            self.assertEqual(config_name.wake_words(), ("jarvis", "sunday"))
        finally:
            os.environ.pop("PRABH_WAKE_LEGACY", None)


if __name__ == "__main__":
    unittest.main(verbosity=2)