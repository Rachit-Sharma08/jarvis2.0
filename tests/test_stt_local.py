"""Local STT (faster-whisper) — provider chain, WAV parsing, aur local raasta.

**Kyun:** `GROQ_API_KEY` khaali hone par har command "Sun nahi paya" par girti
thi. Ab `auto` par local model chalta hai. Asli model load nahi hota (`_MODEL`
fake hai), is liye test 1 second me khatam hota hai.
"""

import asyncio
import io
import sys
import time
import unittest
import wave
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.stthelper import FakeModel, wav_bytes
from tests.wakecmdhelp import patch
from tests.wakehelp import check, finish
from voice import stt, stt_local


class TestAvailable(unittest.TestCase):
    def setUp(self):
        self.saved = (config.STT_LOCAL, config.STT_LOCAL_MODEL, stt_local._BROKEN)

    def tearDown(self):
        config.STT_LOCAL, config.STT_LOCAL_MODEL, stt_local._BROKEN = self.saved

    def test_real_model_present(self):
        stt_local._BROKEN = ""
        check("model folder + library maujood", stt_local.available(), True)

    def test_off_switch(self):
        for value in ("off", "0", "false", "no", "disabled"):
            config.STT_LOCAL = value
            check(f"'{value}' = band", stt_local.available(), False)

    def test_missing_folder(self):
        config.STT_LOCAL = "auto"
        config.STT_LOCAL_MODEL = str(Path(config.STT_LOCAL_MODEL) / "nope")
        check("folder nahi = band", stt_local.available(), False)

    def test_broken_load_remembers(self):
        stt_local._BROKEN = "RuntimeError: boom"
        check("load fail yaad rehta hai", stt_local.available(), False)


class TestProvider(unittest.TestCase):
    """Chain: Groq key > local > khaali. `JARVIS_STT_LOCAL` se force."""

    def setUp(self):
        self.saved = (config.STT_LOCAL, config.has_groq, stt_local.available)

    def tearDown(self):
        config.STT_LOCAL, config.has_groq, stt_local.available = self.saved

    def pick(self, mode, groq, local):
        config.STT_LOCAL = mode
        config.has_groq = lambda: groq
        stt_local.available = lambda: local
        return stt.provider()

    def test_auto_prefers_groq_then_local(self):
        check("auto + key = groq", self.pick("auto", True, True), "groq")
        check("auto + key nahi = local", self.pick("auto", False, True), "local")
        check("auto + dono nahi = ''", self.pick("auto", False, False), "")

    def test_forced_local(self):
        for mode in ("local", "whisper", "offline"):
            check(f"{mode} + key bhi ho to local", self.pick(mode, True, True), "local")
        check("local model nahi = ''", self.pick("local", True, False), "")

    def test_forced_groq(self):
        check("groq + key = groq", self.pick("groq", True, True), "groq")
        check("groq + key nahi = '' (local par nahi girta)",
              self.pick("groq", False, True), "")

    def test_off(self):
        check("off + key nahi = ''", self.pick("off", False, True), "")

    def test_error_messages(self):
        config.STT_LOCAL = "local"
        check("local missing ka message",
              "Local STT model" in str(stt._provider_error()), True)
        config.STT_LOCAL = "auto"
        check("dono missing ka message",
              "GROQ_API_KEY" in str(stt._provider_error()), True)


class TestSource(unittest.TestCase):
    def test_16k_mono_is_numpy(self):
        samples = np.full(16000, 0.25, dtype=np.float32)
        out = stt_local._source(wav_bytes(samples, 16000, 1))
        check("numpy mila", isinstance(out, np.ndarray), True)
        check("length", out.size, 16000)
        check("amplitude", round(float(out[0]), 3), 0.25)

    def test_other_formats_go_to_av(self):
        cases = {
            "44.1k mono": wav_bytes(np.zeros(44100, dtype=np.float32), 44100, 1),
            "16k stereo": wav_bytes(np.zeros(32000, dtype=np.float32), 16000, 2),
            "webm": b"\x1aE\xdf\xa3" + b"\x00" * 32,
        }
        for name, audio in cases.items():
            out = stt_local._source(audio)
            check(f"{name} = BytesIO", isinstance(out, io.BytesIO), True)
            check(f"{name} bytes wahi", out.getvalue(), audio)

    def test_empty_frames(self):
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(16000)
        check("khaali WAV = BytesIO", isinstance(
            stt_local._source(buf.getvalue()), io.BytesIO), True)


class TestLocalTranscribe(unittest.TestCase):
    def setUp(self):
        self.model = FakeModel()
        self.saved = (config.STT_LOCAL, stt_local._MODEL)
        config.STT_LOCAL = "local"
        stt_local._MODEL = self.model

    def tearDown(self):
        config.STT_LOCAL, stt_local._MODEL = self.saved

    def test_text_and_kwargs(self):
        audio = wav_bytes(np.full(16000, 0.2, dtype=np.float32))
        text = stt_local.transcribe(audio)
        check("text wapas", text, "Jarvis WhatsApp kholo")
        kw = self.model.calls[0]["kw"]
        check("language en", kw["language"], "en")
        check("beam 1 (tez)", kw["beam_size"], 1)
        check("vad_filter off (hamara VAD pehle chala)",
              kw["vad_filter"], False)
        check("timestamps nahi", kw["without_timestamps"], True)
        check("hinglish prompt (Mahabharat)",
              "Mahabharat" in kw["initial_prompt"], True)

    def test_async_path_uses_local(self):
        async def go():
            return await stt.transcribe(
                wav_bytes(np.full(16000, 0.2, dtype=np.float32)), 1200)
        check("stt.transcribe local se text", asyncio.run(go()),
              "Jarvis WhatsApp kholo")
        check("local model hi chala", len(self.model.calls), 1)


class TestGuards(unittest.TestCase):
    def setUp(self):
        self.saved = (config.STT_LOCAL, stt_local._MODEL,
                      config.STT_LOCAL_DEADLINE_SECONDS)
        config.STT_LOCAL = "local"

    def tearDown(self):
        (config.STT_LOCAL, stt_local._MODEL,
         config.STT_LOCAL_DEADLINE_SECONDS) = self.saved

    def run_with(self, model, duration_ms=1200):
        stt_local._MODEL = model

        async def go():
            return await stt.transcribe(
                wav_bytes(np.full(16000, 0.2, dtype=np.float32)), duration_ms)
        return asyncio.run(go())

    def test_short_recording(self):
        with self.assertRaises(stt.SttError) as box:
            self.run_with(FakeModel(), duration_ms=300)
        check("600ms se kam reject", "chhoti" in str(box.exception), True)

    def test_local_deadline(self):
        """Local model atke to caller ceiling par turant laute (daemon thread)."""
        config.STT_LOCAL_DEADLINE_SECONDS = 0.2
        start = time.perf_counter()
        with self.assertRaises(stt.SttError) as box:
            self.run_with(FakeModel(sleep=3.0))
        took = time.perf_counter() - start
        check("saaf message", "waqt" in str(box.exception), True)
        check(f"caller turant luta ({took:.2f}s)", took < 1.2, True)

    def test_silence_hallucination_rejected(self):
        with self.assertRaises(stt.SttError):
            self.run_with(FakeModel(text="Thank you for watching."))


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules["__main__"])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    finish("local STT theek" if result.wasSuccessful() else "FAIL")
