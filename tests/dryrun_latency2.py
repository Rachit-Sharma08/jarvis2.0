"""Latency baseline part 2 - dryrun (suite se bahar, asli network allowed).

Suite loop sirf `tests/test_*.py` chalata hai, is liye ye `dryrun_` naam se hai.
Sirf *naapta* hai, app ka code nahi badalta. Hissa:

  a) LLM -> `dryrun_llm.py` ka `lane()` (3 model x 5 sawal x 5 baar).
  b) STT: edge-tts se ~4 s ka Hinglish clip -> app wale Groq whisper model par.
  c) TTS (edge-tts): pehla audio chunk + poori file, 3 lambai (5/15/30 shabd) x 5.
  d) Wait: config ka chup-hone ka wait sirf padh kar (naapna nahi).
  e) Andaza: bolna khatam -> pehli awaaz = wait + STT + LLM + TTS pehla chunk.

Koi key/secret print nahi. `data/` me kuch nahi likha. Speaker par kuch nahi bajta.
System prompt me `memory.MEM.context()` shaamil hai (app bilkul yahi karta hai).
Output: TEMP/latency_probe2.txt
"""
import asyncio, os, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dryrun_llm import MODELS, ascii_only, estimate, lane, stats   # ye .env load karta hai

import config                                  # noqa: E402
from brain import prompt                        # noqa: E402
from core import modes                          # noqa: E402
from gatekeeper import keeper                   # noqa: E402
from voice import stt as stt_mod                # noqa: E402

REPS, GAP = 5, 2.0
STT_TEXT = "chrome kholo aur youtube par lofi search karo"
TTS_TEXTS = {
    5: "theek hai bhai ho gaya",
    15: "ji maine ye kaam kar diya hai ab aap chahe to youtube kholu ya notes likhwaa do",
    30: "theek hai bhai maine aapka kaam kar diya hai, chrome khol kar youtube par lofi "
        "search bhi kar diya, aur kal doodh lana hai ye note bhi kar liya gaya",
}
TEMP = Path(os.environ.get("TEMP", "."))


async def make_clip():
    """edge-tts se Hinglish clip (app ki wahi hi-IN-SwaraNeural voice)."""
    import edge_tts
    speaker = edge_tts.Communicate(STT_TEXT, config.EDGE_VOICES[config.DEFAULT_MODE])
    data = bytearray()
    async for chunk in speaker.stream():
        if chunk["type"] == "audio":
            data.extend(chunk["data"])
    return bytes(data)


def clip_seconds(audio):
    """Clip ki asli lambai second me (miniaudio decode, koi speaker nahi)."""
    import miniaudio, numpy as np
    dec = miniaudio.decode(audio, output_format=miniaudio.SampleFormat.SIGNED16,
                           nchannels=1, sample_rate=16000)
    return round(len(np.asarray(dec.samples, dtype="<i2")) / 16000, 2)


def _transcribe_named(audio, name):
    """App ke `_transcribe` jaisa, par filename alag (mp3 bytes webm naam par
    fail ho sakte hain - Groq filename se format pehchanta hai)."""
    import io
    from groq import Groq
    client = Groq(api_key=config.GROQ_API_KEY, timeout=config.BRAIN_TIMEOUT_GROQ)
    reply = client.audio.transcriptions.create(
        file=(name, io.BytesIO(audio)), model=config.GROQ_STT_MODEL)
    return (reply.text or "").strip()


def stt_probe(audio, out):
    """App ka STT raasta (config.GROQ_STT_MODEL + app timeout), 5 baar."""
    samples, bad, used, text = [], [], "app (mic.webm)", ""
    for i in range(REPS):
        start = time.perf_counter()
        try:
            text = (stt_mod._transcribe(audio) if used.startswith("app")
                    else _transcribe_named(audio, "mic.mp3"))
            samples.append(int((time.perf_counter() - start) * 1000))
        except Exception as exc:
            if used.startswith("app") and i == 0:
                used = "seedha (mic.mp3)"        # webm naam par mp3 bytes nahi chale
                continue
            bad.append(str(exc)[:60])
        time.sleep(GAP)
    out(f"  raasta: {used} | suna: {text!r}")
    n, med, p90, mn, mx = stats(samples)
    out(f"  {config.GROQ_STT_MODEL}: n={n} median={med} p90={p90} min={mn}"
        f" max={mx} ms" + (f" | gine: {len(bad)} {bad[:2]}" if bad else ""))
    return med


