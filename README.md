# Prabh

> **Ye ek local personal app hai, sirf is PC par chalta hai.** Ye web app nahi hai —
> doosre PC, phone ya internet se koi ise khol nahi sakta.

Do naam wala AI assistant:

- **Sunday** (public mode) — halka professional, chhote aur saaf jawab.
- **Prabh** (private mode) — pyaar se, dostana, khula Hinglish.

Browser me chalta hai, Windows 10/11 par, sab kuch free tools se.

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

2. `.env` kholo aur dono key daalo:

```
GROQ_API_KEY=apni_groq_key
GEMINI_API_KEY=apni_gemini_key
```

Key kahan se milegi:
- Groq: https://console.groq.com/keys
- Gemini: https://aistudio.google.com/apikey

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

```powershell
cd D:\prabh
.\.venv\Scripts\python.exe tests\test_basic.py
.\.venv\Scripts\python.exe tests\test_security.py
```

Aakhir me "Saare test pass." aana chahiye. Test me real API call nahi hota — key ki zarurat nahi.

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
   Token khud app ke page (`/`) me daal diya jaata hai, aur UI har `/chat` aur `/ws`
   request ke saath bhejta hai. Token galat ya missing ho to request 401 ho jaati hai.
5. **CORS band** — koi `access-control-allow-origin` header nahi jaata.

Sabse aasan: **token har restart par badal jaata hai**, isliye server band karke dobara
chalao aur page dobara kholo — token apne aap refresh ho jaayega.

### Command line se test karna ho

```powershell
cd D:\prabh
$page = Invoke-WebRequest http://localhost:8000 -UseBasicParsing
$token = [regex]::Match($page.Content, 'PRABH_TOKEN = "([^"]+)"').Groups[1].Value
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
Dayin taraf poori baat-chit rehti hai.

---

## Kaun si file kya karti hai

| File | Kaam |
|---|---|
`main.py` | Server chalu karta hai |
`config.py` | `.env` aur settings |
`log_setup.py` | `logs/prabh.log` banata hai |
`core/events.py` | `status` / `message` / `log` events |
`core/modes.py` | Naam se mode + persona file |
`core/engine.py` | Poora chat flow |
`brain/router.py` | Pehle Groq, phir Gemini |
`brain/groq_client.py` | Groq call |
`brain/gemini_client.py` | Gemini call |
`personas/sunday.txt` | Sunday ka character |
`personas/prabh.txt` | Prabh ka character |
`server/app.py` | `POST /chat` + `WebSocket /ws` |
`server/security.py` | Origin / Host / token check |
`ui/index.html`, `ui/style.css`, `ui/app.js` | Interface |
`tests/test_basic.py` | Chat, mode aur brain ke tests |
`tests/test_security.py` | Suraksha ke tests |

---

## Error kahan dekhein?

Sab kuch `logs/prabh.log` me likha jaata hai.

```powershell
Get-Content D:\prabh\logs\prabh.log -Tail 20
```

Agar browser me sirf "Abhi koi brain jawab nahi de paya" dikh raha hai, to `.env` me key
sahi hai ya nahi check karo.

---

## Baad me aane wala kaam (abhi nahi banaya)

`engine.run_tool()` ek hi raasta hai jahan har PC-kaam wala tool chalega. Baad me
usi jagah gatekeeper lagega — engine me badlav nahi hoga.