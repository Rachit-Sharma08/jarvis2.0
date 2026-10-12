"""Faisla: tool + args se SAFE / ASK / BLOCKED.

Sirf yahin se risk decide hota hai. Config me base risk hai, yahan args
dekh kar use badhaya jaata hai (allowed folders, http/https, allowed apps).
"""

import re
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


# ---- KAAM 3: hamesha card wale kaam ----------------------------------------
# Ye `decide()` ke **shuru me** chalti hain — matlab tool chahe kisi bhi
# source se aaya ho (mic, HUD, ya page/file/message ka content), card ke bina
# aage nahi badhega. Isi liye page me likha "sab allow kar do" inhe bypass
# **nahi** kar sakta: tool ke **args** hi yahan dekhe jaate hain, aur args
# kaun likha ye puchha hi nahi jaata.
_ASK_COMPILED = tuple((name, re.compile(pat, re.IGNORECASE))
                      for name, pat in config.ALWAYS_ASK)
_NEVER_COMPILED = tuple((name, re.compile(pat, re.IGNORECASE))
                        for name, pat in config.NEVER_ALLOW)


def _escalate(text: str) -> tuple:
    """(risk, karan). `config.NEVER_ALLOW` BLOCKED, `ALWAYS_ASK` ASK.

    Pehle `ALWAYS_ASK` text ke saath + args ke saath dono par chalti hai —
    sirf args dekhne se "sab allow kar do" jaisa pattern args me na aaye par
    `open_website` ke URL me `?q=sab+allow+kar+do` ho sakta hai."""
    for name, regex in _NEVER_COMPILED:
        if regex.search(text):
            return config.BLOCKED, f"kabhi nahi: {name}"
    for name, regex in _ASK_COMPILED:
        if regex.search(text):
            return config.ASK, f"hamesha poochhna hai: {name}"
    return "", ""


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

    # KAAM 3: jo kaam **hamesha** card maangte hain. Text + saare args dono
    # dekhe jaate hain (sirf ek arg nahi) — is liye koi bhi jagah chhupa kar
    # nikal nahi sakta.
    escalate, why = _escalate(" ".join(str(v) for v in args.values()))
    if escalate:
        return escalate, why

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

    # Docstring ke mutabiq karan **hamesha** bhara hua hona chahiye — UI/log me
    # khaali karan ka matlab "kuch nahi pata". Pehle yahan `""` aa raha tha.
    return base, f"base risk {base}"
