"""BLOCKED patterns. Command aur args ki TEXT yahin jaanchi jaati hai.

Sirf naam dekh kar allow nahi hota — poora text regex se check hota hai.
Code me koi pattern hard-coded nahi; `config.EXTRA_BLOCKED_PATTERNS` bhi lagta hai.
"""

import re

import config

# (naam, regex). Naam sirf log/report ke liye hai, regex hi faisla karta hai.
PATTERNS = (
    ("disk format", r"\bdiskpart\b|\bmkfs\b|\bformat\.com\b|\bformat\s+[a-zA-Z]:"
                    r"|\bformat\b[^\n]*/[a-zA-Z]|\b(clear-disk|initialize-disk|remove-partition"
                    r"|resize-volume)\b"),
    ("disk khaali karna", r"\bclean\s+all\b|\bclean\s+/\s*[amf]?\b"),
    ("drive root delete", r"\b(del|rd|rmdir|remove-item|erase)\b[^|;&\n]*[a-zA-Z]:\\?\s*($|\*|-)"),
    ("registry delete", r"\breg(\.exe)?\s+(delete|uninstall)\b|\bregedit\b|\bremove-item\b[^|\n]*\bhk(cu|lm|ey_)"
                        r"|\bnew-item\b[^|\n]*\bhk(cu|lm)\b[^|\n]*\.(ps1|reg)"),
    ("encoded powershell", r"-e[a-z]{0,12}\b\s+[A-Za-z0-9+/=]{8,}|-\s*encodedcommand"),
    ("download aur chalana", r"\b(curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod|wscript|cscript)\b"
                             r"[^|\n]*\|\s*(iex|invoke-expression|invoke-command|cmd|powershell|pwsh|bash|sh)\b"
                             r"|\bcertutil\b[^\n]*(urlcache|decode|verifyctl)\b|\bbitsadmin\b"
                             r"|\bstart-bittransfer\b"),
    ("code turant chalana", r"\biex\b|\binvoke-expression\b|\bdownloadstring\b|\bdownloadfile\b"
                            r"|\bnew-object\s+net\.webclient\b"),
    ("protected folder me badlav", r"\b(del|erase|remove-item|rmdir|rd|rm|takeown|icacls|cacls|attrib"
                                   r"|set-content|add-content|out-file|new-item|copy-item|move-item"
                                   r"|rename-item|clear-content)\b[^|\n]*\b(windows|system32|syswow64|winsxs"
                                   r"|program files|programdata|boot|drivers)\b"),
    ("protection band karna", r"\bset-mppreference\b|\bnetsh\s+advfirewall\b[^\n]*\b(off|disable)\b"),
    (".env ya key ki file", r"(?<![\w.])[\w\\\-/.]*\.env\b|\bid_rsa\b|\bid_ed25519\b|\bcredentials\b"
                            r"|\bsecrets?\.json\b|\.ssh\\"),
    ("env variables padhna", r"\$env:\w*(key|token|secret|password)|\bget-childitem\s+env:"
                              r"|\bdir\s+env:|\bsetx\b[^\n]*(key|token|secret)"),
)

_COMPILED = tuple((name, re.compile(pattern, re.IGNORECASE)) for name, pattern in PATTERNS)
_EXTRA = tuple((p, re.compile(re.escape(p), re.IGNORECASE)) for p in config.EXTRA_BLOCKED_PATTERNS)
_ALL = _COMPILED + _EXTRA


def check_text(text: str) -> str:
    """Pehla pattern jo mila uska naam, warna khaali string."""
    if not text:
        return ""
    for name, regex in _ALL:
        if regex.search(text):
            return name
    return ""


def is_blocked(text: str) -> bool:
    return bool(check_text(text))
