"""Faisla: tool + args se SAFE / ASK / BLOCKED.

Sirf yahin se risk decide hota hai. Config me base risk hai, yahan args
dekh kar use badhaya jaata hai (allowed folders, http/https, allowed apps).
"""

from urllib.parse import urlparse

import config
from gatekeeper import patterns, paths

_PATH_KEYS = ("path", "folder", "file", "directory", "target")

# Sirf in args ki TEXT pattern-check hoti hai. `write_file` ka content kabhi
# nahi (warna ek note likhna bhi block ho jayega) — woh user ko dikhaya jaata hai.
_TEXT_ARGS = {
    "run_command": ("command",),
    "open_website": ("url",),
    "open_app": ("name",),
    "close_app": ("name",),
}


def _args_text(tool: str, args: dict) -> str:
    return " ".join(str(args[key]) for key in _TEXT_ARGS.get(tool, ()) if key in args)


def _path_arg(args: dict) -> str:
    for key in _PATH_KEYS:
        if key in args and args[key]:
            return str(args[key])
    return ""


def _check_path(args: dict) -> str:
    raw = _path_arg(args)
    if not raw:
        return ""
    return paths.blocked_reason(paths.resolve(raw), raw)


def _open_website(url: str) -> str:
    parsed = urlparse(str(url))
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return "sirf http/https link khul sakta hai"
    return ""


def _open_app(name: str) -> str:
    if str(name).strip().lower() in config.ALLOWED_APPS:
        return ""
    return f"'{name}' allowed apps ki list me nahi hai"


def decide(tool: str, args: dict) -> tuple:
    """-> (risk, reason). reason hamesha bhar-i hui hoti hai taaki log me kaam aaye."""
    base = config.TOOL_BASE_RISK.get(tool)
    if base is None:
        return config.BLOCKED, f"'{tool}' naam ka koi tool nahi hai"

    bad_path = _check_path(args)
    if bad_path:
        return config.BLOCKED, f"path block: {bad_path}"

    hit = patterns.check_text(_args_text(tool, args))
    if hit:
        return config.BLOCKED, f"khatarnak pattern: {hit}"

    if tool == "open_website":
        reason = _open_website(args.get("url", ""))
        return (config.BLOCKED, reason) if reason else (config.SAFE, "sirf http/https")

    if tool == "open_app":
        reason = _open_app(args.get("name", ""))
        return (config.ASK, reason) if reason else (config.SAFE, "allowed app")

    if tool in ("list_dir", "read_file"):
        path = paths.resolve(_path_arg(args) or str(config.WORKSPACE))
        if paths.is_readable(path):
            return config.SAFE, "allowed folder"
        return config.ASK, "ye folder allowed list me nahi hai"

    if tool in ("write_file", "run_command", "close_app", "delete_to_trash"):
        return config.ASK, "hamesha poochhna hai"

    return base, ""
