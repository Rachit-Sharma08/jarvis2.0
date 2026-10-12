// HUD ka shuruaati bharav — `/hud/stats` ek baar load par (13-Oct, KAAM 6).
//
// SABOOT: `hud_stats.js` ka `render()` sirf WebSocket ke `stats` event par
// chalti thi. Par `server/ws_routes.py` ka pump **pehle** 2 s sota hai — yaani
// pehla event 2 s BAAD aata tha, is liye har load par SYSTEM panel par
// `--` dikhta. Aur WS kabhi na chala (token mismatch — `localhost` vs
// `127.0.0.1` wala purana bug) to `--` HAMESHA rehta.
//
// `server/hud_routes.py` ka docstring kehta hai ye endpoint "ek baar load par
// bhi chalta hai taaki panel khali na rahe" — par JS use kabhi call hi nahi
// karta tha. Ye file wahi kaam karti hai.
//
// Weather alag hai: `hud_weather.js` apne `load()` se khud chalta hai
// (15 min interval) — is liye usse yahan dobara nahi maanga.
//
// Same-origin GET par `Origin` header nahi jaata; endpoint `Referer` /
// `Sec-Fetch-Site` proof maangta hai (`server/security.py`). Normal browser
// fetch dono bhej deta hai — `tests/test_hud_stats_load.py` me pakda hai.

(function () {
  "use strict";

  function token() {
    var meta = document.querySelector('meta[name="prabh-token"]');
    return (meta && meta.content) || "";
  }

  function loadOnce(path, render) {
    fetch(path, { headers: { "x-prabh-token": token() } })
      .then(function (res) {
        if (!res.ok) throw new Error("http " + res.status);
        return res.json();
      })
      .then(render)
      .catch(function () {
        // Server band ya WS nahi - panel ko "--" hi rehne do. Crash nahi.
      });
  }

  function primePanels() {
    loadOnce("/hud/stats", function (data) {
      if (window.PRABH_STATS) window.PRABH_STATS.render(data);
    });
  }

  // Expose taaki test/app dono isko ek hi jagah se dekh sakein.
  window.PRABH_PRIME = { prime: primePanels, loadOnce: loadOnce };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", primePanels);
  } else {
    primePanels();
  }
})();
