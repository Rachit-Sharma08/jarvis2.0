"""Wake ke baad ka poora command â€” "Ji, boliye" se le kar jawab ki awaaz tak.

Ye Phase 5 **Step 2c** hai. Step 2a (`wake/utterance.py`) ne mic se audio
uthaya, Step 2b (`desktop/playback.py`) ne awaaz banayi â€” is file me dono ko
ek flow me jod diya gaya hai:

    wake -> mic drain + 0.18 s peek -> ("Ji, boliye" | pehle se bol raha hai)
         -> warm-up -> capture (VAD) -> WAV -> Groq STT (guard)
         -> shared ENGINE -> Hub/UI events -> jawab ki chhoti awaaz

Char zaroori baatein:

1. **Wake word poori tarah local hai** (Vosk, 100% offline). Sirf command ki
   recording, memory me bante hi, Groq ke STT par network par jaati hai â€”
   **disk par kabhi save nahi hoti**, koi file likhi jaati hi nahi.
2. Ye `wake/session.py` ke `_fire()` se **wake thread par, synchronous** chalta
   hai. Is liye poore flow me sunna ruka rehta hai aur "Jarvis" dobara trigger
   nahi hota. TTS ke waqt mic `worker.hold_for_command()` se band rehta hai â€”
   warna apni hi awaaz sun kar phir uth jaata.
3. **Gatekeeper bilkul waisa hi hai.** Is file me approve/deny ka koi raasta
   nahi â€” tool sirf `ENGINE.handle()` ke andar chalta hai. ALLOW hamesha screen
   ke button se hota hai, awaaz se kabhi nahi. ASK card aaye to sirf HUD khol
   kar "Screen par confirm kijiye" bolte hain.
4. **Mute ya PC lock par kuch nahi hota** â€” na record, na awaaz. Faisla
   `allowed()` callback deta hai (`desktop/callbacks.py` bhejta hai), taaki
   `wake/` ko `desktop/` ka import na karna pade.

Har stage ka time `core/timing.py` ke `Stopwatch` se ek line me log hota hai:
`TIME wake_command: TOTAL | ack=.. warmup=.. capture=.. stt=.. brain=.. speak=..`

Mic ke chaar kaam (`drain`/`warmup`/`capture`/`to_text`) `wake/listen.py` me
aur brain/speaker ka kaam `wake/ask.py` me hai â€” yahan sirf **flow** hai, is liye
do files me se kabhi brain ka raasta dobara mat likhna.
"""

import time
import random

import config
from core.timing import Stopwatch
from log_setup import get_logger
from server.hub import HUB
from voice import tts
from wake import ask
from wake import listen
from wake import phrase as phrase_mod

log = get_logger("wake_command")


def _safe(callback, *args) -> None:
    """Callback ka crash hamara crash nahi hai (HUD open, busy pill...)."""
    if callback is None:
        return
    try:
        callback(*args)
    except Exception as exc:
        log.warning("callback crash: %s: %s", type(exc).__name__, exc)


def _allowed(allowed) -> tuple:
    """`allowed()` se faisla. Default (koi callback nahi) = sab theek."""
    if allowed is None:
        return True, ""
    try:
        ok, reason = allowed()
    except Exception as exc:
        log.error("allowed() crash: %s: %s", type(exc).__name__, exc)
        return False, "guard crash"
    return bool(ok), str(reason or "")


def _is_sleep(text: str) -> bool:
    """'So jao' hai kya? Yahi guard `desktop/sleep.py` me hai â€” `wake/` ko
    `desktop/` ka import nahi karwana (`tests/test_desktop_sleep.py` dono check
    karta hai, taaki dono alag na ho jaayein)."""
    low = (text or "").strip().lower()
    if not low or len(low.split()) > 4:
        return False
    return any(word in low for word in config.SLEEP_WORDS)


