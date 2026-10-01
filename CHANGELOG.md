# Changelog (Prabh ka pura record)

`AGENTS.md` sirf **niyam** rakhta hai; kaam ka poora record yahan hai. Ek line =
ek kaam ka group. Doc ka detail `BRAIN.md`, `TOOLS.md`, `VOICE.md`, `TESTS.md`,
`ROUND2.md` me hai.

---

## Round 2 (1-2 Oct 2026) — brain pool, suraksha, voice

| Kya bana | File |
|---|---|
| Do-tier brain pool + provider order | `brain/pool.py`, `brain/pool_config.py` |
| OpenAI-compatible adapter (chat + GET models) | `brain/openai_pool.py` |
| NVIDIA pool-wide 30/min sliding window | `brain/limiter.py` |
| Cooldown/lock/quota + error-word categories | `brain/health.py`, `brain/health_words.py` |
| Manual strict-JSON probe + 24h cache | `brain/probe.py` |
| Startup par sirf free `/models` check | `brain/checkup.py` |
| `GET /brain/status` (masked) | `server/brain_routes.py` |
| Dynamic `.env` masking + `nvapi_` pattern | `gatekeeper/audit.py` |
| Dono mode female-only + female allowlist | `voice/tts_female.py`, `config_voice.py` |
| STT guard (duration/silence/script) | `voice/stt_guard.py`, `voice/stt.py` |
| `SUNDAY` / `PRABH` answer label | `core/events.py`, `core/modes.py`, `core/engine.py`, `ui/app.js` |
| Config split | `config_brain.py`, `config_voice.py` |
| UI split | `ui/voice_ui.js` |
| Docs | `TESTS.md` + BRAIN/VOICE/TOOLS/README/AGENTS update |

**Live probe (Sept-Oct 2026):**

- NVIDIA `nemotron-3-super-120b-a12b` — strict JSON **pass**, ~1.0s → winner.
- NVIDIA `nemotron-3.5-lightning-30b-a3b` — 60s+ timeout → fail.
- NVIDIA `nemotron-nano-3-30b-a3b` — **404** → pool se bahar.
- OpenRouter `nemotron-3-super-120b-a12b:free` — strict JSON **pass**, ~1.2s.
- OpenRouter `qwen3.8-27b:free` — **429**.
- NVIDIA free trial = 1000 credits; credits khatam par HTTP **402**.

**Result:** 22 suite green (`SUITE GREEN`), sab file `<200` lines.

---

## Fix round 1

- Models fix + fallback (Groq 10s / Gemini 15s, 503 par 1 retry).
- `brain/health.py` — 404 → model GONE, 402/429/503/timeout → 10 min rest.
- Startup `/models` check + warning banner.
- `core/timing.py` — stage + total timing.
- Dono brain provider fail ho to **ek hi** message.
- `rid` + UI message dedupe.
- Prabh ki awaaz female, Cartesia ka Hindi payload fix.
- `BRAIN.md` bana. 15 suite.

**Root cause (jaanch):** khaali jawab `max_tokens=800` + reasoning model — content
token me hi khatam ho jata tha. Fix: `max_tokens` 1600/3200, `reasoning_effort=low`,
aur khaali/length/ghalat JSON = failure count.

---

## Phase 3 (PC tools)

- `gatekeeper/` + `tools/` — 10 tools, Recycle Bin delete, scrubbed env.
- Strict tool JSON + duplicate-key reject.
- 5-step tool loop.
- `server/tool_routes.py` + UI (ACTIVITY panel, confirm card, `TOOLS`, `STOP`).
- Confirm card ki detail me secret masking.
- 4 badi file split.
- Docs: `TOOLS.md`, `VOICE.md`.

---

## Phase 1-2 (skeleton)

- Skeleton, brain (Groq → Gemini), personas, mode switch.
- Engine + events, FastAPI (`/chat`, `/ws`), HUD UI.
- Suraksha: 127.0.0.1 only, Origin + Host check, per-start token, CORS band.
- Voice: `stt.py`, TTS chain, `/stt` + `/tts`, mic UI, 500 char limit.
- Tests.

---

## Keys

- `.env` me 6 brain/voice keys + voice ids (values kabhi commit nahi).
- `.env.example` me sirf naam.
- `.env` git-ignored.
