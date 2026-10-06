"""Local notes."""
import json
from pathlib import Path

import config

DATA_DIR = Path(config.BASE_DIR) / 'data'
NFILE = DATA_DIR / 'notes.json'


def _load():
    try:
        if NFILE.exists():
            with open(NFILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        pass
    return []


def _save(items):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(NFILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def note_add(text: str = '', title: str = 'note') -> str:
    if not text or not str(text).strip():
        return 'Kya add karun?'
    items = _load()
    items.append({'id': len(items) + 1, 'title': str(title)[:20], 'text': str(text)[:500]})
    _save(items)
    return 'Note saved'


def note_list() -> str:
    items = _load()
    if not items:
        return 'Koi note nahi'
    return '\n'.join(f"#{x['id']}: {x['title']}" for x in items)


def note_search(query: str = '') -> str:
    if not query or not str(query).strip():
        return 'Query do'
    q = str(query).lower()
    items = _load()
    hits = [x for x in items if q in x['text'].lower() or q in x['title'].lower()]
    if not hits:
        return 'Kuch nahi mila'
    return '\n'.join(f"#{x['id']}: {x['text'][:100]}" for x in hits[:2])
