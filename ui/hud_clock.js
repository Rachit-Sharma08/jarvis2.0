// CHRONOMETER panel: seconds ka gol dial + bada HH:MM + poori date.
// Browser ka apna clock use hota hai (Date) — koi extra API nahi.
// Date text server se nahi aata, isliye locale se banta hai. textContent hi.

(function () {
  const timeEl = document.getElementById("clockTime");
  const dateEl = document.getElementById("clockDate");
  const secEl = document.getElementById("clockSec");
  const dialEl = document.getElementById("dialSec");
  if (!timeEl) return;

  const CIRCUMFERENCE = 276.5;      // 2 * pi * 44 (svg viewBox 100 me r=44)
  const MONTHS = ["January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"];
  const DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday"];

  function pad(value) {
    return value < 10 ? "0" + value : String(value);
  }

  // Wednesday, 30 September 2026
  function longDate(now) {
    return DAYS[now.getDay()] + ", " + now.getDate() + " " +
      MONTHS[now.getMonth()] + " " + now.getFullYear();
  }

  function tick() {
    const now = new Date();
    timeEl.textContent = pad(now.getHours()) + ":" + pad(now.getMinutes());
    dateEl.textContent = longDate(now);

    const sec = now.getSeconds();
    secEl.textContent = pad(sec);
    // 0s = khaali ring, 59s = poora. Linear, 1s me update.
    if (dialEl) {
      dialEl.style.strokeDashoffset = String(CIRCUMFERENCE * (1 - sec / 60));
    }
  }

  tick();
  setInterval(tick, 1000);
  window.PRABH_CLOCK = { tick: tick };
})();
