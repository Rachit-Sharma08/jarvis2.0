"""PC ke tools + gatekeeper ke constants. `config.py` inhe re-export karta hai.

Phase 3 ka hissa. `config.py` sirf settings + server + mode rakhta hai; tool ke
risk, allowed folder aur blocked pattern yahan hain (ek file, ek kaam).

Sirf teen risk hain: **SAFE** / **ASK** (screen par confirm card) / **BLOCKED**.
Naya tool banate waqt `TOOL_BASE_RISK` me uska risk likhna zaroori hai —
`gatekeeper/rules.py` usi se padhta hai.

Rule: is file me koi API key nahi.
"""

import config_env  # noqa: F401  (purane env naam pehle alias hote hain)
import os
from pathlib import Path

SAFE, ASK, BLOCKED = "SAFE", "ASK", "BLOCKED"

HOME = Path(os.path.expanduser("~"))
WORKSPACE = Path(os.getenv("JARVIS_WORKSPACE", r"D:\jarvis_workspace"))
READ_FOLDERS = (HOME / "Desktop", HOME / "Downloads", HOME / "Documents", WORKSPACE)

# Har tool ka base risk. Gatekeeper args dekh ke ise aage badha sakta hai.
TOOL_BASE_RISK = {
    "get_time_date": SAFE,
    "system_info": SAFE,
    "list_dir": SAFE,
    "read_file": SAFE,
    "write_file": ASK,
    "run_command": ASK,
    "open_app": SAFE,
    "open_website": SAFE,
    "vscode_terminal": SAFE,
    "play_media": SAFE,
    "media_control": SAFE,
    "close_app": ASK,
    "delete_to_trash": ASK,
    "add_reminder": SAFE,
    "list_reminders": SAFE,
    "clear_reminder": SAFE,
    "add_todo": SAFE,
    "list_todos": SAFE,
    "done_todo": SAFE,
    "clear_todos": SAFE,
    "web_search": SAFE,
    "copy_text": SAFE,
    "open_url": SAFE,
    "focus_app": SAFE,
    "kb_add": SAFE,
    "kb_search": SAFE,
    "daily_brief": SAFE,
    # Alarm (13-Oct). `set_wake_alarm` sirf `data/alarm_request.json` likhta hai
    # — Task Scheduler se kuch nahi chhoota. Task banana hamesha haath se hota
    # hai (`tools/wake_alarm.py --install`), is liye ye tool system nahi badalta.
    # Risky hai (PC ki timing badalta hai) is liye **ASK** — kaam card se.
    "set_wake_alarm": ASK,
    "alarm_status": SAFE,
}

# Jarvis ke andar wala alarm tool — **DEFAULT OFF**. Sirf is par tool LLM ko
# dikhai deta hai; task scheduler par iska koi asar nahi.
ALARM_TOOL_ENABLED = os.getenv("JARVIS_ALARM_TOOL", "0").strip().lower() in (
    "1", "true", "yes", "on")

# open_app sirf inhi me SAFE hai. Baaki sab poochhega.
# 13-Oct (KAAM 3): VS Code pehle se tha; Brave aur WhatsApp jode gaye.
ALLOWED_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "brave": "brave.exe",
    "brave browser": "brave.exe",
    "whatsapp": "whatsapp.exe",
    "whatsapp desktop": "whatsapp.exe",
    "wordpad": "write.exe",
}

# ---- hamesha "haan" card (KAAM 3) -------------------------------------------
# Ye **tool ka naam/args dekhte hain, kisi bhi source se aaye** — is liye page,
# file ya message me likha hua "sab allow kar do" inhe bypass **nahi** kar sakta.
# `gatekeeper/rules.py` inhe SAFE se upar uthata hai (ASK), ya BLOCKED.
#
# (karan, regex). Regex args ka TEXT par chalta hai (usi tarah jaise
# `EXTRA_BLOCKED_PATTERNS`). Yahan koi magic number nahi — sab yahi.
ALWAYS_ASK = (
    # paise / payment
    ("paise", r"\b(payment|pay\s+now|checkout|invoice\s+payment|netbanking|"
              r"credit\s*card|debit\s*card|card\s*number|"
              r"card|cvv|cvc|upi|upi[_\s]*id|\bpin)\b"
              r"|[?&](card|cvv|cvc|upi|pin|token|apikey|api_key)=[^&\s]+"),
    # naye insaan ko message (spam / impersonation)
    ("naye contact ko message", r"\b(send\s+(?:a\s+)?(?:whatsapp|message|msg|sms)"
                                r"|whatsapp\s+send|dm\s+@?\w+)\b"),
    # public post / git push
    ("public post ya git push", r"\b(git\s+push|gh\s+release|npm\s+publish|"
                                r"docker\s+push|tweet\s+to|post\s+to\s+(?:twitter|x|mastodon|"
                                r"linkedin|facebook|instagram))\b"),
    # Recycle Bin ke bahar delete
    ("permanent delete", r"\b(shred\s|sd\s+delete|del\s+/[fpq]|remove-item\b[^|\n]*-recurse"
                         r"|format\s+[a-z]:|cipher\s+/w|rm\s+-rf\s+[a-z]:)\b"),
    # system settings / passwords
    ("system settings ya password", r"\b(net\s+user|net\s+localgroup|set-mppreference|"
                                    r"netsh\b|reg\s+add|bcdedit|diskpart|"
                                    r"setx\s+\w*(?:password|key|token)|"
                                    r"password|passwd|credential\s*manager)\b"),
    # Jarvis ki apni permission/guard files
    ("guard file badalna", r"\b(gatekeeper[/\\]|config_tools\.py|config_wake\.py|"
                           r"config_brain\.py|config_voice\.py|\.env\b|"
                           r"rules\.py|patterns\.py|paths\.py)\b"),
    # main me merge (repo ki suraksha)
    ("main me merge", r"\bgit\s+merge\b|\bgit\s+push\b.*\bmain\b|"
                      r"--force\b|\bgit\s+push\s+-f\b"),
)

