"""Knowledge Base (RAG-lite, local TXT)."""
from pathlib import Path

import config

KB_DIR = Path(config.BASE_DIR) / 'data' / 'kb'


def _load_all():
    texts = []
    if KB_DIR.exists():
        for p in KB_DIR.glob('*.txt'):
            try:
                t = p.read_text(encoding='utf-8', errors='ignore')
                if t:
                    texts.append(t[:5000])
            except Exception:
                pass
    return texts


def kb_add(text: str = '', filename: str = 'note.txt') -> str:
    if not text or not str(text).strip():
        return 'Kya add karun KB me? (text do)'
    KB_DIR.mkdir(parents=True, exist_ok=True)
    name = (filename or 'note.txt').strip()
    if not name.endswith('.txt'):
        name += '.txt'
    p = KB_DIR / name
    try:
        p.write_text(str(text).strip(), encoding='utf-8')
        return f'KB save: {name}'
    except Exception as exc:
        return f'err: {type(exc).__name__}'


def kb_search(query: str = '') -> str:
    if not query or not str(query).strip():
        return 'Kya search karun KB me? (query do)'
    q = str(query).lower().strip()
    hits = []
    for t in _load_all():
        if q in t.lower():
            hits.append(t[:400])
    if not hits:
        return 'KB me kuch nahi mila'
    return '\n---\n'.join(hits[:3])
