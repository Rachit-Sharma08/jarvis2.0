// hud_desktop.js — Python side ka haalat, sirf dikhane ke liye.
//
// Server har badlav par `{"type":"desktop","data":{...}}` bhejta hai
// (desktop/state.py). Yahan sirf ek pill update hota hai: mic + wake.
//
// Ye SIRF state dikhata hai. Mic yahan se ON/OFF nahi hota — wo tray icon
// ya "hello jarvis" se hota hai. Browser ka apna MIC button alag hai
// (wo page ke andar record karta hai).
//
// Text: `textContent` hi — innerHTML kabhi nahi (AGENTS.md ka UI niyam).

(function () {
  "use strict";

  const el = document.getElementById("deskstate");

  const LABEL = {
    off: "MIC BAND",
    idle: "MIC READY",
    listening: "SUN RAHA",
    muted: "MIC MUTE",
    error: "MIC ERROR"
  };

  function render(data) {
    if (!el || !data) return;
    const mic = String(data.mic || "off");
    const wake = data.wake && data.wake !== "off" ? "WAKE ON" : "WAKE OFF";
    let text = wake + " · " + (LABEL[mic] || LABEL.off);
    // Mic error ka wajah (jaise Windows permission band) chhoti line me.
    if (mic === "error" && data.mic_reason) {
      text += " · " + String(data.mic_reason).slice(0, 40);
    }
    el.textContent = text;
    el.className = "pill desk " + mic;
  }

  window.PRABH_DESKTOP = { render: render };
})();