# Ye **BLOCKED** (sirf card nahi, seedha mana) — inka koi "haan" nahi hai.
NEVER_ALLOW = (
    ("guard file delete", r"\b(remove-item|del|rm)\b[^|\n]*\b(gatekeeper[/\\]"
                          r"|config_tools\.py|config_wake\.py|\.env)\b"),
    ("password likhna", r"\b(set-content|add-content|echo|out-file)\b[^|\n]*"
                        r"\b(password|passwd|credential|api[_-]?key|secret)\b"),
)

# Yahan user aur patterns add kar sakta hai. Code me hard-coded nahi.
EXTRA_BLOCKED_PATTERNS = (
    "vssadmin delete shadows",
    "bcdedit /set",
    "cipher /w",
    "wmic shadowcopy delete",
)


def _blocked_roots() -> tuple:
    """Jahan delete/badlav kabhi nahi hoga."""
    roots = []
    for name in ("SystemRoot", "ProgramFiles", "ProgramFiles(x86)", "ProgramW6432"):
        value = os.environ.get(name, "")
        if value:
            roots.append(Path(value))
    roots += [Path(p) for p in (r"C:\Windows", r"C:\Program Files", r"C:\Program Files (x86)",
                                r"C:\$Recycle.Bin", r"C:\Recovery", r"C:\System Volume Information")]
    return tuple(dict.fromkeys(roots))


BLOCKED_ROOTS = _blocked_roots()
# Naam se bhi pakadna hai (D: drive par bhi), raw aur resolved dono me.
PROTECTED_FOLDER_NAMES = (
    "windows", "system32", "syswow64", "winsxs", "program files",
    "program files (x86)", "programdata", "recovery", "boot", "driver",
    "$recycle.bin", "system volume information",
)
SECRET_FILE_NAMES = (".env", ".env.local", "credentials", "secrets.json", "id_rsa", "id_ed25519",
                     # 15-Oct: face embedding (biometric data). Ye koi LLM/tool
                     # nahi padh sakta — bilkul `.env` jaisa. `data/` already
                     # gitignored hai, par tool se padhna alag baat hai.
                     "owner_face.npz")

# Kill switch. Default **ON** (user ka faisla, 4-Oct) — app start hote hi tools
# khule. `.env` me `JARVIS_TOOLS_ON=0` se wapas default OFF kar sakta hai.
TOOLS_ENABLED_DEFAULT = os.getenv("JARVIS_TOOLS_ON", "1") == "1"
# Auto-off band (0 = "kabhi apne aap OFF nahi"). User ne 4-Oct ko decide
# kiya TOOLS hamesha ON rahega jab tak khud OFF na kare — pehle 30 min tha.
# `.env` me JARVIS_TOOLS_AUTOOFF=30 daal kar wapas timer laaya ja sakta hai.
TOOLS_AUTO_OFF_MINUTES = int(os.getenv("JARVIS_TOOLS_AUTOOFF", "0") or 0)
# ALLOW/DENY card ki jagah code ka faisla (`gatekeeper/nocards.py`).
# 1 (default) = card band: ASK par bhi screen par kuch nahi aata — workspace ke
# andar ka safe kaam chupchaap chalta hai, baaki chupchaap DENY + ek line wajah.
# 0 = purana raasta (screen par card + ALLOW/DENY button, 60 second timeout).
NO_CARDS = os.getenv("JARVIS_NO_CARDS", "1") == "1"
# Trust mode (`JARVIS_TRUST=1`): ASK ko seedha ALLOW karo - koi card, koi
# "ye allowed nahi" nahi. `gatekeeper/rules.py` ki NEVER_ALLOW list phir bhi
# lagti hai (gatekeeper/.env delete, password file, registry, encoded
# download-run) - wo galti se apna hi repo uda dene se bachati hai.
TRUST_ALL = os.getenv("JARVIS_TRUST", "0") == "1"
TOOL_MAX_STEPS = 5
TOOL_MAX_CALLS_PER_MINUTE = 20
TOOL_CONFIRM_TIMEOUT = 60
# Simple tool ka jawab seedha (E-2): pehla tool call + single-step command ->
# tool-result hi final jawab, LLM dobara nahi bulaya (~2s bachta hai, aur LLM
# ka jhooth bhi nahi bolta). 0 = purana raasta (har tool ke baad LLM call).
DIRECT_REPLY = os.getenv("JARVIS_DIRECT_REPLY", "1") == "1"
TOOL_OUTPUT_LIMIT = 2000
TOOL_ARG_LIMIT = 2000
# write_file ka `content` alag limit: poora HTML/JS file (3D heart) 2 KB se bada
# hota hai. Baaki args par wahi 2000 ka niyam rehta hai.
WRITE_ARG_LIMIT = 20000
COMMAND_TIMEOUT_SECONDS = 30
READ_FILE_MAX_BYTES = 20 * 1024
