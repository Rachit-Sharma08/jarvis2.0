# Prabh

> **Ye ek local personal app hai, sirf is PC par chalta hai.** Ye web app nahi hai —
> doosre PC, phone ya internet se koi ise khol nahi sakta.

Do naam wala AI assistant:

- **Sunday** (public mode) — halka professional, chhote aur saaf jawab.
- **Prabh** (private mode) — pyaar se, dostana, khula Hinglish.

Browser me chalta hai, Windows 10/11 par, sab kuch free tools se. Mic se baat kar sakta
hai aur PC ke kaam bhi kar sakta hai (file, folder, app, command) — har kaam ke pehle
screen par confirm card aata hai.

- Awaaz ke liye → [VOICE.md](VOICE.md)
- Brain (models, fallback, error) ke liye → [BRAIN.md](BRAIN.md)
- PC ke kaam ke liye → [TOOLS.md](TOOLS.md)

---

## 1. Install (ek hi baar)

PowerShell me `D:\prabh` jao:

```powershell
cd D:\prabh
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### API keys daalo

1. `.env.example` ko copy karke `.env` banao (agar `.env` pehle se hai to skip):

```powershell
Copy-Item .env.example .env
```

2. `.env` kholo aur keys daalo:

```
GROQ_API_KEY=apni_groq_key
GEMINI_API_KEY=apni_gemini_key

ELEVENLABS_API_KEY=
CARTESIA_API_KEY=
ELEVENLABS_VOICE_SUNDAY=
ELEVENLABS_VOICE_PRABH=
CARTESIA_VOICE_SUNDAY=
CARTESIA_VOICE_PRABH=
```

Sirf `GROQ_API_KEY` zaruri hai (chat + mic dono). Baaki sab optional hain.
Key kahan se milegi: Groq https://console.groq.com/keys ·
Gemini https://aistudio.google.com/apikey ·
ElevenLabs https://elevenlabs.io/app/developers/api-keys ·
Cartesia https://cartesia.ai/dashboard

> Key kabhi code ya chat me mat likho. `.env` git-ignore hai, wo kabhi commit nahi hoga.

---

## 2. Chalao

```powershell
cd D:\prabh
.\.venv\Scripts\python.exe main.py
```

Browser me kholo: **http://localhost:8000**

Band karne ke liye terminal me `Ctrl + C`.

---

## 3. Test

Saare suites ek loop me:

```powershell
cd D:\prabh
Get-ChildItem tests\test_*.py | ForEach-Object { .\.venv\Scripts\python.exe $_.FullName }
```

Ek-ek karke bhi chal sakte ho:

```powershell
.\.venv\Scripts\python.exe tests\test_gatekeeper.py
.\.venv\Scripts\python.exe tests\test_tools.py
.\.venv\Scripts\python.exe tests\test_tool_routes.py
```

| Test file | Kya check karta hai |
|---|---|
`test_basic.py` | Chat, mode switching, brain, logging |
`test_security.py` | Token, origin, host, dangerous endpoints |
`test_voice.py` | Voice chain, limit, mode naam, `/stt` `/tts` |
`test_gatekeeper.py` | 40+ SAFE/ASK/BLOCKED cases, path tricks, mode parity |
`test_gatekeeper_approval.py` | Card hash, single use, 60s timeout, kill switch, rate limit, log masking |
`test_paths.py` | Traversal, case, 8.3 naam, junction, drive root |
`test_tools.py` | 10 tools (temp folder me), 20 KB limit, scrubbed env, timeout |
`test_prompt_strict.py` | LLM JSON strict validation + duplicate key reject |
`test_engine_tools.py` | 5-step loop, ASK/BLOCKED, kill switch, mode parity |
`test_engine_detail.py` | Tool output aur confirm card ki masking |
`test_tool_routes.py` | Tool endpoints, CSP, UI source safety |
Aakhir me "OK" / "Saare test pass." aana chahiye. Test me real API call nahi hota aur koi
khatarna command bhi nahi chalti — key ki zarurat nahi.

---

## Suraksha (sirf local)

Ye app bahar se bilkul band hai:

1. **Sirf 127.0.0.1 par suna** — `0.0.0.0` par server chalu hi nahi hoga
   (`main.py` me guard hai).
2. **Origin check** — sirf `http://localhost:8000` aur `http://127.0.0.1:8000` se aane
   wale request chalenge. Koi doosri website (`https://evil.com`) se kuch nahi hoga.
3. **Host header check** — sirf `localhost:8000` / `127.0.0.1:8000`. Isse koi fake
   domain (DNS rebinding) app ko apna nahi dikha sakta.
