// ARC THEME — loader (KAAM B).
//
// `ui/index.html` 200 cross kar gaya tha (CSS + script link + meta = ~20 line).
// Is liye arc ke **CSS aur JS** yahan se late-late lagate hain. Meta tags
// `index.html` ke `<head>` me hi rehte hain — `arc_config.js` unhe load ke
// waqt padhta hai, is liye wahan se hatane ka koi faida nahi.
//
// Wipe karne wala tareeka **NAHI** — sirf `createElement` + `appendChild`.
// Ye do wajah se:
//   1. CSP `script-src 'self'` (inline script mana hai)
//   2. Page ke beech me call karne par poora document hat jaata hai
//
// Ye file NEELA tab me bhi chalti hai. Uska kaam sirf `<link>`/`<script>`
// node banana hai — **booting** `arc_boot.js` karta hai, aur wo sirf
// `data-theme === "arc"` par. Is liye default HUD par inka asar nahi.

(function () {
  "use strict";

  // Load order zaroori hai: config → reactor → dom → live → shell → wire → boot.
  const CSS = [
    "arc.css",
    "arc_layout.css",
    "arc_core.css",
    "arc_bottom.css",
  ];

  const JS = [
    "arc_config.js",
    "arc_reactor.js",
    "arc_dom.js",
    "arc_live.js",
    "arc_shell.js",
    "arc_wire.js",
    "arc_boot.js",
  ];

  function addCss() {
    const head = document.head;
    for (const name of CSS) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = "/ui/" + name;
      head.appendChild(link);
    }
  }

  function addJs() {
    for (const name of JS) {
      const s = document.createElement("script");
      s.src = "/ui/" + name;
      // **`async = false` zaroori hai.** DOM se banaya gaya `<script>`
      // default **async** hota hai — yaani sab parallel download hote hain
      // aur jo pehle laut kar wahi pehle chalta hai. Load order toot'ne se
      // `arc_shell.js` `arc_dom.js` se pehle chala aur
      // `window.PRABH_ARC_DOM` undefined mila ("Cannot read properties of
      // undefined"). `async = false` se order wahi rehta hai jo array me hai.
      s.async = false;
      document.body.appendChild(s);
    }
  }

  function start() {
    addCss();
    addJs();
  }

  // Ye file `<head>` me aati hai, is liye `body` abhi shayad na bana ho.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();