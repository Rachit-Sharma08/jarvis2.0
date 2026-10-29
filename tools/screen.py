"""Screen dekhkar jawab — ffmpeg screenshot + OpenRouter ka vision (VL) model.

User bole "screen par kya hai / is error ka matlab kya hai" to yahan se ek
screenshot jaata hai aur model usi ko dekh kar chhota Hinglish jawab deta hai.

**Privacy:** screenshot + sawaal internet (OpenRouter) par jaate hain. Is liye
har call par log me ek warning line likhi jaati hai, aur PNG disk par sirf kaam
ke dauraan rehti hai (uske baad turant delete). Screen par password/OTP khula
ho to ye tool mat chalao — `TOOLS.md` me ye baat likhi hai.

Koi naya package nahi: screenshot `ffmpeg` (winget wala build) se, HTTP
`urllib` se.
"""

import base64
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request

import config
import config_vision
from log_setup import get_logger

log = get_logger("tools.screen")

API = "https://openrouter.ai/api/v1/chat/completions"
# Model ko saaf hidayat: sirf jo dikh raha hai, chhota Hinglish jawab.
_PROMPT = ("Ye user ke PC ka screenshot hai. Sirf jo screen par DIKH raha hai "
           "usi ke aadhar par 2 line tak ka saaf Hinglish jawab do. Kuch padha "
           "na ja sake to bolo ki saaf nahi dikh raha - apni kalpana mat jodo.")
_MAX_CHARS = 400


def _grab(path: str):
    """Ek screenshot -> PNG file par. Test me yahi patch hota hai."""
    cmd = [config_vision.FFMPEG_EXE, "-y", "-loglevel", "error",
           "-f", "gdigrab", "-i", "desktop", "-frames:v", "1",
           "-vf", "scale=%d:-1" % config_vision.SCREEN_MAX_WIDTH, path]
    return subprocess.run(cmd, shell=False, capture_output=True, timeout=25)


def _post(body: dict, key: str) -> dict:
    """OpenRouter call. Test me yahi patch hota hai (network kabhi nahi)."""
    req = urllib.request.Request(
        API, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key,
                 "X-Title": config.DISPLAY_NAME})
    with urllib.request.urlopen(req, timeout=config_vision.SCREEN_TIMEOUT_SECONDS) as res:
        return json.loads(res.read().decode("utf-8", "replace"))


def _ask(image_b64: str, question: str) -> str:
    """Screenshot + sawaal -> model ka jawab (ek line)."""
    key = config.OPENROUTER_API_KEY
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY")
    text = _PROMPT + (("\nUser ka sawaal: " + question) if question else "")
    body = {
        "model": config_vision.SCREEN_MODEL,
        "max_tokens": 300,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {
                "url": "data:image/png;base64," + image_b64}},
        ]}],
    }
    data = _post(body, key)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("khaali jawab")
    return str((choices[0].get("message") or {}).get("content") or "")


def _one_line(text: str) -> str:
    return " ".join(str(text or "").split())[:_MAX_CHARS]


def screen_look(question: str = "") -> str:
    """Screen dekh kar jawab do. -> ek chhoti Hinglish line."""
    q = _one_line(question)
    log.warning("screen_look: screen ka screenshot OpenRouter (%s) par ja raha hai",
                config_vision.SCREEN_MODEL)
    path = os.path.join(tempfile.gettempdir(), "jarvis_screen.png")
    try:
        res = _grab(path)
    except FileNotFoundError:
        return "ffmpeg nahi mila — screen dekhne ka tool band hai."
    except subprocess.TimeoutExpired:
        return "Screenshot nahi ban paya (timeout)."
    if res.returncode != 0 or not os.path.isfile(path):
        return "Screenshot nahi bana (screen lock?)."
    try:
        with open(path, "rb") as fh:
            image_b64 = base64.b64encode(fh.read()).decode("ascii")
        answer = _one_line(_ask(image_b64, q))
    except RuntimeError as exc:
        if "OPENROUTER" in str(exc):
            return "Screen dekhne ke liye OpenRouter key chahiye (.env me daalo)."
        return "Model ne screen par kuch saaf nahi bataya."
    except urllib.error.HTTPError as exc:
        log.warning("screen_look http %s", exc.code)
        return "Screen dekhne wala model abhi jawab nahi de raha (HTTP %s)." % exc.code
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        log.warning("screen_look fail: %s", exc)
        return "Internet/model se baat nahi ho payi — dobara try karo."
    finally:
        try:
            os.remove(path)  # screenshot disk par na rahe
        except OSError:
            pass
    if not answer:
        return "Model ne screen par kuch saaf nahi bataya."
    return answer
