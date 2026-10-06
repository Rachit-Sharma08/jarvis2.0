"""Chat summarizer (local)."""
from pathlib import Path

import config

SUM_FILE = Path(config.BASE_DIR) / 'data' / 'memory_summary.txt'


def summarize_text(text: str = '') -> str:
    if not text or len(text) < 80:
        return text.strip() if text else ''
    lines = text.strip().splitlines()
    keep = [l.strip() for l in lines if l.strip()][:5]
    s = ' '.join(keep)[:200]
    return s


def save_summary(s: str) -> str:
    try:
        SUM_FILE.parent.mkdir(parents=True, exist_ok=True)
        SUM_FILE.write_text(s, encoding='utf-8')
        return 'summary saved'
    except Exception as exc:
        return f'err: {type(exc).__name__}'
