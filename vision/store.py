"""Owner ki face embedding ka ghar — `data/owner_face.npz`.

`data/` pehle se `.gitignore` me hai (git me kabhi nahi jaata), aur gatekeeper
ka BLOCKED list me bhi daala jayega (`.env` jaisa — koi tool ise na padh sake).

**Privacy ka pakka niyam:** embedding yahin rehti hai, teri PC par. Internet
par kahin nahi jaati, kisi provider ko nahi bhejti. Ye ek **binary** hai
(128 float), usme se photo **reconstruct nahi ki ja sakti** — sirf "ye chehra
is angle/roshni par in numbers ke kareeb tha" pata chalta hai.

Ye module **numpy** aur filesystem chhuta hai — koi camera nahi, koi CV package
nahi. Is liye `test_vision_store.py` ise tmp folder par poori tarah test kar
sakta hai, asli `data/` ko chhue bina.
"""

import json
import os
import tempfile
from pathlib import Path

import numpy as np

import config

FILE_NAME = "owner_face.npz"

# Sirf itni embedding rakhni hain. Zyada = purana data + battery par disk I/O.
MAX_SAMPLES = 12

# Har embedding ki lambai. Standard face model 128 deta hai (ArcFace/R50).
EXPECTED_DIM = 128


def path() -> Path:
    """Embedding file ka full path — `config.DATA_DIR` ke neeche."""
    return Path(config.DATA_DIR) / FILE_NAME


def _atomic_write(target: Path, arrays: dict) -> None:
    """Adhoora file na bache, warna enrollment ke baad crash par app
    khud ka owner hi bhool jaaye.

    `np.savez` ko ek file-object chahiye, is liye temp + `os.replace`. `os.replace`
    Windows par bhi atomic hai — yaani purani file ya nayi, beech ka koi haal
    nahi."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".npz")
    os.close(tmp_fd)
    try:
        with open(tmp_name, "wb") as fh:
            np.savez_compressed(fh, **arrays)
        os.replace(tmp_name, target)
    except Exception:
        Path(tmp_name).unlink(missing_ok=True)      # kuch bhi hua — safai
        raise


def save(samples, meta: dict = None) -> int:
    """Naye samples **jod** do (purane hataye bina). -> kitne save hue.

    Ye "jodta" hai kyun: har enrollment me purane samples rakhne se match
    behtar hota hai (alag roshni/angle). `MAX_SAMPLES` cross hone par **purane
    hataye jaate hain** (rolling window) — taaki disk par unbounded na badhe.
    """
    good = []
    for s in samples or []:
        arr = np.asarray(s, dtype=np.float32).reshape(-1)
        if arr.size == EXPECTED_DIM and np.linalg.norm(arr) > 1e-9:
            good.append(arr)
    if not good:
        return 0

    existing, _ = load()
    merged = (existing + good)[-MAX_SAMPLES:]
    stacked = np.stack(merged).astype(np.float32)
    info = {"count": len(merged), "dim": int(stacked.shape[1]),
            "extra": dict(meta or {})}
    _atomic_write(path(), {"samples": stacked,
                           "meta": np.array(json.dumps(info))})
    return len(merged)


def load() -> tuple:
    """(samples, meta) — file nahi ya kharab ho to `([], {})`.

    **Kharab file par crash nahi** — `UNKNOWN` milna behtar hai jaane se. Ye
    fail-safe ka hissa hai: store bigad to owner = unknown, owner "allow" nahi.
    """
    p = path()
    if not p.is_file():
        return [], {}
    try:
        with np.load(p, allow_pickle=False) as data:
            samples = np.asarray(data["samples"], dtype=np.float32)
            info = json.loads(str(data["meta"]))
    except Exception:
        return [], {}          # kharab/ purana format — chup-chaap khaali
    if samples.ndim != 2:
        return [], {}
    return [samples[i] for i in range(samples.shape[0])], info


def enrolled() -> bool:
    """Owner ka face ban chuka hai? (HUD ke pill + debug ke liye)"""
    samples, _ = load()
    return len(samples) > 0


def forget() -> bool:
    """Sab kuch mitao. -> kuch tha ya nahi (pata nahi chala to bhi True).

    Privacy: user ka haq hai ki apna data mita sake. Ye command
    (`PRABH_VISION` off hone par bhi) hamesha chalta rahega."""
    p = path()
    if p.is_file():
        try:
            p.unlink()
            return True
        except OSError:
            return False
    return True


def status() -> dict:
    """HUD/debug ke liye ek line — koi raw data nahi."""
    samples, info = load()
    return {"enrolled": bool(samples), "count": len(samples),
            "dim": int(info.get("dim", 0)),
            "when": str(info.get("extra", {}).get("when", ""))[:19]}