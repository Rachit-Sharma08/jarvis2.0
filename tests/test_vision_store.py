"""Embedding store ka test — `data/owner_face.npz`.

`store.py` sirf `numpy` + filesystem chhuta hai (camera nahi), is liye ye test
bina kisi CV package ke chalta hai.

**Asli `data/` ko chhua jaata hai kya?** Nahi. `tests/datasafe.py` ka
`isolated_data()` `config.DATA_DIR` ek **tmp** folder par le jaata hai aur
tearDown par wapas — plus asli par koi path gir gaya to `AssertionError`. Ye
niyam AGENTS ke E-1b ka hai: `store.py` jaan-boojh kar `config.DATA_DIR`
chhuta hai, is liye ye test **pehle se `isolated_data()` ke bina** likha nahi
jaa sakta.

Test inhe pin karta hai:
1. Round-trip — 128-float sample save + load, byte-level same.
2. **Jodta hai** (append), `MAX_SAMPLES` par rolling (purane katte hain).
3. **Galat size ka sample chhoot diya jaata hai** (128 ke alag) — warna ek
   bekaar sample saara match bigad dega.
4. **Kharab file par crash nahi** — `[]` milta hai (yaani owner = UNKNOWN,
   DENY). Ye fail-safe ka hissa hai.
5. `forget()` sach me mita deta hai (user ka haq).
"""

import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config
from tests.datasafe import isolated_data  # noqa: E402
from tests.pcmhelp import FAILED, check  # noqa: E402
from vision import identity, store  # noqa: E402

DIM = store.EXPECTED_DIM


def sample(seed=0.0, dim=DIM):
    """Deterministic valid embedding (128 float, zero nahi)."""
    return np.linspace(seed + 0.1, seed + 1.0, dim, dtype=np.float32)


def main():
    with isolated_data():
        # --- 1. round-trip ---
        check("pehle enrolled nahi", store.enrolled(), False)
        one = sample(1.0)
        saved = store.save([one], meta={"when": "2026-10-15"})
        check("ek sample save hua", saved, 1)
        check("enrolled ab True", store.enrolled(), True)
        back, info = store.load()
        check("ek wapas mila", len(back), 1)
        check("dim 128", info.get("dim"), DIM)
        check("value same", float(np.max(np.abs(back[0] - one))), 0.0)
        check("meta bacha", "when" in json.dumps(info), True)

        # --- 2. jodta hai, aur limit par rolling ---
        check("doosra joda (2)", store.save([sample(2.0)]), 2)
        back, _ = store.load()
        check("ab 2 samples", len(back), 2)
        for i in range(store.MAX_SAMPLES + 3):
            store.save([sample(10.0 + i)])
        back, info = store.load()
        check(f"limit {store.MAX_SAMPLES} par ruka", len(back), store.MAX_SAMPLES)
        check("count bhi match", info.get("count"), store.MAX_SAMPLES)

        # --- 3. galat size ka sample CHHOOT jaata hai ---
        before = len(store.load()[0])
        added = store.save([sample(1.0, dim=64), np.zeros(DIM, "float32")])
        check("galat size + zero vector reject", added, 0)
        check("purane intact", len(store.load()[0]), before)

        # --- 4. kharab file par crash nahi ---
        store.path().write_bytes(b"ye npz nahi hai, garbage")
        back, info = store.load()
        check("kharab file -> khaali", back, [])
        check("kharab file -> enrolled False", store.enrolled(), False)
        # Aur koi match nahi ho sakta — yaani DENY.
        check("kharab store par OWNER nahi",
              identity.allows(identity.decide(back, sample())["verdict"]), False)

        # --- 5. file sach me `config.DATA_DIR` ke andar banti hai ---
        store.save([sample(3.0)])
        check("file bani", store.path().is_file(), True)
        # Parent ka naam `"data"` NAHI hoga — `isolated_data()` `DATA_DIR` ko
        # tmp folder par point karwata hai. Asli pakkaura: file `config.DATA_DIR`
        # ke andar hi hai (yaani `data/` real app me, jo gitignored hai).
        check("DATA_DIR ke andar hai",
              str(store.path().parent) == str(Path(config.DATA_DIR)), True)
        check("asli data/ chhua nahi",
              str(config.BASE_DIR / "data") not in str(store.path()), True)

        # --- 6. forget() ---
        check("forget ne mita", store.forget(), True)
        check("ab enrolled nahi", store.enrolled(), False)
        check("dobara forget bhi safe", store.forget(), True)

        # --- 7. status me raw data nahi ---
        st = store.status()
        check("status dict hai", isinstance(st, dict), True)
        check("status me vector nahi",
              any(isinstance(v, (list, np.ndarray)) for v in st.values()), False)

    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        return 1
    print("face store (npz, tmp me) theek")
    return 0


if __name__ == "__main__":
    sys.exit(main())