// CENTER ka orb: bahar fine tick-marks, segmented ring, gold progress arc,
// dotted ring, aur beech ka donut core (golden plasma sphere ke andar).
// State (idle/listening/thinking/speaking) wrap + orb par class lagata hai —
// animation pure CSS me hai (hud_center.css).
//
// Progress arc: gold, neeche-daayin se. `setProgress(0..1)` se chalti hai —
// brain ka sochne ka time ya koi loading dikhane ke liye. Har text textContent.

(function () {
  const wrap = document.getElementById("orbwrap");
  const modeEl = document.getElementById("orbMode");
  const stateEl = document.getElementById("orbState");
  const lineEl = document.getElementById("orbLine");
  if (!wrap) return;

  const SVG_NS = "http://www.w3.org/2000/svg";
  const TICKS = 72;              // bahar kitne fine tick-marks
  const R_OUTER = 152;
  const PROG_C = 666;            // 2 * pi * 106
  const STATES = ["idle", "listening", "transcribing", "thinking", "speaking"];
  const STATE_TEXT = {
    idle: "READY",
    listening: "LISTENING",
    transcribing: "HEARING YOU",
    thinking: "THINKING",
    speaking: "SPEAKING"
  };

  // ---- bahar wale tick-marks ek baar banao ----
  function buildTicks() {
    const group = document.getElementById("ringOuter");
    if (!group || group.childNodes.length) return;
    for (let i = 0; i < TICKS; i += 1) {
      // har 6th tick lamba = badi degree
      const major = i % 6 === 0;
      const angle = (i / TICKS) * Math.PI * 2;
      const inner = R_OUTER - (major ? 13 : 7);
      const line = document.createElementNS(SVG_NS, "line");
      line.setAttribute("class", major ? "tick major" : "tick");
      line.setAttribute("x1", String(160 + inner * Math.cos(angle)));
      line.setAttribute("y1", String(160 + inner * Math.sin(angle)));
      line.setAttribute("x2", String(160 + R_OUTER * Math.cos(angle)));
      line.setAttribute("y2", String(160 + R_OUTER * Math.sin(angle)));
      group.appendChild(line);
    }
  }

  // ---- state class ----
  function setState(value) {
    let key = String(value || "idle").toLowerCase();
    // CSS me transcribing ke liye alag animation nahi — wahi listening.
    if (key === "transcribing") key = "listening";
    if (STATES.indexOf(key) === -1) key = "idle";

    for (const name of STATES) wrap.classList.remove(name);
    wrap.classList.add(key);
    const orb = document.getElementById("orb");
    if (orb) {
      orb.className.baseVal = (orb.className.baseVal || "").replace(/\b(idle|listening|transcribing|thinking|speaking)\b/g, "");
      orb.classList.add(key);
    }
    stateEl.textContent = STATE_TEXT[key] || STATE_TEXT.idle;
  }

  function setMode(mode) {
  // Server `label()` ka naam bhejta hai ("JARVIS"). Agar kabhi sirf mode id
  // ("sunday") mile to usse bhi upar jor do - user ko purana naam dikhna
  // nahi chahiye. Naam `meta[name="jarvis-name"]` se aata hai (config-driven).
  const fallback = ((document.querySelector('meta[name="jarvis-name"]') || {}).content
    || "Jarvis").toUpperCase();
  const raw = String(mode || "").toLowerCase();
  modeEl.textContent = (raw === "sunday" ? fallback : (mode || fallback)).toUpperCase();
  }

  // ---- gold progress arc ----
  const progEl = document.getElementById("ringProg");
  function setProgress(fraction) {
    let pct = Number(fraction);
    if (!isFinite(pct)) pct = 0;
    pct = Math.max(0, Math.min(1, pct));
    progEl.style.strokeDashoffset = String(PROG_C * (1 - pct));
  }

  // ---- orb ke neeche assistant ka pehla vakya ----
  // Markdown ke halke symbols (#, **, `, _ ke around) hata dete hain, phir
  // textContent se daalte hain — kabhi HTML nahi banate.
  function cleanText(text) {
    return String(text == null ? "" : text)
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/\*\*([^*]+)\*\*/g, "$1")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1$2")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/\s+/g, " ")
      .trim();
  }

  function firstLine(text) {
    const clean = cleanText(text);
    if (!clean) return "";
    // pehla vakya: '.', '?', '!' ya '—' par ruk jao
    const stop = clean.search(/[.?!—]/);
    let first = stop > 0 ? clean.slice(0, stop + 1) : clean;
    if (first.length > 180) first = first.slice(0, 180) + "…";
    return first;
  }

  function setLine(text) {
    lineEl.textContent = firstLine(text);
  }

  buildTicks();
  setState("idle");
  setProgress(0);

  window.JARVIS_ORB = {
    setState: setState,
    setMode: setMode,
    setProgress: setProgress,
    setLine: setLine,
    cleanText: cleanText,
    firstLine: firstLine
  };
})();
