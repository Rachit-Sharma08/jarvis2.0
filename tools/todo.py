"""Simple To-Do list (local JSON)."""
import json
from pathlib import Path

import config

DATA_DIR = Path(config.BASE_DIR) / 'data'
TFILE = DATA_DIR / 'todos.json'


def _load():
    try:
        if TFILE.exists():
            with open(TFILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        pass
    return []


def _save(items):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(TFILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_todo(text: str = "") -> str:
    if not text or not text.strip():
        return 'Todo text kya hai? (example: "add buy milk to todo")'
    items = _load()
    items.append({'id': len(items) + 1, 'text': text.strip(), 'done': False})
    _save(items)
    return f'Todo added #{len(items)}: {text.strip()}'


def list_todos() -> str:
    items = _load()
    if not items:
        return 'Koi todo nahi hai'
    lines = ['Todos:']
    for x in items:
        mark = '✓' if x.get('done') else '•'
        lines.append(f"{mark} #{x['id']}: {x['text']}")
    return '\n'.join(lines)


def done_todo(id: int | None = None) -> str:
    if id is None:
        return 'Kaunsa todo mark karun? (id do, jaise done_todo id=1)'
    items = _load()
    nid = int(id)
    for x in items:
        if x['id'] == nid:
            x['done'] = True
            _save(items)
            return f'Todo #{nid} done: {x["text"]}'
    return f'Todo #{nid} nahi mila'


def clear_todos() -> str:
    _save([])
    return 'Todos saare clear ho gaye'
