"""Simple tool ka seedha jawab — doosra LLM call bachao (E-2).

Jin tools ka result pehle se saaf Hinglish me hai (open_app, add_todo,
write_file ...) unke liye LLM ko dobara bulakar jawab banwana bekaar hai: ~2
second lagta hai aur LLM kabhi jhooth bhi bol deta hai ("website khol diya"
bina tool call ke). Is liye pehla (aur single-step) tool call hone par wahi
tool-result final jawab hai — LLM ko dobara bulaye bina.

DENY par bhi wahi raasta: gatekeeper ki asli wajah seedhe. Pehle LLM se
poochhte the aur wo "already closed" jaisa jhooth bol deta tha.

Baaki tools (list_dir, read_file, web_search, list_todos, list_reminders,
kb_search, system_info, daily_brief) ka data samjhana padta hai — un par
purana raasta (tool result LLM ko, phir LLM ka jawab).
"""

from core import turnguard

# In tools ka result khud hi final jawab ban jaata hai.
DIRECT_TOOLS = frozenset({
    "get_time_date", "open_app", "open_website", "open_url", "write_file",
    "delete_to_trash", "add_todo", "add_reminder", "copy_text", "focus_app",
})

# In shabdon wale command me ek se zyada kaam ho sakta hai — multi-step chain
# hai, is liye purana raasta (dobara LLM call) hi sahi hai.
MULTI_WORDS = (" aur ", " phir ", " fir ", " uske baad", " baad me",
               " then ", " and ", ",", ";")

DENY_LINE = "Ye nahi kar sakta: %s."
MAX_CHARS = 160


def looks_single_step(user_text: str) -> bool:
    """User ne ek hi kaam kaha? Multi-kaam wale shabd mile to False."""
    low = " " + str(user_text or "").strip().lower() + " "
    return not any(word in low for word in MULTI_WORDS)


def _clean(text) -> str:
    """Control character hatao, ek line, 160 char tak."""
    out = "".join(ch if (ord(ch) >= 32 and ord(ch) != 127) else " " for ch in str(text))
    return " ".join(out.split())[:MAX_CHARS]


def _deny_reason(result_text: str) -> str:
    """`run_tool` ka "tool nahi chala — <wajah>" -> sirf wajah."""
    reason = str(result_text).partition(turnguard.DENY_PREFIX)[2]
    return reason.strip(" \u2014-") or str(result_text)


def reply_for(tool, args, verdict, result_text):
    """Final jawab (string) ya None = purana raasta (LLM dobara bulao)."""
    if verdict == "deny":
        return DENY_LINE % _clean(_deny_reason(result_text))
    if tool not in DIRECT_TOOLS:
        return None
    text = _clean(result_text)
    return text or None
