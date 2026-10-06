"""Tools ka registry. Yehi ek jagah se tool chalta hai.

`TOOL_ARGS` strict hai: har tool ke sirf ye args, aur sab string. LLM ka JSON
bhi isi ke hisaab se validate hota hai — koi extra field ya non-string chalega hi nahi.
"""

from tools import apps, command, files, system, reminders, todo, quick, search as search_mod

TOOLS = {
    "get_time_date": system.get_time_date,
    "system_info": system.system_info,
    "list_dir": files.list_dir,
    "read_file": files.read_file,
    "write_file": files.write_file,
    "run_command": command.run_command,
    "open_app": apps.open_app,
    "open_website": apps.open_website,
    "close_app": apps.close_app,
    "delete_to_trash": files.delete_to_trash,
    "add_reminder": reminders.add_reminder,
    "list_reminders": reminders.list_reminders,
    "clear_reminder": reminders.clear_reminder,
    "add_todo": todo.add_todo,
    "list_todos": todo.list_todos,
    "done_todo": todo.done_todo,
    "clear_todos": todo.clear_todos,
    "web_search": search_mod.web_search,
    "copy_text": quick.copy_text,
    "get_clipboard": quick.get_clipboard,
    "open_url": quick.open_url,
    "focus_app": quick.focus_app,
}

TOOL_ARGS = {
    "get_time_date": (),
    "system_info": (),
    "list_dir": ("path",),
    "read_file": ("path",),
    "write_file": ("path", "content"),
    "run_command": ("command",),
    "open_app": ("name",),
    "open_website": ("url",),
    "close_app": ("name",),
    "delete_to_trash": ("path",),
    "add_reminder": ("text", "at", "in_minutes"),
    "list_reminders": (),
    "clear_reminder": ("id",),
    "add_todo": ("text",),
    "list_todos": (),
    "done_todo": ("id",),
    "clear_todos": (),
    "web_search": ("query", "num"),
    "copy_text": ("text",),
    "get_clipboard": (),
    "open_url": ("url",),
    "focus_app": ("name",),
}

TOOL_SUMMARY = {
    "get_time_date": "abhi ka time aur date",
    "system_info": "CPU, RAM aur battery ki jaanch",
    "list_dir": "folder ki list",
    "read_file": "text file padho (20 KB tak)",
    "write_file": "file likho",
    "run_command": "PowerShell command chalao",
    "open_app": "app kholo",
    "open_website": "website browser me kholo",
    "close_app": "app band karo",
    "delete_to_trash": "file/folder Recycle Bin me bhejo",
    "add_reminder": "reminder set karo (at jaise '5 PM' ya in_minutes number)",
    "list_reminders": "pending reminders dikhao",
    "clear_reminder": "reminder clear karo (id number)",
    "add_todo": "todo add karo",
    "list_todos": "todos dikhao",
    "done_todo": "todo mark done karo (id number)",
    "clear_todos": "saare todos clear karo",
    "web_search": "internet par search karo (SerpAPI)",
    "copy_text": "text clipboard me copy karo",
    "get_clipboard": "clipboard ka text padho",
    "open_url": "URL browser me kholo",
    "focus_app": "ek app par focus do",
}


def spec() -> str:
    """LLM ke system prompt ke liye ek-line description."""
    lines = []
    for name, summary in TOOL_SUMMARY.items():
        args = ", ".join(TOOL_ARGS[name])
        lines.append(f"- {name}({args}): {summary}")
    return "\n".join(lines)


def execute(name: str, args: dict) -> str:
    """Tool chalao. Galti ho to text return karo — crash kabhi nahi."""
    func = TOOLS.get(name)
    if func is None:
        return f"'{name}' naam ka koi tool nahi hai."
    missing = set(TOOL_ARGS[name]) - set(args)
    extra = set(args) - set(TOOL_ARGS[name])
    if missing or extra:
        return f"args galat. chahiye={sorted(TOOL_ARGS[name])} extra={sorted(extra)}"
    if any(not isinstance(value, str) for value in args.values()):
        return "args galat: sab args string hone chahiye."
    try:
        return str(func(**args))
    except Exception as exc:
        return f"error: {type(exc).__name__}: {exc}"
