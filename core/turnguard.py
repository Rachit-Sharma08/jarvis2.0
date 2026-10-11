"""Ek turn (ek user message) me same tool+args dobara na chale.

LLM kabhi wahi tool 5 baar bhejta hai - ALLOW ke baad bhi, DENY ke baad bhi
(dry-run me live proof: open_website x5, close_app x5). Faisla yahan hai,
LLM ke bharose nahi: pehli baar wahi (tool, args) aaya to LLM ko ek note;
doosri baar aaya to turn yahin khatam - jawab = pehle result (success) ya
DENY ki wajah. Alag args = alag key, wo dono chalte rahenge.
"""

import json

NOTE = ("ye kaam abhi ho chuka hai: {first}. Ab user ko ek chhoti Hinglish "
        "line me batao, koi tool mat bulao.")
DENY_PREFIX = "tool nahi chala"
CAP_FALLBACK = "Abhi jawab nahi de paya. Thoda saamne batao kya karna hai."


class TurnGuard:
    def __init__(self):
        self._seen = {}
        self._again = set()

    @staticmethod
    def key(tool, args):
        return tool + "|" + json.dumps(args or {}, sort_keys=True, ensure_ascii=False)

    def seen(self, tool, args):
        return self._seen.get(self.key(tool, args))

    def record(self, tool, args, verdict, text):
        self._seen[self.key(tool, args)] = (verdict, text)

    def again(self, tool, args):
        key = self.key(tool, args)
        if key in self._again:
            return True
        self._again.add(key)
        return False

    @staticmethod
    def note(entry):
        first = " ".join(str(entry[1]).split())[:160]
        return NOTE.format(first=first)

    @staticmethod
    def final(entry):
        verdict, text = entry
        if verdict == "deny":
            return text.partition(DENY_PREFIX)[2].strip(" \u2014-") or text
        return " ".join(str(text).split())[:300]

    def cap_message(self):
        if not self._seen:
            return CAP_FALLBACK
        return self.final(list(self._seen.values())[-1])
