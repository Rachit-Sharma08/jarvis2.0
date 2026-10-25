---
name: jarvis-rules
description: Jarvis project ke pakke niyam — .env, nakli audio, 200 line, DEFAULT OFF, test, report
---

# Jarvis rules (har kaam me)

## Suraksha (sabse pehle)

- `.env` **kabhi mat kholo**. Key print/commit/log kabhi nahi.
  Confirm ke liye sirf **aakhri 4 akshar**.
- Dynamic UI text sirf `textContent` se. `innerHTML`/`eval` kabhi nahi.
- Server sirf 127.0.0.1. Naya endpoint `server/security.py` se guard karo.

## Test ke niyam

- Sab test **NAKLI** audio/mic/speaker se. `start_jarvis.bat` mat chalao,
  koi process kill mat karo, port 8000 par server nahi (8700+).
- Har badlav ke saath test. Bug-injection: fix kharab karke test fail
  hona chahiye, warna test kuch pakadta hi nahi.
- Poori suite: 6 purane fail wahi rehte hain (hisab me aata hai).

## Code ke niyam

- **Koi file 200 lines se zyada nahi** — cross karte hi split karo.
- Naye mic/awaaz features **DEFAULT OFF** (flag + test dono).
- Naya package mat lagao. PowerShell se repo ki text file mat badlo
  (UTF-8 double-encode ho jaata hai) — `edit` tool ya Python use karo.
- Ek file ka ek kaam. Pehle plan, phir code, phir test, phir commit.

## Report

Chhoti, seedhi Hinglish. Kya badla, suboot kya hai, TUMHARA KAAM kya
bacha hai. Raw dump kabhi nahi.
