// ARC THEME — Python config ka JS saathi (KAAM B).
//
// `server/app.py` ke `fill_html()` is placeholder ko bhar deta hai, is liye
// rang/constant Python aur JS me dobara nahi likhe. Ek hi source: config_hud.py.
//
// Values HTML attribute me JSON ke roop me daali jati hain — `textContent`
// se nahi, aur raw-HTML injection KABHI nahi (AGENTS XSS niyam). Sirf humari apni
// numbers/strings hain, user ka koi input nahi.

(function () {
  "use strict";

  // Numbers/arrays JSON me aate hain (`json.dumps` server par), plain strings
// (credit, channel) seedhe. `read` JSON.parse karta hai; `readText` nahi.
function read(name, fallback) {
    const e = document.querySelector('meta[name="' + name + '"]');
    if (!e || !e.content) return fallback;
    try { return JSON.parse(e.content); } catch (err) { return fallback; }
  }

  function readText(name, fallback) {
    const e = document.querySelector('meta[name="' + name + '"]');
    return (e && e.content) || fallback;
  }

  window.PRABH_ARC_CFG = {
    accent: read("arc-accent", "#ff8a2e"),
    accent2: read("arc-accent-2", "#ff5e3a"),
    routing: read("arc-routing", ["WAKE", "STT", "BRAIN", "TTS"]),
    channel: readText("arc-channel", "LOCAL"),
    credit: readText("arc-credit", ""),
    ticks: read("arc-ticks", 72),
    hex: read("arc-hex", 6),
    activityMax: read("arc-act-max", 6),
    // ms per tick — ~30fps. CSS animations alag (GPU), ye sirf typewriter
    // aur core-number ke liye.
    typeMs: read("arc-type-ms", 28),
    frameMs: read("arc-frame-ms", 33),
  };
})();