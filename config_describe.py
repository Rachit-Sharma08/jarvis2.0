"""`describe()` ki ek line - log aur `--wake-info` ke liye (config_wake se alag).

11-Oct (E-2): `config_wake.py` 200 lines cross kar gayi thi, is liye ye teen
faisle yahan aa gaye — `describe()`, `config_stt_name()` aur config_tools ke do
flag. config_tools ka flag **lazy** import hota hai: `config.py` yahan se
`config_wake` import karta hai, is liye module-level import cycle bana deta.
config_wake bhi isi file se re-export karta hai, is liye `config_wake.describe`
aur `config.describe` dono pehle jaise chalte hain.
"""

import config_env  # noqa: F401  (purane env naam pehle alias hote hain)
import os
from pathlib import Path


def _tools_flag(name: str) -> bool:
    """config_tools ka ek flag lazy pakdo ("cards" ya "direct")."""
    from config_tools import DIRECT_REPLY, NO_CARDS

    return {"cards": NO_CARDS, "direct": DIRECT_REPLY}[name]


def config_stt_name() -> str:
    """Command ke liye kaunsa STT - yahan `config_brain` se utha rahe hain taaki
    cycle na bane (`config.py` yahan se import karta hai, wahan se nahi)."""
    return os.getenv("JARVIS_STT_MODEL", "groq-whisper")


def describe() -> str:
    """Log + `--wake-info` ke liye ek line (aakhri field hamesha `hot=`)."""
    import config_wake as wake

    from config_hud import hud_theme

    folder = wake.model_path()
    # `hot=` 13-Oct (KAAM 5): follow-up window on hai ya nahi. `--wake-info` se
    # pata chalna zaroori hai, warna "follow-up nahi ho raha" ka pata hi nahi
    # chalega - flag to DEFAULT OFF hai.
    # `theme=` 14-Oct (KAAM B): neela ya arc - dono DEFAULT me band hote
    # hain, is liye yahan dekhna hi padta hai kaunsa chal raha hai.
    return ("wake=%s word=%s%s model=%s stt=%s direct=%s cards=%s gate=%s "
            "beep=%s hot=%s theme=%s") % (
        "ON" if wake.WAKE_ENABLED else "OFF",
        "/".join(wake.WAKE_WORDS),
        "+legacy" if wake.legacy_enabled() else "",
        Path(folder).name if folder else "MISSING",
        config_stt_name(),
        "on" if _tools_flag("direct") else "off",
        "off" if _tools_flag("cards") else "on",
        "on" if wake.WAKE_VOSK_GATE else "off",
        "on" if wake.ACK_BEEP else "off",
        ("on:%.0fs" % wake.HOT_WINDOW_SECONDS) if wake.HOT_WINDOW_ENABLED else "off",
        hud_theme(),
    )
