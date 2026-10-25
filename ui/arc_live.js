// ARC THEME — asli data se LIVE panels (KAAM B).
//
// Sirf Wahi data jo server pehle se bhejta hai: `/hud/stats` (CPU/RAM/net),
// `/ws` ke `stats` + `activity` + `log` events, aur `status` events.
// NAYA koi endpoint nahi — sirf naya presentation. "--" ki jagah "n/a"
// (spec) aur data na ho to "n/a", khaali string nahi.

(function () {
  "use strict";

  const CFG = window.JARVIS_ARC_CFG;
  const DOM = window.JARVIS_ARC_DOM;
  const byId = (id) => document.getElementById(id);

  // ---- STATE <-> UI label ----
  const STATES = {
    idle: "STANDBY", listening: "LISTENING", thinking: "THINKING",
    speaking: "SPEAKING", muted: "MUTED", error: "ERROR",
  };

  function setState(state) {
    const key = String(state || "idle").toLowerCase();
    const label = STATES[key] || STATES.idle;
    byId("a-status-word").textContent = label;
    byId("a-corestate").textContent = label;
    // Routing chip: brain tak ka hissa hi "live" dikhta hai.
    const busy = key === "thinking" || key === "speaking";
    byId("a-route-0").classList.toggle("live", key === "listening");
    byId("a-route-1").classList.toggle("live", key === "listening");
    byId("a-route-2").classList.toggle("live", busy);
    byId("a-route-3").classList.toggle("live", key === "speaking");
    if (key === "muted") byId("a-mute").classList.add("on");
    if (key !== "muted") byId("a-mute").classList.remove("on");
    if (key === "error") byId("a-taskdot").className = "a-taskdot err";
    else if (busy) byId("a-taskdot").className = "a-taskdot busy";
    else byId("a-taskdot").className = "a-taskdot";
  }

  // ---- SYSTEM: asli CPU/RAM/network ----
  function setStats(data) {
    if (!data) return;
    // `n/a` khaali ki jagah — spec ke mutabiq. `--` sirf tab jab number hi
    // na mile, jo ab nahi hota (KAAM 6 ke baad `/hud/stats` hamesha deta hai).
    [["core", data.cpu], ["memory", data.ram]].forEach(function (row) {
      const v = Number(row[1]);
      const ok = isFinite(v);
      byId("a-sys-" + row[0]).textContent = ok ? Math.round(v) + "%" : "n/a";
      byId("a-bar-" + row[0]).style.width = ok ? Math.max(0, Math.min(100, v)) + "%" : "0%";
    });
    const net = data.net || {};
    const down = Number(net.down), up = Number(net.up);
    const okNet = isFinite(down) && isFinite(up);
    // Network ek combined "up+down" bar hai — MB/s me.
    const pct = okNet ? Math.min(100, ((down + up) / (20 * 1024 * 1024)) * 100) : 0;
    byId("a-sys-network").textContent = okNet
      ? (down / 1048576).toFixed(1) + " / " + (up / 1048576).toFixed(1) + " MB/s" : "n/a";
    byId("a-bar-network").style.width = pct + "%";
  }

  // ---- UPLINK: latency = pichhli brain call ka ms ----
  function setLatency(ms) {
    const v = Number(ms);
    byId("a-up-lat").textContent = isFinite(v) && v >= 0 ? Math.round(v) + " ms" : "n/a";
  }

  function setChannel(text) {
    byId("a-up-chan").textContent = text || CFG.channel;
  }

  // ---- ACTIVITY: naya upar, aakhri N ----
  const rows = [];
  function pushActivity(time, text, kind) {
    rows.unshift({ time: time, text: text, kind: kind || "" });
    while (rows.length > CFG.activityMax) rows.pop();
    renderActivity();
  }

  function renderActivity() {
    const list = byId("a-activity");
    // Rebuild: sirf N chhoti lines hain, is liye sasta hai. `textContent`
    // se — raw-HTML nahi.
    while (list.firstChild) list.removeChild(list.firstChild);
    rows.forEach(function (row) {
      const line = DOM.mk("div", "a-act" + (row.kind ? " " + row.kind : ""));
      line.appendChild(DOM.mk("time", null, row.time));
      line.appendChild(DOM.mk("span", null, row.text));
      list.appendChild(line);
    });
  }

  function setTask(text, busy) {
    byId("a-tasktext").textContent = text || "Koi kaam chal nahi raha";
    const dot = byId("a-taskdot");
    dot.className = "a-taskdot" + (busy ? " busy" : "");
  }

  // ---- core ka bada number: active task, warna seconds ----
  let since = Date.now();
  function coreNumber(busyText) {
    if (busyText) return busyText;
    const s = Math.floor((Date.now() - since) / 1000);
    return String(s % 100).padStart(2, "0");
  }

  window.JARVIS_ARC_LIVE = {
    setState: setState, setStats: setStats, setLatency: setLatency,
    setChannel: setChannel, pushActivity: pushActivity, renderActivity: renderActivity,
    setTask: setTask, coreNumber: coreNumber,
    STATES: STATES,
  };
})();