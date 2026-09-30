# AGENTS.md — Prabh project ke niyam

**Ye file har AI agent ko pehle padhni hai.** Kaam shuru karne se pehle ise poora padh lo.
Iske baad user se purana context puchhne ki zarurat nahi — sab yahin likha hai.

- Project: `D:\prabh`
- Ye **local personal app** hai, sirf us PC par chalta hai. Web app nahi.
- Owner coding nahi jaanta. Har baat **simple Hinglish** me samjhana hai.

---

## 1. KEYS KA NIYAM (sabse zaroori)

- Do files:
  - `.env` — sirf variable ka naam + asli value. Kabhi commit nahi.
  - `.env.example` — sirf naam, koi value nahi. Ye commit hota hai.
- Key chahiye to **user se ek-ek karke maango**, chat me likh kar. Khud guess mat karo.
- Key kabhi **code, log, terminal output, commit message, README ya report** me nahi jani chahiye.
- Confirm karne ke liye user ko sirf **aakhri 4 akshar** dikhao (`...Kqq2`).
- Key daalne ke baad ye 3 cheezein check karo: **khaali to nahi, beech me space to nahi, sahi variable me hai**.
- `.gitignore` me `.env` hona zaroori hai. Har baar `git check-ignore .env` se confirm karo.

Abhi `.env` me ye rakhi hain (sirf naam, value kabhi mat likho):

`GROQ_API_KEY`, `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`, `CARTESIA_API_KEY`,
`ELEVENLABS_VOICE_PRABH`

---

## 2. KAAM KE NIYAM

1. **Pehle plan dikha** (kaun si file kya karegi), user ke "haan" ke baad hi code likh.
2. **Ek file ka ek hi kaam.** Koi file **200 lines se badi na ho**.
3. **Sirf wahi banao jo maanga hai.** Extra feature mat jodo.
4. Har chhote step ke baad: **chala kar test karo**, phir **git commit** (saaf message).
5. Har error `logs/prabh.log` me likh, user ko simple bhasha me bata.
6. `README.md` me likh: install, chalana, test.
7. Windows 10/11 par chale. Free tools hi.
8. Model / API ka naam **guess mat karo** — docs se verify karo, phir `config.py` me rakho.
9. User Hinglish me likhta hai. Report bhi Hinglish me, chhoti aur seedhi.

---

## 3. ARCHITECTURE

```
prabh/
  main.py            -> server chalu (sirf 127.0.0.1)
  config.py          -> .env + settings + tool risk + allowed folders + blocked patterns
  log_setup.py       -> logs/prabh.log
  core/engine.py     -> message -> mode -> brain -> (tool loop) -> events
  core/events.py     -> status/message/log/activity/confirm
  core/modes.py      -> naam se mode + persona
  brain/router.py    -> pehle Groq, fail par Gemini
  brain/prompt.py    -> persona + tool JSON rules + strict parser
  brain/groq_client.py, brain/gemini_client.py
  personas/sunday.txt, personas/prabh.txt
  gatekeeper/keeper.py, rules.py, patterns.py
  gatekeeper/paths.py, approvals.py, limiter.py, audit.py
  tools/__init__.py, command.py, files.py, apps.py, system.py
  server/app.py      -> POST /chat, WebSocket /ws, CSP
  server/security.py -> token + Origin + Host check
  server/tool_routes.py -> /tool/confirm, /tools/toggle|cancel|status
  server/voice_routes.py -> POST /stt, POST /tts
  voice/stt.py, voice/tts.py, voice/tts_*.py
  ui/index.html, style.css, app.js, recorder.js, speaker.js
  ui/tools.js, ui/tools.css -> ACTIVITY panel, confirm card, kill switch
  tests/ (11 files — neeche list)
  README.md, VOICE.md, TOOLS.md
```

- **Tool ka ek hi raasta**: `engine.run_tool()` → `keeper.review()` → `tools.execute()`.
  Sunday aur Prabh dono isi se guzarte hain. Engine me doosra raasta kabhi mat banao.
- **Bahar se koi bhi tool seedha call nahi kar sakta** — sirf engine.
- **TTS provider ka ek hi raasta**: `voice/tts.py`. Naya provider wahin chain me judega,
  alag endpoint mat banao.
