"""Simple Pomodoro timer state (local)."""
import json
from datetime import datetime, timedelta
from pathlib import Path

import config

DATA_DIR = Path(config.BASE_DIR) / 'data'
PFILE = DATA_DIR / 'pomodoro.json'


def _load():
    try:
        if PFILE.exists():
            with open(PFILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {'running': False, 'end': None, 'mode': 'work', 'mins': 25}


def _save(d):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(PFILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def pomodoro_start(mins: int = 25) -> str:
    m = int(mins or 25)
    d = {'running': True, 'end': (datetime.now() + timedelta(minutes=m)).isoformat(), 'mode': 'work', 'mins': m}
    _save(d)
    return f'Pomodoro started {m} min'


def pomodoro_stop() -> str:
    d = _load()
    d['running'] = False
    d['end'] = None
    _save(d)
    return 'Pomodoro stopped'


def pomodoro_status() -> str:
    d = _load()
    if not d.get('running') or not d.get('end'):
        return 'Pomodoro nahi chal raha'
    try:
        end = datetime.fromisoformat(d['end'])
        left = max(0, (end - datetime.now()).total_seconds())
        m, s = divmod(int(left), 60)
        return f'{m:02d}:{s:02d} left ({d["mode"]})'
    except Exception:
        return 'Pomodoro chal raha hai'