4. **Token** — server har baar start hone par ek naya random token banata hai.
   Token page ke `<meta name="prabh-token">` me daal diya jaata hai, aur UI har request
   ke saath bhejta hai. Token galat ya missing ho to request 401 ho jaati hai.
5. **CORS band** — koi `access-control-allow-origin` header nahi jaata.
6. **CSP header** — page par sirf apna hi code chal sakta hai (inline script band).
7. **PC tools** — har tool gatekeeper se guzarta hai; badlav-wale kaam bina ALLOW ke
   nahi hote, aur `.env`/key files hamesha BLOCKED. Details [TOOLS.md](TOOLS.md) me.

Sabse aasan: **token har restart par badal jaata hai**, isliye server band karke dobara
chalao aur page dobara kholo — token apne aap refresh ho jaayega.

### Command line se test karna ho

```powershell
cd D:\prabh
$page = Invoke-WebRequest http://localhost:8000 -UseBasicParsing
$token = [regex]::Match($page.Content, 'name="prabh-token" content="([^"]+)"').Groups[1].Value
Invoke-RestMethod http://localhost:8000/chat -Method Post `
  -Headers @{ Origin = "http://localhost:8000"; "x-prabh-token" = $token } `
  -ContentType "application/json" -Body '{"text":"Sunday, hi"}'
```

---

## Kaise use karna hai

Command box me likho aur **SEND** dabao (ya Enter).

- Mode badalne ke liye message ke **shuru me** naam likho:
  - `Sunday, ek hafta ka plan bana` → Sunday mode
  - `Prabh, aaj mood kharab hai` → Prabh mode
- Jaise hi ek naam likhoge, mode badal jayega aur wahi rehta rahega jab tak doosra naam na likho.
- Default mode **Sunday** hai.

Beeche me gol orb aur uske neeche status dikhta hai: `IDLE` -> `THINKING` -> `SPEAKING` -> `IDLE`.
Dayin taraf poori baat-chit rehti hai, neeche **ACTIVITY** box me har tool ka hisaab.

---

## Kaun si file kya karti hai

| File | Kaam |
|---|---|
`main.py` | Server chalu karta hai |
`config.py` | `.env`, settings, tool risk, allowed folders, blocked patterns |
`log_setup.py` | `logs/prabh.log` banata hai |
`core/events.py` | `status` / `message` / `log` / `activity` / `confirm` events |
`core/modes.py` | Naam se mode + persona file |
`core/engine.py` | Poora chat flow + tool loop (**sirf** `run_tool` raasta) |
`brain/router.py` | Pehle Groq, phir Gemini — dono fail ho to ek hi message |
`brain/prompt.py` | Persona + tool JSON rules + strict parser |
`brain/groq_client.py`, `brain/gemini_client.py` | Brain API calls |
`gatekeeper/keeper.py` | Har tool ka faisla + card ka intezaar |
`gatekeeper/rules.py`, `patterns.py` | Risk + khatarna command regex |
`gatekeeper/paths.py` | Traversal, symlink, 8.3, protected root jaanch |
`gatekeeper/approvals.py`, `limiter.py`, `audit.py` | Card hash, kill switch, masked log |
`tools/*.py` | 10 tools ka asal kaam |
`server/app.py` | `POST /chat` + `WebSocket /ws` + CSP |
`server/security.py` | Host + Origin + token check |
`server/tool_routes.py` | `/tool/confirm`, `/tools/toggle`, `/tools/cancel`, `/tools/status` |
`server/voice_routes.py` | `POST /stt` + `POST /tts` |
`voice/*.py` | STT/TTS providers (details [VOICE.md](VOICE.md)) |
`ui/index.html`, `ui/style.css`, `ui/app.js` | Interface |
`ui/tools.js`, `ui/tools.css` | ACTIVITY panel, confirm card, kill switch |
`ui/recorder.js`, `ui/speaker.js` | Mic record + audio playback |
`personas/sunday.txt`, `personas/prabh.txt` | Dono ka character |

---

## Error kahan dekhein?

Sab kuch `logs/prabh.log` me likha jaata hai — har brain call ka timing bhi (`groq=1.4s total=1.5s`). Har tool ka hisaab `logs/actions.log` me.

```powershell
Get-Content D:\prabh\logs\prabh.log -Tail 20
Get-Content D:\prabh\logs\actions.log -Tail 20
```

Agar browser me sirf "Abhi koi brain jawab nahi de paya" dikh raha hai, to `.env` me key
sahi hai ya nahi check karo — model list ka live check [BRAIN.md](BRAIN.md) me hai.