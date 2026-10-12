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
ESTIMATE_MODELS = ("llama-3.1-8b-instant", "openai/gpt-oss-120b")
QUESTIONS = ["time kya hai", "chrome kholo", "notes me likho kal doodh lana hai",
             "aaj mausam kaisa rahega", "gana chala do"]


def ascii_only(text):
    """Console cp1252 hai - Devanagari/emoji se crash na ho. File UTF-8 me asli."""
    return text.encode("cp1252", "replace").decode("cp1252")


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


def estimate(w, stt_med, llm_med, tts_first, out):
    """(e) bolna khatam -> pehli awaaz. Pure hai (sirf jod + print).

    Kisi model ka median na mile (sab 404/error) to `stats()` ne `"-"` diya hota
    hai - wo number nahi hai. Table me `-` dikhta hai, jod me uska hissa 0.
    """
    out("e) andaza: bolna khatam -> pehli awaaz (wait + STT + LLM + TTS pehla chunk)")
    out(f"  {'model':24} {'wait':>8} {'stt':>8} {'llm':>8} {'tts30':>8} {'total':>9}")
    stt = stt_med if isinstance(stt_med, int) else 0
    tts = tts_first.get(30)
    tts = tts if isinstance(tts, int) else 0
    for model in ESTIMATE_MODELS:
        raw = llm_med.get(model)
        llm = raw if isinstance(raw, int) else 0
        cell = f"{raw:6}ms" if isinstance(raw, int) else f"{'-':>7}"
        out(f"  {model:24} {w['ms']:6}ms {stt:6}ms {cell}"
            f" {tts:6}ms {w['ms'] + stt + llm + tts:7}ms")
    out("  (playback ka pehla PCM chunk + HUD events isme shaamil nahi)")


# ---- audit flags: --models | --show-error (sirf is script me, read-only) ----

CHAT_EXCLUDE = ("whisper", "tts", "guard", "safeguard", "orpheus")


def audit_models():
    """Config/pool ke model IDs vs live /models list. List ke liye app ka apna
    `brain/checkup.py` (wahi GET, wahi URL) - app code badalta nahi."""
    from brain import pool_config
    from brain.checkup import _gemini_models, _groq_models

    def out(text=""):
        print(ascii_only(text))

    ids = _groq_models()
    chat = [i for i in sorted(ids) if not any(k in i.lower() for k in CHAT_EXCLUDE)]
    out("== Groq /models - chat/LLM wale (sirf naam) ==")
    for name in chat:
        out(f"  {name}")
    out(f"  (chat/LLM: {len(chat)} | chhude: {len(ids) - len(chat)})")

    out("")
    out("== pool ke Groq IDs (STEP 2 table) ==")
    for provider in pool_config.POOL:
        if provider["api_style"] != "groq":
            continue
        for model in provider["models"]:
            out(f"  T{provider['tier']} {provider['name']:9} {model:24}"
                f" {'exists' if model in ids else 'GONE'}")

    out(f"  -- STT (voice/stt.py): {config.GROQ_STT_MODEL:24}"
        f" {'exists' if config.GROQ_STT_MODEL in ids else 'GONE'}")

    out("")
    out("== Gemini: config ke IDs list me hain? ==")
    have = _gemini_models()
    for model in config.GEMINI_MODELS:
        out(f"  {model:24} {'haan' if model in have else 'nahi'}")


def show_error(model="openai/gpt-oss-20b"):
    """gpt-oss-20b par call + poora error (pehle 400 char, `mask()` ke baad).
    Pehla trial wahi hai jo app bhejta hai (`brain/groq_client.py`); baaki 3 sirf
    ye dekhne ke liye hain ki 400 kis param se aata hai."""
    from gatekeeper.audit import mask
    from groq import Groq
    client = Groq(api_key=config.GROQ_API_KEY, timeout=config.BRAIN_TIMEOUT_GROQ)
    msgs = [{"role": "user", "content": "time kya hai"}]
    base = {"temperature": 0.7, "max_tokens": config.BRAIN_MAX_TOKENS}
    trials = [("app ka shape (temperature + max_tokens)", dict(base)),
              ("+ reasoning_effort=low",
               dict(base, reasoning_effort=config.BRAIN_REASONING_EFFORT)),
              ("max_tokens=5000 (retry wala)",
               dict(temperature=0.7, max_tokens=config.BRAIN_MAX_TOKENS_RETRY)),
              ("sirf messages, koi param nahi", {})]
    for label, extra in trials:
        try:
            reply = client.chat.completions.create(model=model, messages=msgs, **extra)
            text = (reply.choices[0].message.content or "").strip()
            print(ascii_only(f"OK   {label} -> {len(text)} chars"))
        except Exception as exc:
            print(ascii_only(f"FAIL {label}\n     {mask(str(exc))[:400]}"))


if __name__ == "__main__":
    wanted = [a for a in sys.argv[1:] if a.startswith("--")]
    if wanted == ["--models"]:
        audit_models()
    elif wanted == ["--show-error"]:
        show_error()
    else:
        print("usage: python tests/dryrun_llm.py --models | --show-error")
        print("bina flag: library hai - dryrun_latency2.py ise import karta hai")