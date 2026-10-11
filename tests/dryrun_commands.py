r"""Dry-run harness: asli LLM + asli prompt + asli gatekeeper, nakli tools (L-2).

Suite se bahar (naam dryrun_ se, test_ se nahi) - is liye yahan asli network LLM
call allowed hai. Har stub apne asli tool ke success-string jaisa hi format
lautata hai (sirf asli kaam nahi hota). Nakli duniya (stub strings, heuristics,
injection/exfil/startup cases) dryrun_cases.py me hai. Command ke beech 6s.
Chalana: .venv\Scripts\python.exe tests\dryrun_commands.py ; Report: data\dryrun_report.md
"""

import json
import re
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from core import engine as engine_mod
from core import memory
from dryrun_cases import expects, items, stub_text
from gatekeeper import audit, keeper
from gatekeeper.audit import mask
from tools import TOOLS, TOOL_SUMMARY

REAL_TOOLS = {"get_time_date", "system_info"}
STUB_TOOLS = set(TOOLS) - REAL_TOOLS
PAUSE, RETRY_PAUSE = 6.0, 10.0
WORD_OK = re.compile(r"allow|confirm", re.I)
A, D = keeper.ALLOW, keeper.DENY
S = {"reviews": [], "calls": [], "brain": [], "read_text": ""}

def ascii_safe(text) -> str:
    return str(text).encode("ascii", "replace").decode("ascii")

def install():
    """Sab kuch is process me monkeypatch se - asli config/file ko haath nahi."""
    memory.MEM._save = lambda: None
    memory.MEM._items = []
    memory.MEM.context = lambda max_turns=None: ""
    audit.log_action = lambda *a, **k: ""
    if not keeper.tools_on():
        keeper.set_tools(True)
        print("[harness] TOOLS OFF tha -> ON kiya (gatekeeper asli hai)")
    real_review = keeper.review
    def spy(tool, args, mode):
        verdict, payload = real_review(tool, args, mode)
        S["reviews"].append((tool, dict(args), verdict, "" if payload is None else str(payload)))
        return verdict, payload
    engine_mod.keeper.review = spy
    real_execute = engine_mod.execute
    engine_mod.execute = lambda name, args: (real_execute(name, args) if name not in STUB_TOOLS
                                             else stub_text(name, args, S["read_text"]))
    real_ask = engine_mod.router.ask
    def timed(history, persona):
        began = time.perf_counter()
        out = real_ask(history, persona)
        S["calls"].append(int((time.perf_counter() - began) * 1000))
        return out
    engine_mod.router.ask = timed

def run_one(idx, text, stub=""):
    S["reviews"], S["calls"], S["brain"], S["read_text"] = [], [], [], stub
    answers = []
    for ev in engine_mod.Engine().handle(text, "dryrun-%d" % idx):
        if ev.get("type") == "message" and ev.get("role") == "assistant":
            answers.append(ev.get("text", ""))
        elif ev.get("type") == "log" and (ev.get("data") or {}).get("brain"):
            S["brain"].append(ev["data"]["brain"])
    answer = " ".join(mask(answers[-1] if answers else "(koi jawab nahi)").split())
    return {"reviews": S["reviews"], "calls": S["calls"], "brain": S["brain"], "answer": answer}

def show(text, limit=120) -> str:
    return mask(" ".join(str(text).split()).replace("|", "/"))[:limit]

def repeat_cell(r) -> str:
    seen = {}
    for t, a, v, w in r["reviews"]:
        seen.setdefault((t, json.dumps(a, sort_keys=True)), []).append(v)
    out = [f"{t} x{len(vs)} ({'ALLOW' if A in vs else 'DENY'} ke baad repeat)"
           for (t, _k), vs in seen.items() if len(vs) > 1]
    return "; ".join(out) if out else "none"

def action_cell(r) -> str:
    seen, out = set(), []
    for t, a, v, w in r["reviews"]:
        key = (t, json.dumps(a, sort_keys=True))
        if key not in seen:
            seen.add(key)
            out.append(f"{t}({show(' '.join(f'{k2}={v2}' for k2, v2 in a.items()), 70)})")
    return "; ".join(out) if out else "(koi tool nahi)"

def verdict_cell(r) -> str:
    seen, out = set(), []
    for t, a, v, w in r["reviews"]:
        if (t, v) not in seen:
            seen.add((t, v))
            out.append(f"{t} {v.upper()}" + (f" ({w})" if w else ""))
    return "; ".join(out) or "-"

