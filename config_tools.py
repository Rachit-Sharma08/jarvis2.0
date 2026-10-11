"""PC ke tools + gatekeeper ke constants. `config.py` inhe re-export karta hai.

Phase 3 ka hissa. `config.py` sirf settings + server + mode rakhta hai; tool ke
risk, allowed folder aur blocked pattern yahan hain (ek file, ek kaam).

Sirf teen risk hain: **SAFE** / **ASK** (screen par confirm card) / **BLOCKED**.
Naya tool banate waqt `TOOL_BASE_RISK` me uska risk likhna zaroori hai —
`gatekeeper/rules.py` usi se padhta hai.

Rule: is file me koi API key nahi.
"""

import os
from pathlib import Path

SAFE, ASK, BLOCKED = "SAFE", "ASK", "BLOCKED"

HOME = Path(os.path.expanduser("~"))
WORKSPACE = Path(os.getenv("PRABH_WORKSPACE", r"D:\prabh_workspace"))
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
}

# open_app sirf inhi me SAFE hai. Baaki sab poochhega.
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
    "wordpad": "write.exe",
}

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
SECRET_FILE_NAMES = (".env", ".env.local", "credentials", "secrets.json", "id_rsa", "id_ed25519")

# Kill switch. Default **ON** (user ka faisla, 4-Oct) — app start hote hi tools
# khule. `.env` me `PRABH_TOOLS_ON=0` se wapas default OFF kar sakta hai.
TOOLS_ENABLED_DEFAULT = os.getenv("PRABH_TOOLS_ON", "1") == "1"
# Auto-off band (0 = "kabhi apne aap OFF nahi"). User ne 4-Oct ko decide
# kiya TOOLS hamesha ON rahega jab tak khud OFF na kare — pehle 30 min tha.
# `.env` me PRABH_TOOLS_AUTOOFF=30 daal kar wapas timer laaya ja sakta hai.
TOOLS_AUTO_OFF_MINUTES = int(os.getenv("PRABH_TOOLS_AUTOOFF", "0") or 0)
# ALLOW/DENY card ki jagah code ka faisla (`gatekeeper/nocards.py`).
# 1 (default) = card band: ASK par bhi screen par kuch nahi aata — workspace ke
# andar ka safe kaam chupchaap chalta hai, baaki chupchaap DENY + ek line wajah.
# 0 = purana raasta (screen par card + ALLOW/DENY button, 60 second timeout).
NO_CARDS = os.getenv("PRABH_NO_CARDS", "1") == "1"
TOOL_MAX_STEPS = 5
TOOL_MAX_CALLS_PER_MINUTE = 20
TOOL_CONFIRM_TIMEOUT = 60
# Simple tool ka jawab seedha (E-2): pehla tool call + single-step command ->
# tool-result hi final jawab, LLM dobara nahi bulaya (~2s bachta hai, aur LLM
# ka jhooth bhi nahi bolta). 0 = purana raasta (har tool ke baad LLM call).
DIRECT_REPLY = os.getenv("PRABH_DIRECT_REPLY", "1") == "1"
TOOL_OUTPUT_LIMIT = 2000
TOOL_ARG_LIMIT = 2000
COMMAND_TIMEOUT_SECONDS = 30
READ_FILE_MAX_BYTES = 20 * 1024

# ---- WhatsApp call (browser CDP) ---------------------------------------------
# 5-Oct: ye char constant `config_wake.py` me theek se nahi thhe (file 200 cross
# kar gayi thi) — aur wake se inka koi lena-dena nahi. WhatsApp Web ek **tool**
# hai, is liye ghar yahi hai. `config.py` inhe waise bhi re-export karta hai,
# is liye `config.CDP_PORT` jaisa references badalte nahi hue chalega.
# Edge/Chrome is port par remote debug mode me chalta hai; pehli baar QR scan.
WHATSAPP_WEB = "https://web.whatsapp.com"
CDP_PORT = 9222
CDP_HOST = "127.0.0.1"
CALL_ASK_FIRST = True         # call se pehle confirm card (gatekeeper ka ASK)
