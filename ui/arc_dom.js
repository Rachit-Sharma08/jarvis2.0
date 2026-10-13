// ARC THEME — pura DOM banata hai (KAAM B).
//
// Sirf `createElement` + `textContent` — raw-HTML injection KABHI nahi
// (AGENTS ka XSS niyam, aur `hud_check_ui.py` bhi yehi check karta hai).
// Isi wajah se markup JS me banaya ja raha hai, `index.html` chhota rehta hai.

(function () {
  "use strict";

  const NAME = (document.querySelector('meta[name="prabh-name"]') || {}).content || "Jarvis";
  const CFG = window.PRABH_ARC_CFG;

  function mk(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }

  function panel(title, cls) {
    const p = mk("section", "a-panel" + (cls ? " " + cls : ""));
    if (title) p.appendChild(mk("h2", "a-ptab", title));
    return p;
  }

  // ---- SYSTEM: 3 metric + orange bar ----
  function systemPanel() {
    const p = panel("SYSTEM");
    ["core", "memory", "network"].forEach(function (key) {
      const box = mk("div", "a-metric");
      const row = mk("div", "row");
      row.appendChild(mk("span", null, key.toUpperCase()));
      const val = mk("b", null, "n/a");
      val.id = "a-sys-" + key;
      row.appendChild(val);
      const track = mk("div", "a-track");
      const fill = mk("div", "a-fill");
      fill.id = "a-bar-" + key;
      track.appendChild(fill);
      box.appendChild(row);
      box.appendChild(track);
      p.appendChild(box);
    });
    return p;
  }

  // ---- UPLINK: latency (pichhli brain call) + channel ----
  function uplinkPanel() {
    const p = panel("UPLINK");
    [["a-up-lat", "LATENCY"], ["a-up-chan", "CHANNEL"]].forEach(function (row) {
      const line = mk("div", "a-metric");
      const r = mk("div", "row");
      r.appendChild(mk("span", null, row[1]));
      const v = mk("b", null, "n/a");
      v.id = row[0];
      r.appendChild(v);
      line.appendChild(r);
      p.appendChild(line);
    });
    return p;
  }

  // ---- ROUTING chip: WAKE -> STT -> BRAIN -> TTS ----
  function routingPanel() {
    const p = panel("ROUTING");
    const row = mk("div", "a-routing");
    CFG.routing.forEach(function (node, i) {
      if (i) row.appendChild(mk("span", "a-arrow", "→"));
      const chip = mk("span", "a-node", node);
      chip.id = "a-route-" + i;
      row.appendChild(chip);
    });
    p.appendChild(row);
    p.appendChild(mk("span", "a-credit", CFG.credit));
    return p;
  }

  // ---- ACTIVITY: asli events, aakhri ~6, naya upar ----
  function activityPanel() {
    const p = panel("ACTIVITY");
    p.classList.add("grow");
    const list = mk("div", "a-actlist");
    list.id = "a-activity";
    p.appendChild(list);
    return p;
  }

  // ---- LIVE TASK + status dot ----
  function taskPanel() {
    const p = panel("LIVE TASK");
    const box = mk("div", "a-task");
    const top = mk("div", "a-tasktop");
    const dot = mk("span", "a-taskdot");
    dot.id = "a-taskdot";
    top.appendChild(dot);
    top.appendChild(mk("span", null, "IDLE"));
    box.appendChild(top);
    box.appendChild(mk("p", "a-tasktext", "Koi kaam chal nahi raha"));
    box.lastChild.id = "a-tasktext";
    p.appendChild(box);
    return p;
  }

  // ---- REACTOR: SVG + core ke andar number + state ----
  function reactor() {
    const wrap = mk("div", "a-core-wrap");
    const box = mk("div", "a-reactor-box");
    // **SVG namespace** zaroori hai. `document.createElement("svg")` se
    // HTML-namespace ka `<svg>` banta hai, aur usme daale gaye
    // SVG-namespace ke children `getBBox() = 0x0` dete hain — sab invisible.
    // `createElementNS(NS, ...)` hi asli `<svg>` banata hai.
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "a-reactor");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", NAME + " arc reactor");
    window.PRABH_ARC_REACTOR.build(svg, {
      accent: CFG.accent, accent2: CFG.accent2,
      ticks: CFG.ticks, hex: CFG.hex,
    });
    const txt = mk("div", "a-coretxt");
    const num = mk("p", "a-corenum", "00");
    num.id = "a-corenum";
    const st = mk("p", "a-corestate", "STANDBY");
    st.id = "a-corestate";
    txt.appendChild(num);
    txt.appendChild(st);
    box.appendChild(svg);
    box.appendChild(txt);
    wrap.appendChild(box);
    return wrap;
  }

  function corner(cls) {
    const d = mk("div", "a-corner " + cls);
    d.setAttribute("aria-hidden", "true");
    return d;
  }

  window.PRABH_ARC_DOM = {
    systemPanel: systemPanel,
    uplinkPanel: uplinkPanel,
    routingPanel: routingPanel,
    activityPanel: activityPanel,
    taskPanel: taskPanel,
    reactor: reactor,
    corner: corner,
    mk: mk,
    name: NAME,
  };
})();