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
  config.py          -> .env + sab settings ek jagah
  log_setup.py       -> logs/prabh.log
  core/engine.py     -> message aaya -> mode -> brain -> events
  core/events.py     -> status/message/log
  core/modes.py      -> naam se mode + persona
  brain/router.py    -> pehle Groq, fail par Gemini
  brain/groq_client.py, brain/gemini_client.py
  personas/sunday.txt, personas/prabh.txt
  server/app.py      -> FastAPI: POST /chat, WebSocket /ws
  server/security.py -> token + Origin + Host check
  server/voice_routes.py -> POST /stt, POST /tts
  voice/stt.py       -> audio -> text (Groq Whisper)
  voice/tts.py       -> chain: elevenlabs -> cartesia -> edge
  voice/tts_elevenlabs.py, voice/tts_cartesia.py, voice/tts_edge.py
  ui/index.html, style.css, app.js, recorder.js, speaker.js
  tests/test_basic.py, tests/test_security.py, tests/test_voice.py
```

- Baad ke phase (abhi mat banao): `gatekeeper/`, `tools/`, `memory/`, full voice loop.
- **Tool ka ek hi raasta**: `engine.run_tool()`. Har PC-kaam wala tool usi se guzrega,
  aur usi jagah gatekeeper lagega. Engine me naya raasta mat banao.
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
- Token browser ko `/` se milta hai (placeholder `__PRABH_TOKEN__` replace hota hai).

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
.\.venv\Scripts\python.exe tests\test_basic.py
.\.venv\Scripts\python.exe tests\test_security.py
.\.venv\Scripts\python.exe tests\test_voice.py
```

- Test me **asli API call kabhi nahi** — sab mock.
- Naya feature banao to uska test bhi banao, phir teenon chala kar confirm karo.

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

_(abhi koi nayi rule nahi)_

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
- **Keys** — `.env` me 4 asli keys lagi (Groq, Gemini, ElevenLabs, Cartesia) +
  Prabh ki ElevenLabs voice id. `.env.example` me sirf naam. `.env` git-ignore me.
- **AGENTS.md** — banaya, saare niyam ek jagah.