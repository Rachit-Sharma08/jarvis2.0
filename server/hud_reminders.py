"""Upcoming reminders for HUD badge."""
from datetime import datetime

from server.hub import HUB
from tools import reminders


def _fmt(dt):
    try:
        return dt.strftime('%H:%M')
    except Exception:
        return ''


def due_soon(max_minutes: int = 5):
    try:
        items = reminders._load()
    except Exception:
        items = []
    now = datetime.now()
    soon = []
    for x in items:
        if x.get('done'):
            continue
        try:
            w = datetime.fromisoformat(x['when'])
        except Exception:
            continue
        if w <= now:                     # nikal gaya - HUD par overdue (m=0)
            soon.append({'id': x['id'], 'text': x['text'], 'when': _fmt(w), 'm': 0})
            continue
        delta = (w - now).total_seconds() / 60.0
        if delta <= max_minutes:
            soon.append({'id': x['id'], 'text': x['text'], 'when': _fmt(w), 'm': int(delta + 0.5)})
    soon.sort(key=lambda e: e['m'])
    return soon[:3]


def broadcast():
    try:
        data = {'count': len(due_soon()), 'items': due_soon()}
        HUB.publish({'type': 'reminders', 'data': data})
    except Exception:
        pass
