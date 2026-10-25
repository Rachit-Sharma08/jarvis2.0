// ARC THEME — data + keyboard + typewriter (KAAM B).
//
// `arc_boot.js` 200 cross karne par isme bant gaya: DOM ka hissa `arc_shell.js`
// me gaya, yahan sirf wiring hai.
//
// Performance (i5 laptop): koi WebGL/canvas nahi, sirf CSS transform/SVG.
// JS timers **~30fps** se zyada nahi (`CFG.frameMs`/`CFG.typeMs`), aur window
// background me CSS animation khud ruk jaati hai. `prefers-reduced-motion`
// ka rule `arc_bottom.css` me hai.

(function () {
  "use strict";

  const CFG = window.JARVIS_ARC_CFG;
  const SHELL = window.JARVIS_ARC_SHELL;
  const DOM = window.JARVIS_ARC_DOM;
  const LIVE = window.JARVIS_ARC_LIVE;

  // DOM abhi bhi na bana ho (ya page unload ho raha ho) tab `null` — is liye
  // har `setText` null-check karta hai. Yehi WS callbacks ko safe rakhta hai.
  const byId = (id) => document.getElementById(id);

  function setText(id, text) {
    const e = byId(id);
    if (e) e.textContent = text;
  }

  // ---------------- typewriter ----------------
  // Hidden tab par **rukna** hai (spec: "window hidden par ruke"). `setInterval`
  // background tab me bhi chalta rehta hai (throttled, par chalta hai), is liye
  // har tick par `document.hidden` check karte hain — sasta guard, koi listener
  // manage karne ki zarurat nahi.
  let typeTimer = null;
  function typewriter(text) {
    const line = byId("a-line");
    if (!line) return;
    if (typeTimer) { clearInterval(typeTimer); typeTimer = null; }
    line.classList.remove("done");
    line.textContent = "";
    const chars = String(text || "");
    let i = 0;
    typeTimer = setInterval(function () {
      if (document.hidden) return;      // hidden tab: ek bhi char aage nahi
      if (i >= chars.length) {
        clearInterval(typeTimer); typeTimer = null;
        line.classList.add("done");
        return;
      }
      i = Math.min(chars.length, i + 2);
      line.textContent = chars.slice(0, i);
    }, CFG.typeMs);
  }

  // ---------------- clock ----------------
  // Clock 1s ka hai aur hidden tab me bhi text update karna sasta hai — par
  // spec ek jaisa hai ("window hidden par ruke"), is liye yahan bhi guard.
  function tickClock() {
    if (document.hidden) return;
    const two = (n) => String(n).padStart(2, "0");
    const d = new Date();
    setText("a-clock",
      two(d.getHours()) + ":" + two(d.getMinutes()) + ":" + two(d.getSeconds()));
  }

  function startClock() {
    tickClock();
    setInterval(tickClock, 1000);
  }

  // ---------------- bhejna ----------------
  function token() {
    return (document.querySelector('meta[name="jarvis-token"]') || {}).content || "";
  }

  function hhmmss() {
    const two = (n) => String(n).padStart(2, "0");
    const d = new Date();
    return two(d.getHours()) + ":" + two(d.getMinutes()) + ":" + two(d.getSeconds());
  }

  function addMsg(who, text) {
    const chat = byId("a-chat");
    if (!chat) return;   // page unload ho raha hai
    const row = DOM.mk("div", "a-msg " + who);
    row.appendChild(DOM.mk("span", "who",
      who === "you" ? "YOU" : SHELL.name.toUpperCase()));
    row.appendChild(DOM.mk("span", "body", text));
    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight;
  }

  function send(text) {
    addMsg("you", text);
    typewriter("...");
    LIVE.setTask(text, true);
    LIVE.pushActivity(hhmmss(), text, "warn");
    const rid = "arc-" + Date.now();
    if (window.ArcWS && window.ArcWS.readyState === WebSocket.OPEN) {
      window.ArcWS.send(JSON.stringify({ text: text, rid: rid }));
      return;
    }
    // WS band: HTTP par bhejo (app.js ka wahi fallback).
    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-jarvis-token": token() },
      body: JSON.stringify({ text: text, rid: rid }),
    }).then(function (r) {
      if (!r.ok) throw new Error("http " + r.status);
      return r.json();
    }).then(function (data) {
      (data.events || []).forEach(handle);
    }).catch(function () {
      LIVE.setTask("Server se baat nahi ho payi", false);
    });
  }

  function handle(ev) {
    const type = ev && ev.type;
    if (type === "status") {
      LIVE.setState(ev.state || ev.status || "idle");
    } else if (type === "message") {
      const text = String(ev.text || "");
      addMsg("jarvis", text);
      typewriter(text);
      LIVE.setTask("", false);
    } else if (type === "activity") {
      LIVE.pushActivity(hhmmss(), String(ev.text || ev.tool || ""),
        ev.decision === "deny" ? "bad" : "");
      LIVE.setTask(String(ev.text || ""), false);
    } else if (type === "stats") {
      LIVE.setStats(ev.data);
    } else if (type === "log") {
      if (ev.data && ev.data.latency_ms !== undefined) {
        LIVE.setLatency(ev.data.latency_ms);
      }
    }
  }

  window.JARVIS_ARC = { handle: handle, send: send, typewriter: typewriter,
                       addMsg: addMsg, hhmmss: hhmmss, token: token,
                       tickClock: tickClock, startClock: startClock };
})();