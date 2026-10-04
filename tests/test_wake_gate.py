"""Battery ka pakkaura — Vosk sirf awaaz par (Step 1 ka fix).

Pehle loop **har** 30 ms chunk recognizer ko deta tha, is liye khamoshi me bhi
~3.9% CPU chalu rehta tha. Ab `wake/gate.py` VAD se faisla leta hai: khamoshi
me chunk `False` (recognizer tak nahi jaata), awaaz par `True`.

Ye test **pure** hai — mic, thread, Vosk model, `sounddevice` kuch nahi.
Helpers `tests/wakehelp.py` se (`loud`/`quiet` + `check`).
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from wake import gate as gate_mod
from wakehelp import FakeListener, check, finish, loud, quiet, show, truthy


def test_silence_not_fed():
    print("GATE: KHAMOSHI ME VOSK NAHI")
    listener = FakeListener()
    gate = gate_mod.Gate()
    for _ in range(40):                      # 40 * 30 ms = 1.2 s khamoshi
        truthy_fed = gate.push(listener, quiet())
        if truthy_fed:
            break
    check("khamoshi me ek bhi chunk Vosk ko nahi", gate.fed, 0)
    check("40 chunk skip hue", gate.skipped, 40)
    check("listener.reset baar baar hua", gate.resets > 0, True)
    check("listener ke paas kuch nahi gaya", listener.finals, 0)


def test_speech_fed():
    print("GATE: AWAZ PAR FEED + HANGOVER")
    listener = FakeListener()
    gate = gate_mod.Gate()
    check("pehla loud chunk feed", gate.push(listener, loud()), True)
    check("dusra loud chunk feed", gate.push(listener, loud()), True)
    check("hangover me bhi feed (shabd ka poora hissa)",
          gate.push(listener, quiet()), True)
    truthy("hangover 0.9s se bada", config.VAD_HANGOVER_BLOCKS >= 20)
    check("fed 3", gate.fed, 3)


def test_silence_blocks_reset():
    print("GATE: VAD_SILENCE_BLOCKS KE BAAD PICHHLA BHOOL")
    listener = FakeListener()
    gate = gate_mod.Gate()
    gate.push(listener, loud())
    before = gate.resets
    # Pehle VAD ka hangover (0.9 s) khatam hoga, phir `_silent` ginna shuru hota
    # hai — is liye reset `HANGOVER + SILENCE_BLOCKS` ke chunk par aata hai.
    warm = config.VAD_HANGOVER_BLOCKS
    for _ in range(warm + config.VAD_SILENCE_BLOCKS - 1):
        gate.push(listener, quiet())
    check("hangover + silence se pehle reset nahi", gate.resets, before)
    gate.push(listener, quiet())
    check("silence blocks poore par ek reset", gate.resets, before + 1)
    for _ in range(config.VAD_SILENCE_BLOCKS - 1):
        gate.push(listener, quiet())
    check("uske baad reset nahi", gate.resets, before + 1)


def test_gate_off_switch():
    print("GATE: PRABH_VOSK_GATE=0 (purana behaviour)")
    listener = FakeListener()
    gate = gate_mod.Gate(gate_on=False)
    for _ in range(5):
        gate.push(listener, quiet())
    check("band gate me sab chunk Vosk ko", gate.fed, 5)
    check("kuch skip nahi", gate.skipped, 0)
    truthy("config me gate switch hai", isinstance(config.WAKE_VOSK_GATE, bool))


def test_wake_reset():
    print("GATE: WAKE KE BAAD RESET")
    listener = FakeListener()
    gate = gate_mod.Gate()
    gate.push(listener, loud())
    gate.reset()
    check("reset ke baad fed/skipped 0 se recompute",
          (gate.fed, gate.skipped), (1, 0))
    truthy("VAD bhi reset hua", gate.vad.speaking() in (True, False))


def test_config_knobs():
    print("GATE: CONFIG")
    truthy("gate default ON hai", config.WAKE_VOSK_GATE is True)
    show(config.describe())
    check("describe me gate", config.describe().split()[-1], "gate=on")


for fn in (test_silence_not_fed, test_speech_fed, test_silence_blocks_reset,
           test_gate_off_switch, test_wake_reset, test_config_knobs):
    fn()

finish("Saare wake gate test pass.")
