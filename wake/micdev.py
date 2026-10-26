"""Mic device ka faisla — kaun sa host API, exclusive chahiye ya nahi.

`wake/audio.py` ka loop yahan se sirf jawab leta hai; asli capture wahan hai.
Alag file is liye ki ye hissa **probe** hai (sounddevice + numpy) aur audio.py
200 line cross kar raha tha.

**Kyun exclusive:** is PC par Realtek ka AEC/denoise shared mode me mic ko daba
deta hai — 0.9 amplitude ke tone ka peak **shared 0.0049 vs exclusive 0.0486**
(10x). Exclusive APO bypass karta hai, par mic doosri apps (Teams/Zoom) se lock
ho sakta hai — is liye default `auto` hai: sirf tab exclusive jab shared
bilkul dead ho.
"""

import time

import numpy as np

import config
from log_setup import get_logger

log = get_logger("wake_audio")

BLOCK_SECONDS = config.BLOCK_MS / 1000.0
GATE_FLOOR = 0.00005        # is se neeche = digital silence (APO gate)


def hostapi_name(sd, device) -> str:
    """Log ke liye: device kis host API ka hai (`MME`/`WASAPI`/...)."""
    try:
        info = sd.query_devices(device, kind="input")
        return str(sd.query_hostapis(info["hostapi"])["name"])
    except Exception:
        return "?"


def native_rate(sd, device) -> int:
    """Device ka apna capture rate. WASAPI 48 kHz maangta hai — 16 kHz par
    PortAudio `Invalid sample rate` deta hai (5-Oct)."""
    try:
        info = sd.query_devices(device, kind="input")
        return int(info["default_samplerate"]) or config.SAMPLE_RATE
    except Exception:
        return config.SAMPLE_RATE


def wasapi_extra(sd, device):
    """`JARVIS_MIC_EXCLUSIVE`: shared (0) | exclusive (1) | auto.

    `auto` device ka floor sun kar dekhta hai: digital silence (p10 < 0.00005)
    matlab Windows ka APO/denoise use daba raha hai — tab exclusive par jao,
    jo APO bypass karta hai. Healthy mic par shared hi rehta hai, taaki mic
    doosri apps (Teams/Zoom) ke saath share hota rahe.
    """
    mode = config.MIC_EXCLUSIVE
    if mode in ("0", "off", "false", "no", "shared", ""):
        return None
    try:
        if "WASAPI" not in hostapi_name(sd, device).upper():
            return None
        settings = sd.WasapiSettings(exclusive=True)
    except Exception as exc:
        log.warning("exclusive mic setting nahi bani: %s", exc)
        return None
    if mode in ("1", "on", "true", "yes", "exclusive"):
        return settings
    return None if floor(sd, device) >= GATE_FLOOR else settings


def floor(sd, device, seconds: float = 0.8) -> float:
    """Device ka noise floor (p10 RMS). Digital silence = APO gate.

    p90 nahi: 0.8 s me ek-do spike (chair, notification) p90 ko threshold ke
    upar khinch deta tha, aur mic galti se shared par chala jaata tha — phir
    AEC speaker ki awaaz cancel kar deta (peak 0.003 vs 0.049). Ab **p10**:
    gated mic ke 90% window digital silence hote hain (0.0), healthy mic ke
    saare window floor par — spikes se faisla nahi badalta. Shuru ke 150 ms
    chhodte hain (device khulte waqt pop).
    """
    rate = native_rate(sd, device)
    buf = []

    def callback(indata, frames, time_info, status):
        buf.append(indata[:, 0].copy())

    try:
        stream = sd.InputStream(samplerate=rate, channels=1, device=device,
                                dtype="float32", callback=callback, blocksize=0)
        stream.start()
        time.sleep(seconds)
        stream.stop()
        stream.close()
    except Exception as exc:
        log.warning("mic floor probe fail: %s", exc)
        return 1.0
    if not buf:
        return 1.0
    data = np.concatenate(buf)
    data = data[np.isfinite(data)]
    data = data[int(rate * 0.15):]
    win = max(1, int(rate * BLOCK_SECONDS))
    count = data.size // win
    if count < 1:
        return 1.0
    rms = np.sqrt(np.mean(data[:count * win].reshape(count, win) ** 2, axis=1))
    return float(np.percentile(rms, 10))
