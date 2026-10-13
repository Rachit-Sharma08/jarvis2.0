// ARC THEME — boot + keyboard (KAAM B). Entry point.
//
// Sirf teen kaam: shell mount karna, keyboard lagana, aur live data shuru
// karna. Baaki hissa:
//   `arc_shell.js` — DOM        `arc_wire.js`  — data/WS/typewriter
//   `arc_dom.js`   — panels     `arc_live.js`  — stats/activity/state
//   `arc_reactor.js` — SVG      `arc_config.js` — Python se aayi constants
//
// Ye teen file NEELA tab me bhi load hoti hain (script tag har theme par
// hai), is liye neeche ka `if (theme === "arc")` guard zaroori hai — warna
// dono HUD ek saath dikh rahe honge.

(function () {
  "use strict";

  const CFG = window.PRABH_ARC_CFG;
  const SHELL = window.PRABH_ARC_SHELL;
  const ARC = window.PRABH_ARC;          // typewriter/send/handle (arc_wire.js)
  const LIVE = window.PRABH_ARC_LIVE;
  const byId = (id) => document.getElementById(id);

  // ---------------- boot ----------------
  function boot() {
    const bg = document.createElement("div");
    bg.className = "a-bg";
    bg.setAttribute("aria-hidden", "true");
    document.body.appendChild(bg);
    ["tl", "tr", "bl", "br"].forEach(function (c) {
      const d = document.createElement("div");
      d.className = "a-corner " + c;
      d.setAttribute("aria-hidden", "true");
      document.body.appendChild(d);
    });
    document.body.appendChild(SHELL.shell());
    LIVE.setChannel(CFG.channel);
    LIVE.setLatency(null);
    ARC.tickClock();
    ARC.typewriter("Ji, main hoon. Kya karun?");
    keyboard();
    prime();
  }

  // ---------------- keyboard ----------------
  function isTyping(node) {
    const tag = node && (node.tagName || "").toLowerCase();
    return tag === "input" || tag === "textarea";
  }

  function stopAll() {
    // STOP: awaaz + pending confirm card — wahi kaam jo purane HUD ka STOP
    // karta hai. `isTrusted` click-handler wala rule yahan nahi lagta (key
    // se aaya hai), par dono raaste band karte hain.
    if (window.JarvisTools && window.JarvisTools.cancel) window.JarvisTools.cancel();
    if (window.PRABH_VOICE && window.PRABH_VOICE.stop) window.PRABH_VOICE.stop();
  }

  function keyboard() {
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { stopAll(); return; }
      if (e.key === "F11") { e.preventDefault(); toggleFullscreen(); return; }
      if (e.key === "Enter") {
        const box = byId("a-cmd");
        if (!box) return;
        const text = box.value.trim();
        if (text) { WIRE.send(text); box.value = ""; }
        return;
      }
      // SPACE hold-to-speak. Input me space **type** karna hai.
      if (e.code === "Space" && !isTyping(e.target)) {
        e.preventDefault();
        if (!e.repeat) talk(true);
      }
    });
    document.addEventListener("keyup", function (e) {
      if (e.code === "Space" && !isTyping(e.target) && !e.repeat) talk(false);
    });

    const mute = byId("a-mute");
    if (mute) mute.addEventListener("click", function (e) {
      if (!e.isTrusted) return;
      if (window.PRABH_VOICE && window.PRABH_VOICE.toggleMute) {
        window.PRABH_VOICE.toggleMute();
      }
      LIVE.setState(mute.classList.contains("on") ? "muted" : "idle");
    });
    const stop = byId("a-stop");
    if (stop) stop.addEventListener("click", function (e) {
      if (e.isTrusted) stopAll();
    });
    const full = byId("a-full");
    if (full) full.addEventListener("click", function (e) {
      if (e.isTrusted) toggleFullscreen();
    });
  }

  function talk(on) {
    const v = window.PRABH_VOICE;
    if (!v) return;
    if (on && v.start) v.start();
    if (!on && v.stop) v.stop();
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      const p = document.documentElement.requestFullscreen &&
                document.documentElement.requestFullscreen();
      // Fail ho to chup-chaap — user ko dikhane ki zarurat nahi.
      if (p && p.catch) p.catch(function () {});
    } else if (document.exitFullscreen) {
      document.exitFullscreen();
    }
  }

  // ---------------- live data ----------------
  function prime() {
    // Same-origin GET par `Origin` header nahi jaata — `Referer` chalta hai
    // (server/security.py ka wahi rule). Token meta se.
    fetch("/hud/stats", { headers: { "x-prabh-token": ARC.token() },
                          cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) LIVE.setStats(d); })
      .catch(function () { /* panel "n/a" par rahega, crash nahi */ });

    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(proto + "://" + location.host + "/ws?token=" +
                             encodeURIComponent(ARC.token()));
    window.ArcWS = ws;
    ws.onmessage = function (e) {
      let ev = null;
      try { ev = JSON.parse(e.data); } catch (err) { return; }
      window.PRABH_ARC.handle(ev);
    };
    // WS ke callback DOM ke BAAD bhi chal sakte hain (unload, ya tab
    // background me band) — is liye null-check zaroori.
    ws.onclose = function () {
      LIVE.pushActivity(ARC.hhmmss(), "connection closed", "bad");
      const badge = byId("a-live");
      if (badge) badge.textContent = "OFFLINE";
    };
    ws.onopen = function () {
      const badge = byId("a-live");
      if (badge) badge.textContent = "LIVE";
    };

    // Core ka bada number: active task, warna seconds. ~30fps, hidden par ruke.
    setInterval(function () {
      if (document.hidden) return;
      const num = byId("a-corenum");
      if (num) num.textContent = LIVE.coreNumber(null);
    }, CFG.frameMs);
  }

  // Sirf arc theme par. Default "neon" me ye teeno file chup-chaap load hoti
  // hain par kuch nahi karte.
  const theme = (document.querySelector('meta[name="prabh-theme"]') || {}).content;
  if (theme === "arc") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", boot);
    } else {
      boot();
    }
  }
})();