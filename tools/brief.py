"""Daily brief (local): reminders + todos summary, user ke naam ke saath."""
from datetime import datetime

from core import profile
from tools import reminders, todo


def _greeting(hour: int) -> str:
    if hour < 5:
        return "Good night"
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    if hour < 21:
        return "Good evening"
    return "Good night"


def daily_brief() -> str:
    now = datetime.now()
    name = profile.load().get("user_name", "")
    who = f", {name} Sir" if name else ", Sir"
    out = [f'DAILY BRIEF ({now.strftime("%Y-%m-%d %H:%M")}) - {_greeting(now.hour)}{who}']
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
