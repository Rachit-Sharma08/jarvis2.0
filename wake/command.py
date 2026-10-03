"""Wake ke baad ka poora command — "Ji, boliye" se le kar jawab ki awaaz tak.

Ye Phase 5 **Step 2c** hai. Step 2a (`wake/utterance.py`) ne mic se audio
uthaya, Step 2b (`desktop/playback.py`) ne awaaz banayi — is file me dono ko
ek flow me jod diya gaya hai:

    wake -> "Ji, boliye" -> mic drain + warm-up -> capture (VAD)
         -> WAV -> Groq STT (guard) -> shared ENGINE -> Hub/UI events
         -> jawab ki awaaz

Char zaroori baatein:

1. **Wake word poori tarah local hai** (Vosk, 100% offline). Sirf command ki
   recording, memory me bante hi, Groq ke STT par network par jaati hai —
   **disk par kabhi save nahi hoti**, koi file likhi jaati hi nahi.
2. Ye `wake/session.py` ke `_fire()` se **wake thread par, synchronous** chalta
   hai. Is liye poore flow me sunna ruka rehta hai aur "Jarvis" dobara trigger
   nahi hota. TTS ke waqt mic `worker.hold_for_command()` se band rehta hai —
   warna apni hi awaaz sun kar phir uth jaata.
3. **Gatekeeper bilkul waisa hi hai.** Is file me approve/deny ka koi raasta
   nahi — tool sirf `ENGINE.handle()` ke andar chalta hai. ALLOW hamesha screen
   ke button se hota hai, awaaz se kabhi nahi. ASK card aaye to sirf HUD khol
   kar "Screen par confirm kijiye" bolte hain.
4. **Mute ya PC lock par kuch nahi hota** — na record, na awaaz. Faisla
   `allowed()` callback deta hai (`desktop/callbacks.py` bhejta hai), taaki
   `wake/` ko `desktop/` ka import na karna pade.

Har stage ka time `core/timing.py` ke `Stopwatch` se ek line me log hota hai:
`TIME wake_command: TOTAL | ack=.. warmup=.. capture=.. stt=.. brain=.. speak=..`

Mic ke chaar kaam (`drain`/`warmup`/`capture`/`to_text`) `wake/listen.py` me
hain — yahan sirf flow aur brain/speaker ka faisla hai.
"""

import time

import config
from core.timing import Stopwatch
from gatekeeper.audit import mask
from log_setup import get_logger
from server.hub import HUB
from wake import listen

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


def ask_brain(text: str, rid: str, on_confirm=None, stop=None) -> tuple:
    """Shared ENGINE se jawab. -> `(answer, card_aaya, brain_fail)`.

    Engine ke event seedhe `HUB` par jaate hain (browser wahi HUD hai). Har event
    me `via="voice"` lagta hai: `ui/app.js` us par browser TTS nahi chalata,
    warna jawab do baar bolta. Typed message ka raasta badalta nahi.

    `keeper.approve()` yahan nahi hai - card sirf dikhta hai, ALLOW ka button
    screen par hai aur `engine` us par wait karta hai.

    `brain_fail` = engine ka log event jis me `data.brain == "none"` (saare provider
    fail, ya brain crash). Us message me **saare technical reasons** hote hain -
    HUD par theek hai, par awaaz me padhne layak nahi; is liye caller
    `config.BRAIN_FAILED` bolta hai."""
    from server.state import engine as shared_engine

    stop = stop or listen._STOP
    answer, asked, failed = "", False, False
    for event in shared_engine().handle(text, rid):
        event["via"] = "voice"
        HUB.publish(event)
        kind = event.get("type")
        if kind == "message" and event.get("role") == "assistant":
            answer = mask(event.get("text", ""))
        elif kind == "confirm":
            asked = True
            log.info("ASK card aaya: %s (awaaz se allow nahi hoga)", event.get("tool"))
            _safe(on_confirm)
            # Yahi bolna zaroori hai: agli iteration par engine `keeper.wait()`
            # par **ruk jaata hai** (60 s). Bolna yahan chhod diya to user ko
            # card dikhega par awaaze se koi raasta nahi bataya jayega.
            speak(config.CONFIRM_VOICE, stop)
        elif kind == "log" and (event.get("data") or {}).get("brain") == "none":
            failed = True
        if stop.is_set():
            log.info("brain beech me ruka (app band ho raha hai)")
            break
    return answer, asked, failed


def speak(text: str, stop=None) -> int:
    """Text bol kar suno. -> kitni der lagi (ms); `0` matlab nahi bola.

    Speaker ka ek hi raasta `desktop/playback.py` — yahan koi naya `sd.play`
    nahi, koi TTS provider chuna nahi jaata. Time alag se: `voice/tts.py` apna
    `TIME tts: ... Nms` aur `playback` apna `speaker: Nms` log me likhta hai."""
    from desktop import playback

    stop = stop or listen._STOP
    if stop.is_set():
        return 0
    return playback.say(text)


def run(mic=None, stop=None, allowed=None, on_confirm=None, on_busy=None) -> str:
    """Wake ke baad ka poora command. -> kya hua (log + test ke liye).

    `mic` aur `stop` `wake/session.py` ke `_fire()` se aate hain — kahin aur se
    mic nahi milta (mic ka ek hi owner `wake/audio.py` hai). Baaki teen callback
    `desktop/callbacks.py` deta hai: `allowed` (mute/lock), `on_confirm` (HUD
    kholo) aur `on_busy` (HUD ka WAKE pill)."""
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
        # 1. "Ji, boliye" — mic hold ho chuka hai, to apni awaaz capture nahi hogi.
        at = stage()
        speak(config.ACK_ON_WAKE, stop)
        watch.stage("ack", at)

        # 2. Purana audio phenko + mic baithne do, phir suno.
        at = stage()
        listen.drain(mic, stop)
        listen.warmup(mic, stop)
        watch.stage("warmup", at)

        # 3. VAD se command uthao. Kuch suna hi nahi -> dobara boliye.
        at = stage()
        chunks = listen.capture(mic, stop)
        if not chunks:
            speak(config.NOT_UNDERSTOOD, stop)
            return "not-heard"
        watch.stage("capture", at)

        # 4. WAV + Groq STT (wahi guard jo browser wale raaste par chalta hai).
        at = stage()
        text = listen.to_text(chunks, stop)
        if not text:
            speak(config.NOT_UNDERSTOOD, stop)
            return "no-text"
        watch.stage("stt", at)

        # 5. Shared ENGINE — wahi object jo /chat aur /hud/quick use karte hain.
        at = stage()
        answer, asked, failed = ask_brain(
            text, "voice%d" % int(time.time() * 1000), on_confirm, stop)
        watch.stage("brain", at)

        # 6. Jawab ki awaaz. (ASK card ki "confirm kijiye" `ask_brain` ne andar
        #    bol di — yahan sirf brain ka jawab.)
        at = stage()
        speak(config.BRAIN_FAILED if failed else (answer or config.BRAIN_FAILED),
              stop)
        watch.stage("speak", at)
        return "asked" if asked else "ok"
    finally:
        # TTS ka shor queue me pada hai — phenk do, warna `Session._loop` use
        # wake shabd samajh kar dobara trigger kar dega.
        listen.drain(mic, stop)
        if held:
            wake_worker.release_from_command()
        _safe(on_busy, False)
        HUB.publish({"type": "status", "value": "idle"})
        watch.total()