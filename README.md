# Prabh

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
```

Saare "OK" aa jaye to test pass. Test me real API call nahi hota — key ki zarurat nahi.

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
`ui/index.html`, `ui/style.css`, `ui/app.js` | Interface |
`tests/test_basic.py` | Tests |

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