"""Daily brief (local): reminders + todos summary."""
from datetime import datetime

from tools import reminders, todo


def daily_brief() -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    out = [f'DAILY BRIEF ({now})']
    try:
        r = reminders.list_reminders()
        out.append('REMINDERS: ' + r)
    except Exception:
        out.append('REMINDERS: n/a')
    try:
        t = todo.list_todos()
        out.append('TODOS: ' + t)
    except Exception:
        out.append('TODOS: n/a')
    return '\n'.join(out)
