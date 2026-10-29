"""Reminders + Timers (local JSON). Natural: 'remind me at 5 PM to call X'."""
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import config

DATA_DIR = Path(config.BASE_DIR) / 'data'
RFILE = DATA_DIR / 'reminders.json'


def _now():
    return datetime.now()


def _load():
    try:
        if RFILE.exists():
            with open(RFILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        pass
    return []


def _save(items):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(RFILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _fmt(dt):
    return dt.strftime('%Y-%m-%d %H:%M')


def add_reminder(text: str = "", at: str = "", in_minutes: int | None = None) -> str:
    items = _load()
    when = None
    n = _now()
    if in_minutes:
        try:
            m = int(in_minutes)
        except Exception:
            m = 0
        when = n + timedelta(minutes=m)
    elif at:
        s = at.strip()
        for fmt in ('%H:%M', '%I:%M %p', '%I:%M%p'):
            try:
                t = datetime.strptime(s, fmt)
                when = n.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                if when < n:
                    when += timedelta(days=1)
                break
            except Exception:
                pass
    if not when:
        return 'Samajh nahi aaya (example: "remind me in 5 minutes to call home" ya "remind me at 5 PM to water plants")'
    nid = max((x.get('id', 0) for x in items), default=0) + 1
    items.append({'id': nid, 'text': text or 'Reminder', 'when': when.isoformat(), 'done': False})
    _save(items)
    return f'Reminder set #{nid}: "{text or "Reminder"}" at {_fmt(when)}'


def list_reminders() -> str:
    items = [x for x in _load() if not x.get('done')]
    if not items:
        return 'Koi pending reminder nahi hai'
    lines = ['Pending reminders:']
    for x in items:
        try:
            w = datetime.fromisoformat(x['when'])
            lines.append(f"#{x['id']}: {x['text']} — {_fmt(w)}")
        except Exception:
            lines.append(f"#{x['id']}: {x['text']}")
    return '\n'.join(lines)


def clear_reminder(id: int | None = None) -> str:
    items = _load()
    if id:
        nid = int(id)
        items = [x for x in items if x['id'] != nid]
        _save(items)
        return f'Reminder #{nid} cleared'
    items = [x for x in items if x.get('done')]
    _save(items)
    return 'All pending reminders cleared? (use id to clear one)'


def due():
    """Abhi bajne wale reminders — `when` nikal chuka aur `done` nahi."""
    now = _now()
    out = []
    for x in _load():
        if x.get('done'):
            continue
        try:
            if datetime.fromisoformat(x['when']) <= now:
                out.append(x)
        except Exception:
            continue
    return out


def mark_done(ids) -> int:
    """In ids ko done karo. -> kitne badle (app ek hi reminder do baar na bole)."""
    want = {int(i) for i in ids or []}
    if not want:
        return 0
    items = _load()
    n = 0
    for x in items:
        if x.get('id') in want and not x.get('done'):
            x['done'] = True
            n += 1
    if n:
        _save(items)
    return n
