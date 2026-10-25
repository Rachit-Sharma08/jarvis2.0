"""Test ka apna LOG — asli `logs/prabh.log` me test **kabhi** na likhe.

**Kaunsi galti thi:** `logs/prabh.log` ek hi file hai — app aur dono ek jaisa
likhte hain. Test suite chalti to usme bhi entries aa jaati hain (`wake_command
| user pehle se bol raha hai (rms=0.129)` waghera). S-1 audit me isi wajah se
mic ka asli level galat nikaala gaya tha: `tests/wakehelp.py` ka `loud()` **exactly
0.129** deta hai, aur wo number log me bhi aa raha tha.

**Raasta:** `config.py` ka `LOG_DIR` `JARVIS_LOG_DIR` env se aata hai. Ye file
`os.environ` **import ke time** set karti hai — is liye har test file me `import
config` se **pehle** `from tests import logsafe` honi chahiye (yahi import
`config` ko trigger karta hai).

Ye file jaan-boojh kar `config` **import nahi** karti — warna env set karne se
pehle hi `config.LOG_FILE` ban jayega aur poora kaam bekaar.

Test me use: `logsafe.clear()` ek test ke shuru me log saaf kar deta hai.
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

# Repo root — `tests/` namespace package se khud ban jata hai, par path saaf
# rakhne ke liye yahin daal dete hain (kuch test `tests.x` ki tarah import karte
# hain aur unhe root chahiye).
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_DIR = Path(tempfile.gettempdir()) / "prabh-test-logs"

# `config` se pehle set hona zaroori hai — `config.LOG_FILE` module load par hi
# pakda jaata hai.
os.environ["JARVIS_LOG_DIR"] = str(LOG_DIR)


def clear() -> None:
    """Test log saaf karo (assert me file ka content dekhna ho to)."""
    try:
        shutil.rmtree(LOG_DIR, ignore_errors=True)
    finally:
        LOG_DIR.mkdir(parents=True, exist_ok=True)


def path() -> Path:
    """Test ka log file (`config.LOG_FILE` se wahi path)."""
    import config                      # noqa: PLC0415 - yahin hi jaan-boojh kar
    return config.LOG_FILE             # config load hona chahiye


def read() -> str:
    """Ab tak likha hua poora test log (khali string agar kuch nahi)."""
    try:
        return path().read_text(encoding="ascii", errors="replace")
    except OSError:
        return ""
