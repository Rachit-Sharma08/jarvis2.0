"""Multi-task message: ek message me kai kaam -> code se todkar ek-ek chalao.

Pure test — koi brain, tool ya `data/` nahi (E-1b). Fake engine bas ek
assistant message deta hai, is liye poora raasta bina LLM ke check hota hai.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

from core import multitask  # noqa: E402
from tests.wakehelp import check, finish  # noqa: E402


class FakeEngine:
    def __init__(self):
        self.seen = []

    def handle(self, text, rid=""):
        self.seen.append(text)
        yield {"type": "status", "state": "thinking", "rid": rid}
        yield {"type": "message", "role": "assistant", "text": "ok: " + text, "rid": rid}


print("SPLIT")
check("ek kaam waisa hi", multitask.split("chrome kholo"), ["chrome kholo"])
check("aur se do", len(multitask.split("chrome kholo aur youtube kholo")), 2)
check("or se do", len(multitask.split("brave kholo or gaana chala")), 2)
check("comma se teen", len(multitask.split("time batao, mausam batao, reminder laga do")), 3)
check("bahut zyada kaam cap", len(multitask.split(", ".join("kaam%d" % i for i in range(9)))),
      multitask.MAX_TASKS)
check("khaali message", multitask.split(""), [""])

print("RUN")
engine = FakeEngine()
events = list(multitask.run(engine, "chrome kholo aur youtube kholo", "t"))
check("dono kaam engine tak", engine.seen, ["chrome kholo", "youtube kholo"])
check("rid har kaam ka alag",
      [e.get("rid") for e in events if e.get("role") == "assistant" and e.get("rid")],
      ["t-1", "t-2"])
answers = [e["text"] for e in events if e["type"] == "message" and e["role"] == "assistant"]
check("aakhir me joda hua jawab", answers[-1], "ok: chrome kholo | ok: youtube kholo")

engine = FakeEngine()
events = list(multitask.run(engine, "chrome kholo", "t"))
answers = [e["text"] for e in events if e["type"] == "message" and e["role"] == "assistant"]
check("ek kaam par extra jawab nahi", answers, ["ok: chrome kholo"])

finish("Multi-task: message toda, har kaam alag engine turn, aakhir me joda jawab.")
