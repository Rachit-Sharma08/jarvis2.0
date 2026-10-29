"""Card ki jagah code ka faisla - `JARVIS_NO_CARDS=1` (default).

Jab `gatekeeper/rules.py` ne ASK kaha aur card band hai, `keeper.review()`
yahan se faisla leta hai: ("ALLOW", None) ya ("DENY", "ek line Hinglish wajah").
Card banta hi nahi, koi naya UI nahi - DENY ka raasta engine ka wahi purana hai.

Sirf `config.WORKSPACE` ke andar ka safe kaam, aur **graceful app band karna**
(`close_app`) chupchaap chalta hai. Baaki sab (shell command, workspace ke bahar,
path trick, secret/executable) chupchaap mana. Ye list `TOOLS.md` me likhi hai;
badalna ho to pehle owner se.
"""

import os
from pathlib import Path

from gatekeeper import paths

import config

ALLOW, DENY = "ALLOW", "DENY"

EXEC_SUFFIXES = (".exe", ".dll", ".bat", ".cmd", ".ps1", ".vbs",
                 ".msi", ".lnk", ".scr", ".reg", ".js", ".jse", ".wsf",
                 ".hta", ".com", ".pif", ".cpl", ".py", ".pyw", ".jar",
                 ".url", ".inf", ".psm1", ".appref-ms")

SECRET_SUFFIXES = (".pem", ".key")

PROTECTED_APPS = ("explorer", "winlogon", "csrss", "services", "lsass", "system",
                  "python", "pythonw")


def _short(text: str) -> str:
    """LLM ka diya naam/path: control characters hate, 40 char tak."""
    clean = "".join(ch for ch in str(text) if ord(ch) >= 32)
    return clean[:40]


def _secret_name(name: str) -> bool:
    low = str(name).lower()
    return (low.startswith("id_rsa") or low.endswith(SECRET_SUFFIXES)
            or paths.is_secret_file(Path(low)))


def _raw_path_bad(raw: str) -> str:
    """Raw arg pe hi pakad: khaali, UNC, '..', aakhri dot/space, NTFS stream.

    Leading whitespace/quote hataate hain par **trailing nahi** - aakhri space
    ya dot khud hi trick hai (Windows use store karte hi nahi, is liye pakadna
    hai), aur `paths.resolve()` usse chupa deta hai.
    """
    text = str(raw or "").lstrip().strip('"').strip('"')
    if not text.strip():
        return "path khaali hai"
    if text.startswith("\\\\"):
        return "UNC path se kaam nahi hota"
    parts = [part for part in text.replace("/", "\\").split("\\") if part]
    if ".." in parts:
        return "'..' se path bahar nahi jaa sakti"
    for part in parts:
        if part not in (".", "..") and part != part.rstrip(". "):
            return "path ke naam me aakhri dot/space allowed nahi"
    drive, rest = os.path.splitdrive(text)
    if ":" in (rest if drive else text):
        return "NTFS stream path allowed nahi hai"
    return ""


def _inside_workspace_bad(raw: str) -> str:
    """WORKSPACE ke andar? Wajah ya '' (khaali = theek)."""
    bad = _raw_path_bad(raw)
    if bad:
        return bad
    if paths.is_workspace(paths.resolve(raw)):
        return ""
    return "ye Jarvis ke workspace ke andar nahi hai"


def _extra_path_bad(path: Path) -> str:
    """Resolved path pe extra niyam: .git, secret, executable."""
    if ".git" in [part.lower() for part in path.parts]:
        return ".git ke andar ka path allowed nahi"
    if _secret_name(path.name.rstrip(". ")):
        return "secret file (.env/key) ka path allowed nahi"
    if path.name.rstrip(". ").lower().endswith(EXEC_SUFFIXES):
        return f"{path.suffix} file allowed nahi (executable/script)"
    return ""


def _write_file(args: dict) -> tuple:
    bad = _inside_workspace_bad(args.get("path", ""))
    if bad:
        return DENY, bad
    bad = _extra_path_bad(paths.resolve(args.get("path", "")))
    if bad:
        return DENY, bad
    return ALLOW, None


def _delete_to_trash(args: dict) -> tuple:
    raw = args.get("path", "")
    bad = _inside_workspace_bad(raw)
    if bad:
        return DENY, bad
    path = paths.resolve(raw)
    if path == paths.resolve(str(config.WORKSPACE)):
        return DENY, "workspace root delete nahi ho sakti"
    bad = _extra_path_bad(path)
    if bad:
        return DENY, bad
    return ALLOW, None


def _readish(args: dict) -> tuple:
    """list_dir/read_file ka ASK-case: allowed folders ke bahar -> DENY."""
    raw = args.get("path", "")
    bad = _raw_path_bad(raw)
    if bad:
        return DENY, bad
    if raw and _secret_name(Path(str(raw)).name):
        return DENY, "secret file (.env/key) padhna allowed nahi"
    return DENY, "ye folder allowed list me nahi hai"


def _close_app(args: dict) -> tuple:
    name = _short(args.get("name", "")).strip().lower()
    if not name:
        return DENY, "app ka naam do"
    if name in PROTECTED_APPS:
        return DENY, f"{name} band karna allowed nahi"
    # 29-Oct: pehle yahan hamesha DENY tha (force kill ki wajah se). Ab
    # close graceful hai (`tools/apps.py` - WM_CLOSE, force sirf fallback).
    return ALLOW, None


def resolve_ask(tool: str, args: dict) -> tuple:
    """-> ("ALLOW", None) | ("DENY", "ek line Hinglish wajah"). Card nahi banta."""
    args = args or {}
    if config.TRUST_ALL:
        # Owner ka faisla: koi restriction nahi. NEVER_ALLOW (rules.py) phir
        # bhi pehle chalti hai, is liye gatekeeper/.env delete yahan tak
        # pahunchti hi nahi.
        return ALLOW, None
    if tool == "write_file":
        return _write_file(args)
    if tool == "delete_to_trash":
        return _delete_to_trash(args)
    if tool == "close_app":
        return _close_app(args)
    if tool == "run_command":
        return DENY, "shell command abhi band hai, mujhe specific tool chahiye"
    if tool in ("list_dir", "read_file"):
        return _readish(args)
    if tool in ("remember", "forget"):
        # Sirf `data/profile.json` - koi path arg nahi, is liye likhna safe hai.
        return ALLOW, None
    if tool == "phone_task":
        # Phone owner ke haath me hai aur kaam wahin hota hai (PC par nahi).
        # Voice se "call karo" chale bina card ke - owner ka faisla (29-Oct).
        return ALLOW, None
    if tool == "screen_look":
        # User khud kehta hai "screen dekho" - uski apni screen hai. Par
        # screenshot internet par jaata hai, is liye ASK base risk hai; cards
        # band hone par (default) code allow karta hai.
        return ALLOW, None
    if tool == "open_app":
        name = _short(args.get("name", ""))
        return DENY, f"'{name}' allowed apps ki list me nahi hai"
    return DENY, "ye abhi allowed nahi"
