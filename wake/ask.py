"""Wake ke baad brain se jawab — `wake/command.py` ka brain wala hissa.

`wake/listen.py` mic ka kaam karta hai (drain/warmup/capture/STT); is file me
wo hai jo **uske baad** hota hai. Do wajah se alag:

1. `command.py` 200 lines cross kar raha tha (Step 2c ke baad), aur brain ka
   hissa mic se alag concern hai.
2. Test me brain wala part alag se fake hota hai — `tests/wakecmdhelp.py` ka
   `ask_brain` wala fake.

**Gatekeeper yahan nahi hai.** Tool sirf `ENGINE.handle()` ke andar chalta hai;
`keeper.approve()` is file me nahi hai, is liye awaaz se ALLOW ka koi raasta
nahi banta (test **AST** se check karta hai). ASK card aaye to sirf HUD khulkar
"Screen par confirm kijiye" bolte hain — faisla screen ke button ka hai.

Har event par `via="voice"` lagta hai: `ui/app.js` us par browser TTS nahi
chalata, warna jawab do baar bolta. Typed message ka raasta badalta nahi.
"""

import config
from gatekeeper.audit import mask
from log_setup import get_logger
from server.hub import HUB

log = get_logger("wake_ask")


def _safe(callback, *args) -> None:
    """Callback ka crash hamara crash nahi hai (HUD open, busy pill...)."""
    if callback is None:
        return
    try:
        callback(*args)
    except Exception as exc:
        log.warning("callback crash: %s: %s", type(exc).__name__, exc)


def speak(text: str, stop=None) -> int:
    """Text bol kar suno. -> kitni der lagi (ms); `0` matlab nahi bola.

    Speaker ka ek hi raasta `desktop/playback.py` — yahan koi naya `sd.play`
    nahi, koi TTS provider chuna nahi jaata. Time alag se: `voice/tts.py` apna
    `TIME tts: ... Nms` aur `playback` apna `speaker: Nms` log me likhta hai."""
    from desktop import playback

    from wake import listen

    stop = stop or listen._STOP
    if stop.is_set():
        return 0
    return playback.say(text)


def ask(text: str, rid: str, on_confirm=None, stop=None) -> tuple:
    """Shared ENGINE se jawab. -> `(answer, card_aaya, brain_fail)`.

    `brain_fail` = engine ka log event jis me `data.brain == "none"` (saare
    provider fail, ya brain crash). Us message me **saare technical reasons**
    hote hain - HUD par theek hai, par awaaz me padhne layak nahi; is liye
    caller `config.BRAIN_FAILED` bolta hai."""
    from server.state import engine as shared_engine
    from wake import listen

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