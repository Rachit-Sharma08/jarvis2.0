"""logs/actions.log + memory turns -> masked train/eval JSONL (sirf local).

Ek example: {"instruction": ..., "tool": naam ya null, "args": {...}, "result_ok": bool}

actions.log me user ka vaakya hota hi nahi (sirf tool + args + decision), is liye
tool-wale example ki instruction args ke text se banti hai. Memory turns me asli
user text hai (tool null). Sab text `gatekeeper.audit.mask()` se guzarta hai.

Phone/screen/read_file/OTP-password/profile.json wali entries poori hatti hain.
Split hash par: 80% train, 20% eval — dedupe ke baad, is liye overlap kabhi nahi.

Chalane ka raasta: `python -m tools.export_dataset`
"""
import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import config
from core import memory
from gatekeeper.audit import mask

DROP_TOOLS = {"phone_task", "screen_look", "read_file", "remember", "forget"}

# shortcut: OTP sirf shabd se pakda jaata hai (bina shabd wale 4-6 ank nahi);
# asli OTP data dikhe to ank-pattern ka rule add karo.
SECRET_WORDS = re.compile(
    r"(?i)\b(otp|password|passcode|passwd|pwd|pass|pin|secret|api[_ -]?key|token)\b"
)
PROFILE_WORDS = re.compile(r"(?i)profile\.json|core[\\/]profile")

_LINE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| mode=(?P<mode>[^|]*) \| "
    r"tool=(?P<tool>[^|]*) \| args=(?P<args>.*) \| decision=(?P<decision>[^|]*) \| "
    r"result=(?P<result>.*)$"
)


def _parse_args(text: str):
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return {}
    return value if isinstance(value, dict) else {}


def read_actions(path=None):
    """actions.log ki har line -> dict. Kharab line chup-chaap chhut jaati hai."""
    path = Path(path or config.ACTION_LOG)
    rows = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return rows
    for line in text.splitlines():
        found = _LINE.match(line)
        if not found:
            continue
        tool = found.group("tool").strip()
        if not tool:
            continue
        rows.append({
            "tool": tool,
            "args": _parse_args(found.group("args").strip()),
            "decision": found.group("decision").strip(),
        })
    return rows


def _candidates(rows, turns):
    for item in turns:
        if item.get("role") != "user":
            continue
        yield {"instruction": item.get("text", ""), "tool": None, "args": {}, "result_ok": True}
    for row in rows:
        instruction = " ".join(
            str(value) for value in row["args"].values() if isinstance(value, str)
        )
        yield {
            "instruction": instruction,
            "tool": row["tool"],
            "args": row["args"],
            "result_ok": row["decision"] == "allow",
        }


def _blocked(example) -> bool:
    text = example["instruction"] + " " + json.dumps(example["args"], ensure_ascii=False)
    if example["tool"] in DROP_TOOLS:
        return True
    return bool(SECRET_WORDS.search(text) or PROFILE_WORDS.search(text))


def _masked(example):
    return {
        "instruction": " ".join(mask(example["instruction"]).split())[:300],
        "tool": example["tool"],
        "args": {
            key: (mask(value) if isinstance(value, str) else value)
            for key, value in example["args"].items()
        },
        "result_ok": bool(example["result_ok"]),
    }


def _key(example) -> str:
    return json.dumps(example, sort_keys=True, ensure_ascii=False)


def _bucket(example) -> str:
    digest = hashlib.sha256(_key(example).encode("utf-8")).hexdigest()
    return "eval" if int(digest[:8], 16) % 100 >= 80 else "train"


def _write(path: Path, items: list) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for item in items:
            handle.write(_key(item) + "\n")


def run(actions_path=None, turns=None) -> dict:
    rows = read_actions(actions_path)
    turns = memory.MEM._items if turns is None else turns
    seen, kept = set(), []
    for example in _candidates(rows, turns):
        if _blocked(example):
            continue
        example = _masked(example)
        if not example["instruction"]:
            continue
        key = _key(example)
        if key in seen:
            continue
        seen.add(key)
        kept.append(example)

    train = [item for item in kept if _bucket(item) == "train"]
    evals = [item for item in kept if _bucket(item) == "eval"]
    out = Path(config.DATA_DIR) / "export"
    out.mkdir(parents=True, exist_ok=True)
    _write(out / "train.jsonl", train)
    _write(out / "eval.jsonl", evals)

    counts = Counter(item["tool"] for item in kept if item["tool"])
    print(f"export: {len(kept)} example (train {len(train)}, eval {len(evals)}) | "
          f"tool-wale {sum(counts.values())}")
    for name in sorted(counts):
        print(f"  {name}: {counts[name]}")
    print(f"files: {out / 'train.jsonl'} | {out / 'eval.jsonl'}")
    return {
        "total": len(kept),
        "tool_examples": sum(counts.values()),
        "per_tool": dict(counts),
        "train": len(train),
        "eval": len(evals),
        "files": [str(out / "train.jsonl"), str(out / "eval.jsonl")],
    }


def main() -> int:
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
