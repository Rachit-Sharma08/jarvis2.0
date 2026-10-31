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
from core import multitask
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


PREWARM_TEXTS = ("ACK_ON_WAKE", "CONFIRM_VOICE")


def _texts() -> list:
    """PREWARM_TEXTS ke asli lines — constant tuple ho to uske saare variants.

    `ACK_ON_WAKE` tuple hai (`random.choice` se ek chunta hai). Pehle poora
    tuple `speak_cached()` me jaata tha aur asli TTS `clean()` par
    `TypeError` deta tha — matlab ack kabhi cache nahi hota tha.
    """
    out = []
    for name in PREWARM_TEXTS:
        value = getattr(config, name, "")
        if isinstance(value, (list, tuple)):
            out.extend(str(v) for v in value if v)
        elif value:
            out.append(str(value))
    return out


def prewarm_async(mode: str = None) -> None:
    """`prewarm()` ko background thread me chalao - startup **rukna nahi** chahiye.

    Yehi app se call hota hai (`desktop/app.py: _start_wake`). Thread daemon hai,
    is liye app band karte waqt bhi atka nahi rehta."""
    import threading

    threading.Thread(target=prewarm, args=(mode,), name="prewarm",
                     daemon=True).start()


def prewarm(mode: str = None) -> int:
    """Startup par ack/confirm ka audio cache me bhar do - **awaaz nahi** bajti.

    4-Oct ke live log me pehla "Ji, boliye" ElevenLabs me **4239 ms** me bana,
    is liye pehli wake ka `ack` stage 5680 ms le gaya tha (poora jawab 18 s).
    Cache app restart par khaali hoti hai, is liye ye startup par — background
    thread me — bharna padta hai.

    Sirf `tts.speak_cached()` (cache wali), `playback.say()` **nahi** — warna
    startup par awaaz bajegi. Fail hua to chup-chaap: pehli baar me hi ban
    jayega, bas slow.

    -> kitne text cache me gaye.
    """
    import asyncio

    from voice import tts

    mode = mode or config.DEFAULT_MODE
    texts = _texts()
    if not texts:
        return 0

    async def run() -> int:
        done = 0
        for text in texts:
            try:
                await asyncio.wait_for(
                    tts.speak_cached(text, mode),
                    float(config.PLAYBACK_TIMEOUT_SECONDS),
                )
                done += 1
            except Exception as exc:
                log.info("prewarm skip: %s: %s", type(exc).__name__, exc)
        return done

    try:
        done = asyncio.run(run())
    except Exception as exc:
        log.info("prewarm nahi hua: %s: %s", type(exc).__name__, exc)
        return 0
    log.info("voice cache taiyar: %d/%d", done, len(texts))
    return done


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
    for event in multitask.run(shared_engine(), text, rid):
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