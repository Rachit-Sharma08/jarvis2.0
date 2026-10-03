// TOP BAR: mode ka naam (J.A.R.V.I.S), ● LISTENING status pill, SYSTEM
// ONLINE/DEGRADED/OFFLINE pill, aur uske paas active provider + model.
//
// IMPORTANT: provider/model ka text KABHI hard-code nahi — hamesha
// /brain/status se aata hai. Agar server na bataye to khaali rahega.
//
// ONLINE/DEGRADED/OFFLINE ka faisla /brain/status ke active_tier par:
//   Tier 1 koi provider chal raha hai  -> ONLINE
//   Sirf Tier 2 (reserve) chal raha hai  -> DEGRADED
//   Koi provider nahi                    -> OFFLINE

(function () {
  const statusEl = document.getElementById("status");
  const sysEl = document.getElementById("sysstate");
  const provEl = document.getElementById("provider");
  const brandEl = document.getElementById("brand");
  if (!statusEl) return;

  const STATE = {
    idle: "● IDLE",
    listening: "● LISTENING",
    transcribing: "● TRANSCRIBING",
    thinking: "● THINKING",
    speaking: "● SPEAKING"
  };

  // Naam `meta[name="prabh-display"]` se (config-driven, config_name.py).
  // Server `label()` bhejta hai ("J.A.R.V.I.S"); agar kabhi sirf mode id
  // ("sunday") mile to display-name wapas use karo, purana naam nahi dikhe.
  const META = (n) => ((document.querySelector('meta[name="' + n + '"]') || {}).content || "");
  const DISPLAY = META("prabh-display") || "J.A.R.V.I.S";
  const NAME = META("prabh-name") || "Jarvis";

  // mode -> title. Spaced letters reference photo jaisa.
  function brandFor(mode) {
    return DISPLAY;
  }

  function setStatus(value) {
    const key = String(value || "idle").toLowerCase();
    statusEl.textContent = STATE[key] || STATE.idle;
    statusEl.className = "pill st-" + (STATE[key] ? key : "idle");
  }

  function setMode(mode) {
    const raw = String(mode || "").toLowerCase();
    // Andar ka id "sunday" hai (Step 1 me naam badla, id nahi) - brand hamesha
    // display-name rahe, id nahi.
    const key = (raw === "sunday" || raw === "") ? "jarvis" : raw;
    if (brandEl) brandEl.textContent = brandFor(key);
    return key;
  }

  // ---- /brain/status se SYSTEM pill + provider text ----
  //
  // ONLINE/DEGRADED/OFFLINE ka faisla:
  //   active_tier 1            -> ONLINE     (koi provider sach me chala)
  //   active_tier 2            -> DEGRADED   (sirf reserve tier)
  //   active_tier null         -> abhi kuch poocha hi nahi. Tab providers
  //                               dekhte hain: koi key + koi cooldown nahi
  //                               matlab tayyar hai -> ONLINE, warna OFFLINE.
  //                               (startup par sirf isi wajah se OFFLINE
  //                               dikhna galat hota)
  //   koi ready provider hi nahi-> OFFLINE
  function judgeTier(data) {
    if (data.active_tier === 1) return 1;
    if (data.active_tier === 2) return 2;
    const rows = Array.isArray(data.providers) ? data.providers : [];
    const ready = rows.some((row) => row && row.has_key && !row.cooldown);
    return ready ? 1 : 0;
  }

  function render(data) {
    if (!data) return;

    const tier = judgeTier(data);
    const state = tier === 1 ? "ONLINE" : (tier === 2 ? "DEGRADED" : "OFFLINE");
    sysEl.textContent = "SYSTEM " + state;
    sysEl.className = "pill sys " + (tier === 1 ? "on" : (tier === 2 ? "degrade" : "off"));

    // Sirf naam dikhana hai. Koi key/field idhar nahi — server bhejta hi nahi.
    const provider = data.provider || "";
    const model = data.model || "";
    let line = [provider, model].filter(Boolean).join(" · ");
    if (!line && tier === 1) line = "standby — tayyar";
    provEl.textContent = line;
    provEl.title = line;
  }

  function clearProvider() {
    provEl.textContent = "";
    sysEl.textContent = "SYSTEM …";
    sysEl.className = "pill sys";
  }

  window.PRABH_STATUS = {
    setStatus: setStatus,
    setMode: setMode,
    render: render,
    clearProvider: clearProvider,
    brandFor: brandFor
  };
})();
