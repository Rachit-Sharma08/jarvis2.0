"""Phone (Android) control ke constants — Artemis CLI ka ghar.

Ye values `.env` se badli jaa sakti hain (naya key `config.py` me re-export
hota hai, is liye `config.ARTEMIS_DIR` bhi chalta hai).

`log_setup` yahan **import nahi** hota — wo `config` ko import karta hai aur
`config` isi file ko, is liye cyclic ho jaata (23-Oct ka rule).
"""

import os

# Artemis checkout (Google ka open-source Android agent). Isi folder me
# `uv run artemis run "<kaam>"` chalta hai.
ARTEMIS_DIR = os.getenv("JARVIS_ARTEMIS_DIR", "").strip() or r"D:\artemis"

# 'flash' = tez (5-10 step), 'pro' = poora graph (dheema, zyada pakka).
ARTEMIS_PROFILE = os.getenv("JARVIS_ARTEMIS_PROFILE", "").strip() or "flash"

# Ek phone kaam kitna lamba chal sakta hai. Artemis har step par screen
# dekhta hai (~3-5 s), is liye 20-40 step = 2-3 minute. Phone call bhi isi
# me aa jaata hai.
PHONE_TIMEOUT_SECONDS = int(os.getenv("JARVIS_PHONE_TIMEOUT", "") or 300)
