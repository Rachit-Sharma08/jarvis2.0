"""export_dataset: mask, drop rules, dedupe aur hash-split (eval train me nahi).

Sab kuch `isolated_data()` ke andar — asli `data/` aur `logs/` kabhi nahi chhoote.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402
from core import memory  # noqa: E402
from tests.datasafe import isolated_data  # noqa: E402
from tools import export_dataset  # noqa: E402

FAILED = []

LINES = [
    "2026-10-30 18:43:56 | mode=sunday | tool=web_search | args={'query': 'Delhi weather today', 'num': '1'} | decision=allow | result=base risk SAFE",
    "2026-10-30 18:43:54 | mode=sunday | tool=get_time_date | args={} | decision=allow | result=base risk SAFE",
    "2026-10-30 18:43:56 | mode=sunday | tool=web_search | args={'query': 'Delhi weather today', 'num': '1'} | decision=allow | result=base risk SAFE",
    "2026-10-30 18:57:12 | mode=sunday | tool=open_app | args={'name': 'Brave'} | decision=allow | result=allowed app",
    "2026-10-30 18:53:49 | mode=sunday | tool=web_search | args={'query': 'blocked search'} | decision=deny | result=tools off",
    "2026-10-31 08:33:08 | mode=sunday | tool=phone_task | args={'task': 'Call mummy'} | decision=allow | result=no-cards: auto allow",
    "2026-10-29 10:00:00 | mode=sunday | tool=screen_look | args={'question': 'kya hai'} | decision=allow | result=base risk SAFE",
    "2026-10-29 10:01:00 | mode=sunday | tool=read_file | args={'path': 'notes.txt'} | decision=allow | result=base risk SAFE",
    "2026-10-29 10:02:00 | mode=sunday | tool=run_command | args={'command': 'echo api_key=SUPERSECRET123'} | decision=allow | result=base risk SAFE",
    "2026-10-29 10:03:00 | mode=sunday | tool=web_search | args={'query': 'mera password hunter2 kya hai'} | decision=allow | result=base risk SAFE",
    "2026-10-29 10:04:00 | mode=sunday | tool=web_search | args={'query': 'profile.json me kya hai'} | decision=allow | result=base risk SAFE",
    "2026-10-29 10:05:00 | mode=sunday | tool=remember | args={'key': 'color', 'value': 'laal'} | decision=allow | result=base risk SAFE",
    "2026-10-29 10:06:00 | mode=sunday | tool=web_search | args={'query': 'gsk_abcdefghijklmnopqrst'} | decision=allow | result=base risk SAFE",
    "2026-10-29 10:07:00 | mode=sunday | tool=add_reminder | args={'text': 'paani piyo', 'at': '09:00'} | decision=allow | result=base risk SAFE",
    "ye koi log line nahi hai",
]


def check(name, got, want):
    ok = got == want
    print(("ok   " if ok else "FAIL ") + name, "" if ok else f"(got {got!r}, want {want!r})")
    if not ok:
        FAILED.append(name)


def _lines(path):
    return [line for line in Path(path).read_text(encoding="utf-8").splitlines() if line]


def _find(items, tool):
    return [item for item in items if item["tool"] == tool]


def test_export():
    with isolated_data() as tmp:
        Path(config.ACTION_LOG).write_text("\n".join(LINES) + "\n", encoding="utf-8")
        memory.MEM.add("user", "Delhi ka mausam batao")
        memory.MEM.add("user", "mera code gsk_zzzzzzzzzzzzzzzzzz hai")
        memory.MEM.add("assistant", "ji sir")

        summary = export_dataset.run()
        train_path, eval_path = summary["files"]
        train_raw, eval_raw = _lines(train_path), _lines(eval_path)
        train = [json.loads(line) for line in train_raw]
        evals = [json.loads(line) for line in eval_raw]

        check("files temp folder me", str(tmp) in train_path, True)
        check("total 7", summary["total"], 7)
        check("train+eval = total", len(train) + len(evals), summary["total"])
        check("overlap 0", set(train_raw) & set(eval_raw), set())
        check("per-tool web_search 3", summary["per_tool"].get("web_search"), 3)
        check("tool-wale 5", summary["tool_examples"], 5)

        every = train_raw + eval_raw
        joined = "\n".join(every)
        check("gsk shape mask", "gsk_abcdefghijklmnopqrst" in joined, False)
        check("memory ka gsk mask", "gsk_zzzzzzzzzzzzzzzzzz" in joined, False)
        check("mask stamp", "***" in joined, True)
        for bad in ("phone_task", "screen_look", "read_file", "remember", "hunter2",
                    "profile.json", "SUPERSECRET123"):
            check(f"hata diya: {bad}", bad in joined, False)

        chat = [item for item in train + evals if item["tool"] is None]
        check("memory turn tool null", any(
            item["instruction"] == "Delhi ka mausam batao" for item in chat), True)
        denied = _find(train + evals, "web_search")
        blocked = [item for item in denied if item["instruction"] == "blocked search"]
        check("deny par result_ok False", [item["result_ok"] for item in blocked], [False])
        allowed = [item for item in denied if item["instruction"].startswith("Delhi weather")]
        check("allow par result_ok True", [item["result_ok"] for item in allowed], [True])

        before = (Path(train_path).read_text(encoding="utf-8"),
                  Path(eval_path).read_text(encoding="utf-8"))
        export_dataset.run()
        after = (Path(train_path).read_text(encoding="utf-8"),
                 Path(eval_path).read_text(encoding="utf-8"))
        check("duobara chalane par same split", after, before)


if __name__ == "__main__":
    test_export()
    print("FAIL:", ", ".join(FAILED) if FAILED else "koi nahi")
    sys.exit(1 if FAILED else 0)