def make_row(idx, text, r, ok) -> str:
    outcome, reason = ok
    ms = "+".join(str(c) for c in r["calls"]) or "-"
    return (f"| {idx} | {show(text, 55)} | {len(r['calls'])} | {repeat_cell(r)} | {verdict_cell(r)} | "
            f"{show(r['answer'])} | {ms} | {outcome} - {show(reason, 55)} |")

def run_all():
    tables, results, latencies = [], [], []
    entries = items()
    for idx, (text, check, stub) in enumerate(entries, 1):
        if idx > 1:
            print(f"[harness] {int(PAUSE)}s ruko (rate limit)")
            time.sleep(PAUSE)
        r = run_one(idx, text, stub)
        ok = check(r)
        latencies.extend(r["calls"])
        results.append([idx, text, r, ok])
        tables.append(make_row(idx, text, r, ok))
        print(ascii_safe(tables[-1]))
    return tables, results, latencies

def retry_failed(results, tables, latencies):
    entries = items()
    repeats = []
    for pos, entry in enumerate(results):
        idx, text, r, ok = entry
        if r["brain"] and r["brain"][-1] == "none":
            print(ascii_safe(f"[harness] #{idx} brain fail tha -> ek baar dobara"))
            time.sleep(RETRY_PAUSE)
            r2 = run_one(idx, text, entries[idx - 1][2])
            ok2 = entries[idx - 1][1](r2)
            latencies.extend(r2["calls"])
            results[pos] = [idx, text, r2, ok2]
            tables[pos] = make_row(idx, text, r2, ok2)
            repeats.append(idx)
    return repeats

def main():
    install()
    names = list(TOOL_SUMMARY)
    print(f"[harness] LLM ko dikhne wale tools ({len(names)}): {', '.join(names)}")
    tables, results, latencies = run_all()
    repeats = retry_failed(results, tables, latencies)
    counts = {}
    for entry in results:
        counts[entry[3][0]] = counts.get(entry[3][0], 0) + 1
    med = int(statistics.median(latencies)) if latencies else 0
    mx = max(latencies) if latencies else 0
    allow_rep = [e[0] for e in results if "ALLOW ke baad" in repeat_cell(e[2])]
    deny_rep = [e[0] for e in results if "DENY ke baad" in repeat_cell(e[2])]
    flagged = [e[0] for e in results if WORD_OK.search(e[2]["answer"])]
    out = [
        "# Dry-run report L-2 (test suite se bahar)",
        "Asli: brain pool, persona/prompt, gatekeeper (NO_CARDS=%s)." % config.NO_CARDS,
        "Nakli: tools ke jawab asli-format me (kaam nahi), memory disk par nahi, audit log nahi.",
        "Commands ke beech 6s. Secrets masked (gatekeeper.audit.mask).",
        f"LLM ko dikhne wale tool-names ({len(names)}): {', '.join(names)}",
        "", "| # | command | LLM calls | repeat | gatekeeper verdict | jawab (120) | LLM ms | natija |",
        "|---|---|---|---|---|---|---|---|",
    ] + tables + [
        "", "Kul: %d | PASS %d | WARN %d | FAIL %d | RISK %d" % (
            len(results), counts.get("PASS", 0), counts.get("WARN", 0),
            counts.get("FAIL", 0), counts.get("RISK", 0)),
        f"LLM latency: median {med}ms | max {mx}ms | {len(latencies)} calls",
        f"ALLOW ke baad repeat: {allow_rep if allow_rep else 'kahin nahi'}",
        f"DENY ke baad repeat: {deny_rep if deny_rep else 'kahin nahi'}",
        f"Jawab me ALLOW/confirm shabd: {flagged if flagged else 'kahin nahi'}",
        f"Brain-fail retry: {repeats if repeats else 'zarurat nahi padi'}",
        "", "PASS kaise check hua (heuristic):",
    ] + [f"{i}. {t} -> {e}" for i, (t, e) in enumerate(expects(), 1)]
    path = Path(config.BASE_DIR) / "data" / "dryrun_report.md"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(out) + "\n")
    for line in out:
        print(ascii_safe(line))
    print(ascii_safe(f"report likha: {path}"))

if __name__ == "__main__":
    main()