async def tts_lane(out):
    """3 lambai x 5: pehla audio chunk, aur poori file. -> {shabd: median}"""
    import edge_tts
    voice = config.EDGE_VOICES[config.DEFAULT_MODE]
    firsts = {}
    for words, text in TTS_TEXTS.items():
        first, total = [], []
        for _ in range(REPS):
            start = time.perf_counter()
            t0, data = None, bytearray()
            speaker = edge_tts.Communicate(text, voice)
            async for chunk in speaker.stream():
                if chunk["type"] == "audio":
                    t0 = t0 or time.perf_counter()
                    data.extend(chunk["data"])
            first.append(int(((t0 or time.perf_counter()) - start) * 1000))
            total.append(int((time.perf_counter() - start) * 1000))
            await asyncio.sleep(1.0)
        n, med, p90, mn, mx = stats(first)
        out(f"  {words:2d} shabd ({len(text.split())} actual): pehla chunk"
            f" n={n} median={med} p90={p90} min={mn} max={mx} ms |"
            f" poori file median={int(sorted(total)[len(total) // 2])} ms"
            f" ({len(data)} bytes)")
        firsts[words] = med
    return firsts


def wait_config():
    """Config se chup-hone ka wait sirf PADH kar (naapna nahi)."""
    block = config.BLOCK_MS / 1000.0
    hang = round(config.COMMAND_HANGOVER_SECONDS / block)
    quiet = round(config.COMMAND_END_SILENCE_SECONDS / block)
    return {"blocks": (hang, quiet), "ms": int((hang + quiet) * config.BLOCK_MS)}


def ascii_only(text):
    """Console cp1252 hai - Devanagari/emoji se crash na ho. File UTF-8 me asli."""
    return text.encode("cp1252", "replace").decode("cp1252")


def main():
    lines = []

    def out(text=""):
        lines.append(text)
        # Har step par likh do - beech me crash ho to bhi aadha result bache.
        (TEMP / "latency_probe2.txt").write_text("\n".join(lines) + "\n",
                                                 encoding="utf-8")
        print(ascii_only(text))

    persona = prompt.build(modes.persona_for(config.DEFAULT_MODE), keeper.tools_on())
    out(f"system prompt: {len(persona)} chars | tools_on={keeper.tools_on()}")
    out(f"app: groq timeout={config.BRAIN_TIMEOUT_GROQ}s"
        f" gemini timeout={config.BRAIN_TIMEOUT_GEMINI}s"
        f" max_tokens={config.BRAIN_MAX_TOKENS}")

    out("")
    out("a) LLM (Groq, 5 sawal x 5 baar, beech me 2 s)")
    llm_med = {}
    for model in MODELS:
        llm_med[model] = lane(model, persona, out)[0]
        time.sleep(GAP)

    out("")
    out("b) STT (app wala Groq whisper model)")
    audio = asyncio.run(make_clip())
    out(f"  clip: {len(audio)} bytes, {clip_seconds(audio)} s | text: {STT_TEXT!r}")
    stt_med = stt_probe(audio, out)

    out("")
    out("c) TTS (edge-tts streaming, 5 baar)")
    tts_first = asyncio.run(tts_lane(out))

    out("")
    out("d) chup-hone ka wait (config se padha)")
    w = wait_config()
    out(f"  JARVIS_CMD_SILENCE end_silence={config.COMMAND_END_SILENCE_SECONDS}s"
        f" ({w['blocks'][1]} block) + hangover={config.COMMAND_HANGOVER_SECONDS}s"
        f" ({w['blocks'][0]} block) = {w['ms']} ms")
    out(f"  baaki: pre_roll={config.COMMAND_PRE_ROLL_SECONDS}s"
        f" warmup={config.COMMAND_WARMUP_SECONDS}s"
        f" peek={config.COMMAND_ACK_PEEK_SECONDS}s"
        f" wait={config.COMMAND_WAIT_SECONDS}s"
        f" min={config.COMMAND_MIN_SECONDS}s"
        f" max={config.COMMAND_MAX_SECONDS}s")

    out("")
    estimate(w, stt_med, llm_med, tts_first, out)


if __name__ == "__main__":
    main()