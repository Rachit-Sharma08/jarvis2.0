import logging
import unicodedata

from config import LOG_DIR, LOG_FILE

# Unicode char -> ASCII. Ye pehle replace hote hain, baaki NFKD se fold hote hain.
_MAP = {
    "\u2014": "-", "\u2013": "-", "\u2192": "->", "\u2190": "<-", "\u2026": "...",
    "\u2022": "*", "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u00b0": " deg ", "\u00a0": " ",
}


def ascii_text(text) -> str:
    """Har text ko ASCII bana do.

    Kyun: Windows console `cp1252` hai. Log me Devanagari/arrow jaise char
    aate hain to wo `?`/`??` ban jaate hain — matlab crash ki asli baat hi
    kho jaati hai. Is liye log `logs/jarvis.log` hamesha ASCII rakhta hai.
    """
    if text is None:
        return ""
    out = str(text)
    for src, dst in _MAP.items():
        out = out.replace(src, dst)
    return unicodedata.normalize("NFKD", out).encode("ascii", "ignore").decode("ascii")


class AsciiFormatter(logging.Formatter):
    """Poora record (message + traceback) ASCII ho jaata hai."""

    def format(self, record: logging.LogRecord) -> str:
        return ascii_text(super().format(record))


def get_logger(name: str = "prabh") -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # encoding="ascii" + errors="replace" ek belt: koi bhi raasta se raw char
    # aa bhi jaaye to file me crash-y text nahi bikharenge.
    handler = logging.FileHandler(LOG_FILE, encoding="ascii", errors="replace")
    handler.setFormatter(
        AsciiFormatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger