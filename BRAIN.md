# Brain (sochne wala)

Brain ke liye do provider hain — **pehle Groq, phir Gemini**. Har provider ke andar
models ki ek list hai, to ek model fail ho to agla model usi provider me try hota hai.

## Models

| Model | Role | Timeout |
|---|---|---|
| `openai/gpt-oss-120b` (Groq) | Pehla choice | 10s |
| `openai/gpt-oss-20b` (Groq) | Groq ka dusra | 10s |
| `gemini-3.5-flash` | Groq ke baad | 15s |
| `gemini-flash-latest` | Gemini ka dusra | 15s |

List `config.py` me `GROQ_MODELS` aur `GEMINI_MODELS` me hai. Naam live list endpoint se
verify kiye gaye hain — list badalne se pehle wahi check dobara chala lena.

## Server start par check

`brain/checkup.py` server start hote hi dono providers ki **model list** ek baar dekh
leta hai (`GET /models`). Isme **koi token nahi lagta** — na chat, na generation.

- Jo model list me mil gaya → theek.
- Jo model list me nahi mila → wo model **hamesha ke liye hata** diya jaata hai
  (`model X hata diya gaya`), aur screen par upar chhota warning bar aata hai.
- Agar list hi nahi mili (internet/network) → koi model hata nahi jata, sirf log me
  likha jaata hai. Server chalu rehta hai.

Warning bar tab dikhta hai jab model sach me galat ho — sab theek ho to kuch nahi dikhta.

## Error par kya hota hai

| Kya mila | Kya hoga |
|---|---|
| `404` / `model_not_found` | Wo model **is server session me hamesha ke liye hat** jaata hai. Agli baar dobara try nahi hoga. |
| `402` / `429` / `503` | Wo provider **10 minute ke liye rest** par chala jaata hai (`600` second). Tab tak dusra provider chalta hai. |
| Timeout / `504` | Gemini par bhi 10 minute ka rest, taaki har message par 15s na ruke. |
| `503` (Gemini) | Ek baar turant retry, phir rest. |

Rest ki wajah se har request par wahi galti dobara nahi aati. `health.blocked_reason()`
me time bacha hua seconds bhi aata hai:

```
gemini 2 min 41s rest par (503)
```

## Dono fail hon to

Ek hi message aata hai — dono providers ki galti aur har model ki wajah, saath me:

```
Abhi koi brain jawab nahi de paya.

groq: 401 invalid api key
gemini: 503 The model is overloaded
model openai/gpt-oss-120b hata diya gaya (404)
gemini 2 min 41s rest par (503)
```

## Tools band ho to

Tools ON hone par poora tool JSON spec prompt me jaata hai. Tools OFF par sirf persona
+ ek chhoti line (`tools BAND hain, koi command mat bolo`) — isse har message ka token
bachta hai. Server par real ON/OFF `/tools/status` se badalta hai.

## Timing log

Har brain call ka log `logs/prabh.log` me:

```
brain rid=r-abc provider=groq model=openai/gpt-oss-120b chars=412 ms=1402 total_ms=1451
```

`ms` = us model ka wait, `total_ms` = poora brain (saare models + providers).

## Model list live check

Ye chala kar khud dekh sakte ho (key `.env` se uthegi):

```powershell
cd D:\prabh
.\.venv\Scripts\python.exe -c "from brain import checkup; print(checkup.run())"
```

`{'problems': [], 'missing': []}` ka matlab sab models sahi hain.
