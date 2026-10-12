"""LLM lane - latency baseline part 2 (suite se bahar, asli network allowed).

Sirf LLM ka hissa: 3 model, 5 chhote Hinglish sawal, har ek 5 baar, beech me 2 s
gap. Doosra hissa (STT/TTS/wait/andaza) `dryrun_latency2.py` me hai, aur `stats()`
wahin se bhi leta hai.

Koi key/secret print nahi. `data/` me kuch nahi likha jaata.
"""
import os, statistics, sys, time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_env():
    """.env ko env vars me bharo (print nahi)."""
    try:
        text = (Path(__file__).resolve().parent.parent / ".env").read_text("utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"'))
    except Exception:
        pass


_load_env()

import config                                   # noqa: E402

REPS, GAP = 5, 2.0
MODELS = ("llama-3.1-8b-instant", "openai/gpt-oss-20b", "openai/gpt-oss-120b")
QUESTIONS = ["time kya hai", "chrome kholo", "notes me likho kal doodh lana hai",
             "aaj mausam kaisa rahega", "gana chala do"]


def error_kind(text):
    """Groq ke error message ka chhota tag (429 / 404 / 503 / timeout ...)."""
    low = (text or "").lower()
    if "429" in low or "rate limit" in low:
        return "429"
    if "404" in low or "decommissioned" in low or "not found" in low:
        return "404-gone"
    if "503" in low or "overloaded" in low:
        return "503-busy"
    if "timeout" in low or "timed out" in low:
        return "timeout"
    if "500" in low:
        return "500"
    return "other(" + " ".join((text or "").split())[:40] + ")"


def llm_call(model, messages):
    """Groq chat call, app ke shape me (temperature 0.7, app max_tokens).

    -> (tag, ms): tag = "ok" ya `error_kind()`, ms = naapne wala time ya `None`.
    `brain/groq_client.py` bhi yahi maangta hai.
    """
    from groq import Groq
    client = Groq(api_key=config.GROQ_API_KEY, timeout=config.BRAIN_TIMEOUT_GROQ)
    start = time.perf_counter()
    try:
        client.chat.completions.create(
            model=model, messages=messages, temperature=0.7,
            max_tokens=config.BRAIN_MAX_TOKENS)
        return "ok", int((time.perf_counter() - start) * 1000)
    except Exception as exc:
        return error_kind(str(exc)), None


def stats(samples):
    """-> (n, median, p90, min, max). Sirf naapne wale (int) samples."""
    ok = sorted(s for s in samples if isinstance(s, int))
    if not ok:
        return 0, "-", "-", "-", "-"
    return (len(ok), int(statistics.median(ok)),
            ok[min(len(ok) - 1, int(0.9 * len(ok)))], ok[0], ok[-1])


def lane(model, persona, out):
    """Ek model: 5 sawal x 5 baar, beech me 2 s gap. -> (median, error count)."""
    samples = []
    for q in QUESTIONS:
        row, msgs = [], [{"role": "system", "content": persona},
                         {"role": "user", "content": q}]
        for _ in range(REPS):
            tag, ms = llm_call(model, msgs)
            row.append(ms if ms is not None else tag)
            samples.append(ms if ms is not None else tag)
            time.sleep(GAP)
        out(f"    {q[:34]:36} {str(row)}")
    n, med, p90, mn, mx = stats(samples)
    bad = Counter(s for s in samples if isinstance(s, str))
    out(f"  {model:24} n={n} median={med} p90={p90} min={mn} max={mx} ms"
        f" | gine: {sum(bad.values())}" + (f" {dict(bad)}" if bad else ""))
    return med, sum(bad.values())