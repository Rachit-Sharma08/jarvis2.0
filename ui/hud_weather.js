// WEATHER panel: ardh-gol temperature gauge + bada temp + condition + sheher.
//
// Data SIRF server se aata hai (/hud/weather → Open-Meteo, 15 min cache).
// Browser kabhi bahar site ko call NAHI karta — CSP bhi connect-src 'self'
// se ye rok deta hai. Data na ho to "No data" + hint dikhta hai.
//
// Har text `textContent` se. Koi markup banane wala API nahi.

(function () {
  const tempEl = document.getElementById("wxTemp");
  const condEl = document.getElementById("wxCond");
  const cityEl = document.getElementById("wxCity");
  const hintEl = document.getElementById("wxHint");
  const arcEl = document.getElementById("tempArc");
  if (!tempEl) return;

  const TOKEN = (document.querySelector('meta[name="jarvis-token"]') || {}).content || "";
  const ARC = 151;                 // ardh-gol gauge ki perimeter
  const RETRY_MS = 10 * 60 * 1000; // fail par 10 min baad phir try

  function setArc(percent) {
    let pct = Number(percent) || 0;
    pct = Math.max(0, Math.min(100, pct));
    arcEl.style.strokeDashoffset = String(ARC * (1 - pct / 100));
    arcEl.classList.remove("warm", "cold");
    if (pct >= 65) arcEl.classList.add("warm");       // 12°C+ -> ember
    else if (pct <= 30) arcEl.classList.add("cold");  // -5°C-  -> gold-hot
  }

  function render(data) {
    if (!data) return;

    // Shehar server se hi — config ka naam browser me hard-code nahi.
    cityEl.textContent = data.city || "";

    if (!data.ok || data.temp === null || data.temp === undefined) {
      tempEl.textContent = "--°";
      condEl.textContent = "No data";
      setArc(0);
      hintEl.textContent = data.hint || "";
      return;
    }

    const temp = Number(data.temp);
    tempEl.textContent = Math.round(temp) + "°";
    condEl.textContent = data.condition || "";

    // H/L chhoti line me — gauge ke neeche
    let extra = "";
    if (data.high !== null && data.low !== null && data.high !== undefined) {
      extra = Math.round(Number(data.low)) + "° / " + Math.round(Number(data.high)) + "°";
      if (data.humidity !== null && data.humidity !== undefined) {
        extra += "  ·  " + Math.round(Number(data.humidity)) + "% RH";
      }
    }
    hintEl.textContent = extra;
    setArc(data.temp_percent);
  }

  async function load(force) {
    try {
      const reply = await fetch("/hud/weather", {
        headers: { "x-jarvis-token": TOKEN },
        cache: "no-store"
      });
      if (!reply.ok) throw new Error("http " + reply.status);
      render(await reply.json());
    } catch (err) {
      // Server band ya network nahi — panel ko "No data" hi rehne do.
      render({ ok: false, city: cityEl.textContent, hint: "Server se weather nahi mila." });
      setTimeout(() => load(true), RETRY_MS);
    }
  }

  // Load par ek baar, phir har 15 min (server cache bhi 15 min hai).
  load(true);
  setInterval(() => load(true), 15 * 60 * 1000);

  window.JARVIS_WEATHER = { render: render, load: load };
})();
