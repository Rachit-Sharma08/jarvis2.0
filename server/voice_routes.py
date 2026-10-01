from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

import config
from core.timing import Stopwatch
from log_setup import get_logger
from server import security
from voice import stt as stt_voice
from voice import tts as tts_voice

log = get_logger("voice_routes")
router = APIRouter()


class TtsIn(BaseModel):
    text: str
    mode: str = config.DEFAULT_MODE


def _guard(request: Request) -> None:
    denied = security.verify(
        request.headers.get("origin", ""),
        request.headers.get("host", ""),
        request.headers.get(security.TOKEN_HEADER, ""),
    )
    if denied:
        raise HTTPException(*denied)


@router.post("/stt")
async def stt(request: Request):
    _guard(request)

    size = request.headers.get("content-length")
    if size and int(size) > config.AUDIO_MAX_BYTES:
        raise HTTPException(413, "Recording bahut badi hai (max 10 MB).")

    audio = await request.body()
    if len(audio) > config.AUDIO_MAX_BYTES:
        raise HTTPException(413, "Recording bahut badi hai (max 10 MB).")
    if not audio:
        raise HTTPException(400, "Koi audio nahi mila.")

    # Browser recording ki asli length (ms) bhejta hai. Timer server par nahi —
    # wahan network latency jod kar galat value aati thi. 600ms se chhoti
    # recording STT tak jane se pehle hi rok di jaati hai.
    duration_ms = request.headers.get("x-audio-ms") or request.query_params.get("ms")

    watch = Stopwatch("route")
    try:
        text = await stt_voice.transcribe(audio, duration_ms=duration_ms)
    except stt_voice.SttError as exc:
        watch.total()
        raise HTTPException(502, str(exc)) from exc

    watch.total()
    return {"text": text}


@router.post("/tts")
async def tts(data: TtsIn, request: Request):
    _guard(request)

    if not data.text.strip():
        raise HTTPException(400, "Bolone layak text nahi hai.")

    watch = Stopwatch("route")
    try:
        audio, provider = await tts_voice.speak(data.text, data.mode)
    except tts_voice.TtsError as exc:
        watch.total()
        raise HTTPException(502, str(exc)) from exc

    log.info("tts %s -> %d bytes", provider, len(audio))
    watch.total()
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"x-tts-provider": provider},
    )