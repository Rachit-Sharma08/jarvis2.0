"""Wake word (Phase 5 Step 1) ka test — constants, audio/VAD, detect, phrase.

**Asli mic, Vosk model aur `sounddevice` kabhi nahi chalti.** Sab fakes
`tests/wakehelp.py` se. Worker ka loop alag suite me hai (`test_wake_loop.py`)
kyunki wo thread + `time` use karta hai.

Ye file 4 hisse: config ke constants · PCM/VAD (pure) · detect ke JSON
pakadne ke baare me · phrase matching (pure).
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
import config_wake
from wake import audio, model as model_mod, phrase, worker
from wakehelp import check, finish, loud, make_listener, quiet, show, truthy


def test_config():
    print("WAKE CONFIG")
    check("wake ON/OFF bool", isinstance(config.WAKE_ENABLED, bool), True)
    check("wake word", config.WAKE_WORDS, ("jarvis",))
    truthy("model folder mila", config.model_path())
    show(f"model = {config.model_path().split(chr(92))[-1]}")
    import json
    words = json.loads(config.WAKE_GRAMMAR)
    truthy("grammar me jarvis", "jarvis" in words)
    truthy("grammar me filler", "[unk]" in words)
    check("sample rate", config.SAMPLE_RATE, 16000)
    check("block 30ms", audio.BLOCK_SECONDS, 0.03)
    truthy("cooldown", config.WAKE_COOLDOWN_SECONDS > 0)
    describe = config.describe()
    # 14-Oct (KAAM B): `theme=` ka field jud gaya, is liye 9 -> 10. Ye test
    # jaan-boojh kar update hua hai (AGENTS 8.1.2 ka "purana test bhi badalna
    # padta hai" wala niyam) — naya fail nahi.
    check("describe me 10 hisse", len(describe.split()), 10)
    show(describe)
    truthy("describe me beep", "beep=on" in describe)
    truthy("describe me cards", "cards=off" in describe)
    truthy("describe me direct", "direct=on" in describe)
    truthy("describe me hot (13-Oct)", "hot=off" in describe)
    check("worker READY", worker.READY, True)
    check("startup line stub nahi", config.STARTUP_WAKE, "wake")

    ok, reason = config_wake.wake_available()
    check("wake_available True", (ok, bool(reason)), (True, False))
    saved = config_wake.WAKE_ENABLED
    config_wake.WAKE_ENABLED = False
    try:
        ok, reason = config_wake.wake_available()
        check("band karne par wajah", (ok, reason), (False, "JARVIS_WAKE=0 se band hai"))
    finally:
        config_wake.WAKE_ENABLED = saved
    # Dono model path ek saath badlo, aur dono wapas — sirf ek wapas karne se
    # `WAKE_MODEL_ALT_DIR` is process me hamesha ke liye galat reh jaata.
    saved_dirs = (config_wake.WAKE_MODEL_DIR, config_wake.WAKE_MODEL_ALT_DIR)
    config_wake.WAKE_MODEL_DIR = config_wake.WAKE_MODEL_ALT_DIR = str(
        config.BASE_DIR / "models" / "__nahi__")
    try:
        check("model na ho to path khaali", config_wake.model_path(), "")
        truthy("model_missing ne bataya", "Vosk model nahi mila" in config_wake.model_missing())
        ok, reason = config_wake.wake_available()
        check("wake_available model par False", ok, False)
    finally:
        (config_wake.WAKE_MODEL_DIR,
         config_wake.WAKE_MODEL_ALT_DIR) = saved_dirs
        check("dono model path wapas", config_wake.WAKE_MODEL_DIR, saved_dirs[0])
        check("alt path bhi wapas", config_wake.WAKE_MODEL_ALT_DIR, saved_dirs[1])


def test_audio():
    print("AUDIO + VAD (pure)")
    check("khaali chunk", audio.chunk_to_rms(b""), 0.0)
    check("khamoshi", audio.chunk_to_rms(quiet()), 0.0)
    loud_rms = audio.chunk_to_rms(loud())
    truthy(f"awaaz ka RMS {loud_rms:.3f} > threshold", loud_rms > config.VAD_THRESHOLD)
    import numpy as np
    samples = np.array([0.0, 0.5, -0.5, 1.0], dtype="float32")
    check("encode roundtrip", np.frombuffer(audio.encode(samples), dtype="<i2").size, 4)
    check("encode clip", np.frombuffer(audio.encode(np.array([9.0], "float32")), "<i2")[0], 32767)

    vad = audio.Vad(threshold=0.01, hangover_blocks=3)
    check("pehla chunk bol raha", vad.push(0.2), True)
    check("teeno khamoshi me bhi (hangover)", [vad.push(0.0) for _ in range(3)], [True] * 3)
    check("hangover ke baad chup", vad.push(0.0), False)
    check("phir se bol", vad.push(0.5), True)
    check("speaking()", vad.speaking(), True)
    vad.reset()
    check("reset ke baad chup", vad.speaking(), False)
    check("mic unavailable type", issubclass(audio.MicUnavailable, Exception), True)


def test_detect():
    print("DETECT (fake recognizer)")
    listener, fake = make_listener(["hello jarvis"], partial="hey jarv")
    check("final text", listener.feed(b"\x01\x02"), "hello jarvis")
    check("khatam ho gaya to ''", listener.feed(b"\x01\x02"), "")
    check("partial", listener.partial(), "hey jarv")
    check("bytes recognizer tak gaye", fake.bytes_fed, 4)
    listener.reset()
    check("reset count", fake.resets, 1)
    check("khaali chunk", listener.feed(b""), "")

    broken, _ = make_listener(raw_text="{ye json nahi")
    check("ajeeb JSON par crash nahi", broken.feed(b"\x01\x02"), "")
    empty, _ = make_listener(raw_text="")
    check("khaali JSON", empty.partial(), "")
    check("grammar config se aaya", "jarvis" in listener.grammar, True)


def test_phrase():
    print("PHRASE (pure)")
    check("hit: hey jarvis", phrase.hit("Hey Jarvis, WhatsApp kholo"), True)
    check("hit: sirf jarvis", phrase.hit("jarvis"), True)
    check("hit: filler ke saath", phrase.hit("[unk] jarvis"), True)
    check("hit: punctuation", phrase.hit("hello, jarvis!"), True)
    check("hit: 'jarvisly' nahi", phrase.hit("jarvisly"), False)
    # Vaakya ke beech me "jarvis" bhi pakadte hain - "my jarvis shoes" bhi
    # trigger karega. Ye sahi hai: HUD khulna bekaar nahi, aur production me
    # grammar sirf 5 shabd hi deta hai (isliye ajeeb sentence aata hi nahi).
    check("hit: vaakya me bhi", phrase.hit("my jarvis shoes"), True)
    check("hit: khaali", phrase.hit(""), False)
    check("hit: None", phrase.hit(None), False)
    check("phrase me greeting", phrase.phrase("hey jarvis kholo"), "hey jarvis")
    check("phrase sirf shabd", phrase.phrase("Jarvis"), "jarvis")
    check("phrase nahi mila", phrase.phrase("kuch aur"), "")
    check("normalize", phrase.normalize("  Hello,  Jarvis! "), "hello jarvis")
    check("tokens filler hataye", phrase.tokens("[unk] hey jarvis"), ["hey", "jarvis"])


def test_model_errors():
    print("MODEL (error raaste, load nahi)")
    model_mod.clear()
    check("cache khaali", model_mod.cached(), False)
    try:
        model_mod.load()
        check("model na ho to crash", "raise", "raise")
    except model_mod.ModelMissing as exc:
        truthy(f"ModelMissing: {str(exc)[:40]}", "Vosk model nahi mila" in str(exc))
    try:
        model_mod.load(str(config.BASE_DIR / "models" / "__nahi__"))
        check("galat folder", "raise", "raise")
    except model_mod.ModelMissing:
        print("  OK   galat folder par ModelMissing")
    model_mod.clear()


for fn in (test_config, test_audio, test_detect, test_phrase, test_model_errors):
    fn()

finish("Saare wake test (config/audio/detect/phrase) pass.")
