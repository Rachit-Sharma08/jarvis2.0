from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

import config
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

    try:
        text = await stt_voice.transcribe(audio)
    except stt_voice.SttError as exc:
        raise HTTPException(502, str(exc)) from exc

    return {"text": text}


@router.post("/tts")
async def tts(data: TtsIn, request: Request):
    _guard(request)

    if not data.text.strip():
        raise HTTPException(400, "Bolone layak text nahi hai.")

    try:
        audio, provider = await tts_voice.speak(data.text, data.mode)
    except tts_voice.TtsError as exc:
        raise HTTPException(502, str(exc)) from exc

    log.info("tts %s -> %d bytes", provider, len(audio))
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"x-tts-provider": provider},
    )