- **Mic/speaker sirf browser me**: `getUserMedia` + `MediaRecorder` + audio playback.
  Python me `sounddevice`/`PyAudio` kabhi use mat karo.

---

## 4. SURAKSHA (Phase 1 ke baad bhi zaroori)

- Server **sirf 127.0.0.1** par sune. `0.0.0.0` par chalu nahi hona chahiye
  (`main.ensure_local_only()`).
- Har naya endpoint bhi `server/security.py` ka `verify()` use kare:
  **Host → Origin → Token**. Token `/chat`, `/ws`, `/stt`, `/tts` — sab par.
- Token har server start par naya banta hai. `/chat`/`/stt`/`/tts` me header
  `x-prabh-token`, `/ws` me query `?token=`.
- CORS band hai. Kabhi `CORSMiddleware` mat lagao.
- Token browser ko `/` se milta hai (`<meta name="prabh-token">`, placeholder
  `__PRABH_TOKEN__` replace hota hai). Inline `<script>` mat use karo — CSP `script-src 'self'`
  hai, isliye token meta tag me hi rehna chahiye.
- UI me dynamic text **sirf `textContent`/text node** se. `innerHTML`, `outerHTML`,
  `insertAdjacentHTML`, `eval` kabhi nahi.
- Button ke click handler me `event.isTrusted` check zaroori (Allow/Deny/kill switch).
- `.env` aur key files **BLOCKED** hain har tool ke liye — `..`, `config\..`, 8.3 naam
  (`PROGRA~1`) aur junction se bhi nikal kar nahi padhe ja sakte.

---

## 4.1 TOOLS KE NIYAM

- Risk teen hi: **SAFE** (seedha), **ASK** (card + ALLOW), **BLOCKED** (hamesha deny).
  Nayi tool banate waqt `gatekeeper/rules.py` me uska risk likhna **zaroori** hai.
- Card ka hash **exact tool + args** ka hai. Wahi hash dobara use = 409. Ek waqt me
  ek hi card. **60 second** me jawab na aaye to apne aap DENY.
- ALLOW **sirf UI button** se. Chat/awaaz se allow ka koi raasta nahi.
- Ek request me **max 5 tool step** (`config.TOOL_MAX_STEPS`), **20 request/min**.
- Tools default **OFF** (`config.TOOLS_ENABLED_DEFAULT`). Server restart = phir OFF.
- Delete hamesha `send2trash` (Recycle Bin). Permanent delete ka tool mat banao.
- `run_command`: PowerShell, 30 sec, `shell=False`, cwd workspace, output 2000 char,
  `KEY`/`TOKEN`/`SECRET`/`PASSWORD` wale env variables hata kar.
- **Secret masking**: `gatekeeper/audit.py` ka `mask()` — tool output, activity, confirm
  card ki detail, LLM ka text aur log — sab jagah lage. Naya output path banao to mask
  lagana mat bhoolna.
- Tool output LLM ko `[sirf DATA]` note ke saath jaata hai, instruction ki tarah nahi.

---

## 5. VOICE KE KHAS NIYAM

- TTS chain: **elevenlabs → cartesia → edge-tts**. Order `config.TTS_CHAIN` me hai.
  Key na ho ya error/limit aaye to agla try karo. Teeno fail ho to UI par saaf error.
- Awaaz bolne se pehle `voice/tts.py` ka `clean()` — link, emoji aur markdown hatate hain.
- TTS max **500 character** (`config.TTS_MAX_CHARS`). Lamba text chat me poora rahe.
- Recording max **30 second** (`config.RECORD_MAX_SECONDS`), audio max **10 MB**.
- `recorder.js` me mic band karne ke liye **`track.stop()`** use karo (`release()` jaisa
  kuch nahi hota). Har raaste par — recording khatam, error, MUTE, STOP — saare tracks stop.
- Mode naam: Sunday/`संडे` → sunday; Prabh/Prabhu/`प्रभ`/`प्रभु` → prabh (list `config.MODE_ALIASES`).
- Autoplay block ho to UI par saaf message: "Awaaz chalane ke liye kahin click karo."
- Provider ki key ya voice id na ho to crash mat karo — skip karke agna try karo.