def run(mic=None, stop=None, allowed=None, on_confirm=None, on_busy=None,
        on_sleep=None) -> str:
    """Wake ke baad ka poora command. -> kya hua (log + test ke liye).

    `mic` aur `stop` `wake/session.py` ke `_fire()` se aate hain â€” kahin aur se
    mic nahi milta (mic ka ek hi owner `wake/audio.py` hai). Baaki chaar callback
    `desktop/callbacks.py` deta hai: `allowed` (mute/lock), `on_confirm` (HUD
    kholo), `on_busy` (HUD ka WAKE pill) aur `on_sleep` ("so jao" â€” battery)."""
    from wake import worker as wake_worker

    stop = stop or listen._STOP
    ok, reason = _allowed(allowed)
    if not ok:
        log.info("command nahi chala: %s", reason)
        return "blocked"
    if mic is None or not getattr(mic, "alive", False):
        log.warning("command chhuda: mic nahi hai")
        return "no-mic"

    watch = Stopwatch("wake_command")
    stage = time.perf_counter
    held = wake_worker.hold_for_command()
    _safe(on_busy, True)
    HUB.publish({"type": "status", "value": "listening"})
    try:
        # 1. Purana audio phenko (wake shabd ki goonj + pichli TTS), phir 0.18 s
        #    suno â€” kya user bol hi raha hai? Agar haan to "Ji, boliye" **nahi**
        #    bolte (pehle hamari awaaz uske upar chadh jaati thi), aur usi chhote
        #    intezaar ne mic ka kaam bhi kar diya. Nahi to normal raasta: ack +
        #    1 s warm-up, jiska waqt `settled_by` se overlap hota hai.
        at = stage()
        listen.drain(mic, stop)
        talking, peak = listen.peek_speech(mic, stop)
        if talking:
            # **Ek saans wala command**: ack/beep dono nahi, warmup/drain bhi
            # nahi - queue me jo audio hai wahi capture chalta hai.
            log.info("user pehle se bol raha hai (rms=%.3f) - ack skip", peak)
            watch.stage("ack", at)
            watch.stage("warmup", at)
        elif config.ACK_BEEP:
            # Beep (12-Oct): ~5 s ki "Ji, boliye" + 1 s warmup ki jagah. Beep ka
            # audio `drop_seconds` phenkta hai, phir capture turant shuru.
            from desktop import playback

            playback.beep()
            watch.stage("ack", at)
            at = stage()
            listen.drop_seconds(mic, stop, config.ACK_BEEP_DROP_SECONDS)
            watch.stage("warmup", at)
        else:
            ack = random.choice(config.ACK_ON_WAKE) if hasattr(config.ACK_ON_WAKE, "__iter__") and not isinstance(config.ACK_ON_WAKE, str) else config.ACK_ON_WAKE
            ask.speak(ack, stop)
            watch.stage("ack", at)
            # 2. Mic baithne do, phir queue khaali karo. Jitna warm-up ack me
            #    poora ho chuka hai utna hi wait â€” pehle har baar 1 s dead tha.
            at = stage()
            settled_by = stage() + float(config.COMMAND_WARMUP_SECONDS)
            listen.warmup(mic, stop, deadline=settled_by)
            watch.stage("warmup", at)

        # 3. VAD se command uthao. Kuch suna hi nahi -> dobara boliye.
        at = stage()
        chunks = listen.capture(mic, stop)
        if not chunks:
            ask.speak(config.NOT_UNDERSTOOD, stop)
            return "not-heard"
        watch.stage("capture", at)

        # 4. WAV + Groq STT (wahi guard jo browser wale raaste par chalta hai).
        # `strip_wake`: ek saans wale command me STT "jarvis" bhi suna deta hai.
        # Khaali (ya sirf "jarvis") text par brain **bilkul nahi** chalta.
        at = stage()
        text = phrase_mod.strip_wake(listen.to_text(chunks, stop))
        if not text:
            ask.speak(config.NOT_UNDERSTOOD, stop)
            return "no-text"
        watch.stage("stt", at)

        # 4b. "So jao" â€” battery. Brain nahi, tool nahi: sirf haalat badal do.
        # Text chhota hona zaroori hai (`desktop/sleep.py` ka guard), warna
        # "band ho jao kya matlab hai" jaisa vaakya galti se so jaa dega.
        if config.SLEEP_WORDS and _is_sleep(text):
            ask.speak(config.SLEEP_ACK, stop)
            _safe(on_sleep)
            watch.stage("speak", at)
            return "sleep"

        # 5. Shared ENGINE â€” wahi object jo /chat aur /hud/quick use karte hain.
        at = stage()
        answer, asked, failed = ask.ask(
            text, "voice%d" % int(time.time() * 1000), on_confirm, stop)
        watch.stage("brain", at)

        # 6. Jawab ki awaaz. (ASK card ki "confirm kijiye" `ask.ask` ne andar
        #    bol di â€” yahan sirf brain ka jawab.) Awaaz **chhoti** boli jaati
        #    hai: HUD par poora jawab dikhta hi hai, par 500 char bolne me 4.3 s
        #    lagta tha sirf playback me â€” is liye user ko "late" lagta tha.
        at = stage()
        # `voice_answer()` pehle 1-2 **poore** vaakya leta hai (KAAM 4); pehle
        # `clip_answer()` 220 char par beech se kaat raha tha. HUD par poora
        # jawab waise hi rehta hai - sirf awaaz chhoti.
        spoken = config.BRAIN_FAILED if failed else (
            tts.voice_answer(answer) or config.BRAIN_FAILED)
        ask.speak(spoken, stop)
        watch.stage("speak", at)
        return "asked" if asked else "ok"
    finally:
        # TTS ka shor queue me pada hai â€” phenk do, warna `Session._loop` use
        # wake shabd samajh kar dobara trigger kar dega.
        listen.drain(mic, stop)
        if held:
            wake_worker.release_from_command()
        # Jawab ke baad follow-up window (KAAM 5, **DEFAULT OFF**). Release ke
        # BAAD — warna KAAM 2 ka tail guard nahi lage aur apni awaaz follow-up ban jaati.
        wake_worker.mark_hot()
        _safe(on_busy, False)
        HUB.publish({"type": "status", "value": "idle"})
        watch.total()
