"""Latency baseline probe — dryrun (suite se bahar, asli network allowed).

8 chhote commands, har ek 3 baar, teen lanes (Groq current, Groq small, Gemini).
TTS: edge-tts se 12 shabd ka jawab FILE me (speaker par KABHI nahi). STT: sirf naam.
Koi key/secret print nahi. data\\ me kuch nahi. Output %TEMP%\\latency_probe.txt me.
"""
import asyncio, os, statistics, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _load_env():
    """.env ko env vars me bharo (print nahi)."""
    try:
        for line in (Path(__file__).resolve().parent.parent / ".env").read_text("utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip().strip('"'))
    except Exception:
        pass


_load_env()

import config
from brain import prompt
from core import modes
from gatekeeper import keeper
from voice import tts_edge

COMMANDS = ["time kya hai", "chrome kholo", "notes me likho kal doodh lana hai",
            "hello", "volume badhao", "youtube kholo", "tum kaun ho",
            "desktop ki files dikhao"]
REPS, TIMEOUT = 3, 30.0
TTS_TEXT = "theek hai maine note kar liya kal doodh lana hai bhai sahab"  # 12 shabd
TEMP = Path(os.environ.get("TEMP", "."))


def groq_call(model, messages):
    """Ek Groq chat call. 429 par 5s ruko, ek retry, phir '429'."""
    from groq import Groq
    client = Groq(api_key=config.GROQ_API_KEY, timeout=TIMEOUT)
    for attempt in (1, 2):
        start = time.perf_counter()
        try:
            reply = client.chat.completions.create(
                model=model, messages=messages, temperature=0.7,
                max_tokens=config.BRAIN_MAX_TOKENS)
            ms = int((time.perf_counter() - start) * 1000)
            text = (reply.choices[0].message.content or "").strip()
            u = getattr(reply, "usage", None)
            pt = getattr(u, "prompt_tokens", None) if u else None
            ct = getattr(u, "completion_tokens", None) if u else None
            return ms, text, pt, ct
        except Exception as exc:
            slow = "429" in str(exc) or "rate" in str(exc).lower()
            if attempt == 1 and slow:
                time.sleep(5)
                continue
            return ("429" if slow else "ERR"), "", None, None
    return "429", "", None, None


def small_model():
    """Groq /models se chhota fast chat model (sabse chhota parameters)."""
    import re
    try:
        from groq import Groq
        ids = [m.id for m in Groq(api_key=config.GROQ_API_KEY,
                                   timeout=TIMEOUT).models.list().data]

        def size(m):
            hit = re.search(r"(\d+(?:\.\d+)?)b", m.lower())
            return float(hit.group(1)) if hit else 9999.0

        chat = [m for m in ids if not any(k in m.lower() for k in
                ("whisper", "tts", "guard", "safeguard", "orpheus"))]
        return sorted(chat, key=size)[0] if chat else ""
    except Exception:
        return ""


def stats(samples):
    ms = [s for s in samples if isinstance(s, int)]
    if not ms:
        return "-", "-", "-", "-"
    s = sorted(ms)
    p90 = s[min(len(s) - 1, int(0.9 * len(s)))]
    return int(statistics.median(ms)), p90, min(ms), max(ms)


async def tts_probe():
    times, out = [], TEMP / "latency_tts.mp3"
    for i in range(3):
        start = time.perf_counter()
        audio = await tts_edge.speak(TTS_TEXT, config.DEFAULT_MODE)
        times.append(int((time.perf_counter() - start) * 1000))
        if i == 0:
            out.write_bytes(audio)
    return times


def main():
    lines = []

    def out(text=""):
        print(text)
        lines.append(text)

    persona = prompt.build(modes.persona_for(config.DEFAULT_MODE), keeper.tools_on())
    out(f"system prompt: {len(persona)} chars | tools_on={keeper.tools_on()}")
    lane_b = small_model()
    out(f"Lane B model: {lane_b or '(nahi mila)'}")
    if not config.GEMINI_API_KEY or (config.DATA_DIR / "memory.json").exists():
        out("Lane C: SKIP (GEMINI key nahi / memory.json me user data hai)")
    out(f"{'command':32} {'lane':4} {'samples ms':>22}  action")
    for cmd in COMMANDS:
        for lane, model in (("A", config.GROQ_MODEL), ("B", lane_b)):
            if not model:
                continue
            samples, pt, ct = [], None, None
            for _ in range(REPS):
                ms, text, pt, ct = groq_call(
                    model, [{"role": "system", "content": persona},
                            {"role": "user", "content": cmd}])
                samples.append(ms)
                kind, _ = prompt.parse_action(text)
                out(f"{cmd:32} {lane:4} {str(samples):>22}  {kind}")
            med, p90, mn, mx = stats(samples)
            out(f"{'':32} {lane:4} median={med} p90={p90} min={mn} max={mx}"
                f" tokens p={pt} c={ct}")
    tts = asyncio.run(tts_probe())
    out(f"TTS (edge, file): {tts} median={int(statistics.median(tts))}ms"
        f" -> {TEMP / 'latency_tts.mp3'}")
    out(f"STT: {config.GROQ_STT_MODEL} (skip, sirf model naam)")
    (TEMP / "latency_probe.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