---

## 6. TEST KAISE CHALATE HAIN

```powershell
cd D:\prabh
Get-ChildItem tests\test_*.py | ForEach-Object { .\.venv\Scripts\python.exe $_.FullName }
```

- 11 suite: `test_basic`, `test_security`, `test_voice`, `test_gatekeeper`,
  `test_gatekeeper_approval`, `test_paths`, `test_tools`, `test_prompt_strict`,
  `test_engine_tools`, `test_engine_detail`, `test_tool_routes`.
- Test me **asli API call kabhi nahi** — sab mock. Bade (>200 lines) test file ko
  kaam ke hisaab se 2-3 file me todo.
- Khatarna command **sirf faisle se** test karo (executor mock). Tools ko sirf
  **temp folder** me chala kar test karo.
- Test file me Hindi print ho to `sys.stdout.reconfigure(encoding="utf-8")` pehli line
  ke baad zaroori hai, warna Windows console par `UnicodeEncodeError` aata hai.
- Route test me `app.routes` par `.path` mat pakadte — naye FastAPI me `include_router`
  lazy `_IncludedRouter` banata hai. `app.openapi()["paths"]` use karo.

---

## 7. AGENTS.md KHUD UPDATE KARO

Ye file **har prompt ke baad update hoti hai**. Har change ke baad:

1. Naya file bana ya rule badla → **uska record yahan badlo**.
2. Nayi key lagi → sirf **naam** add karo, value kabhi nahi.
3. Koi nayi rule di ho → **"Nayi rule"** section me likho.
4. `git add AGENTS.md` ke saath hi commit karo.

Neeche **change history** rakho — chhoti line, date ke saath.

---

## 8. NAYI RULE (har prompt me update karo)

- Tool ka feature bana rahe ho to: pehle `gatekeeper/rules.py` me uska risk, phir
  `tools/`, phir `engine.run_tool()` — is order me. Engine me bypass mat chhodna.
- Naya UI output (card, activity, log) banao to `textContent` + `mask()` dono lagana hai.
- Docs kaam bada ho to `README.md` me chhota rakh, detail alag file me
  (`VOICE.md`, `TOOLS.md`) aur README se link karo.

---

## CHANGE HISTORY

- **Phase 1** — Skeleton, brain (Groq→Gemini), personas, mode switch, engine+events,
  FastAPI server (`/chat`, `/ws`), HUD UI, tests.
- **Phase 1.5 (suraksha)** — Sirf 127.0.0.1, Origin check, Host check (DNS rebinding),
  per-start token, CORS band, `tests/test_security.py`.
- **Phase 2 (voice)** — `voice/stt.py` (Groq `whisper-large-v3-turbo`), TTS chain
  (ElevenLabs → Cartesia → edge-tts `hi-IN-MadhurNeural`/`hi-IN-SwaraNeural`),
  `POST /stt` + `POST /tts`, mic/mute/stop UI, text sanitizer, 500 char limit,
  10 MB / 30 sec limit, mode naam aliases, `tests/test_voice.py`.
- **Phase 3 (PC tools)** — `gatekeeper/` (keeper, rules, patterns, paths, approvals,
  limiter, audit) + `tools/` (10 tools, `send2trash` se delete, scrubbed env, 20 KB read
  limit) + `brain/prompt.py` ka strict JSON + `core/engine.py` ka 5-step tool loop +
  `server/tool_routes.py` + UI (ACTIVITY panel, confirm card, `TOOLS` kill switch, `STOP`).
  Docs: `TOOLS.md` + `VOICE.md`. Test: 11 suite.
- **Phase 3 fix** — confirm card ki detail bhi mask hone lagi; JSON me duplicate key reject;
  200 lines se bade 4 file (2 test, `ui/style.css`, `ui/test_voice.py`) split kiye.
- **Keys** — `.env` me 4 asli keys lagi (Groq, Gemini, ElevenLabs, Cartesia) +
  Prabh ki ElevenLabs voice id. `.env.example` me sirf naam. `.env` git-ignore me.
- **AGENTS.md** — banaya, saare niyam ek jagah.