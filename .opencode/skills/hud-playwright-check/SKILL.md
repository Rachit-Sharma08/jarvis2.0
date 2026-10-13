---
name: hud-playwright-check
description: HUD ko Playwright se jaanchna — headless bundled Chromium, nakli server, teen viewport, screenshot %TEMP% me
---

# HUD Playwright check

HUD ka har visual badlav **browser me verify** hota hai. Source-check se
Phase 4 me 8 asli bug chhoot gaye the — sirf asli browser me pakde gaye.

## Kadak niyam

- Sirf **headless** + apna **bundled Chromium**. Koi window nahi khulti.
- Rachit ke Chrome/Edge ka **koi user profile, cookie, ya channel nahi**.
- Sirf `http://127.0.0.1` par **apna nakli server (port 8700+)**.
  Port 8000 (asli Jarvis) kabhi mat chhuo.
- `ignoreHTTPSErrors` / `NODE_TLS_REJECT_UNAUTHORIZED=0` / certificate
  band karne wala **kuch bhi MANA**. Network error aaye to 2 min ruko,
  5 baar retry, phir ruk kar report me likho.
- Reference (`jarvis.mukh1.com`) ek-do baar **sirf dekhna** — code/CSS/SVG
  copy kabhi nahi. google.com par kabhi mat jao.

## Kaise

1. `tests/hudserve.py` ka `FakeHud` — sirf `ui/` static + 2 nakli JSON.
   Koi brain/tool nahi, `import config` nahi (`.env` chhua hi nahi).
2. Teeno viewport: **1366x768, 1280x720, 1920x1080**.
3. Screenshot `%TEMP%\opencode\hudshots` me — **repo me kabhi nahi**.
4. `getBoundingClientRect` + computed style + network log dekho.
5. Bug-injection: fix wapas kharab karke test **fail** hona chahiye,
   warna test kuch pakadta hi nahi.
