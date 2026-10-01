// SYSTEM panel: 3 gol arc gauges (CPU / RAM / BATTERY) + 2 horizontal bars
// (DISK / NETWORK). Data WebSocket ke "stats" event se aata hai — is file me
// koi fetch nahi, koi polling nahi.
//
// Har number server se aata hai aur UI me sirf textContent se jaata hai.
// Gauges pehle hi ban jaate hain (structure), phir har update me sirf
// stroke-dashoffset aur % text badalta hai — DOM dobara nahi banta.

(function () {
  const gaugeBox = document.getElementById("gauges");
  const barBox = document.getElementById("bars");
  if (!gaugeBox || !barBox) return;

  const SVG_NS = "http://www.w3.org/2000/svg";
  const GAUGE_R = 26;
  const GAUGE_C = 2 * Math.PI * GAUGE_R;      // viewBox 60 me r=26
  const REF_SPEED = 8.0;                      // MB/s jisko 100% maana jaye

  const gauges = {};      // name -> {fill, val}
  const bars = {};        // name -> {fill, val}

  function makeSvg(tag, attrs) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const key in attrs) node.setAttribute(key, attrs[key]);
    return node;
  }

  // ---- 3 arc gauges ----
  const GAUGE_DEFS = [
    { name: "cpu", label: "CPU" },
    { name: "ram", label: "RAM" },
    { name: "batt", label: "BATT" }
  ];

  function addGauge(def) {
    const wrap = document.createElement("div");
    wrap.className = "gauge";

    const svg = makeSvg("svg", { viewBox: "0 0 60 60" });
    svg.appendChild(makeSvg("circle", {
      class: "g-track", cx: 30, cy: 30, r: GAUGE_R
    }));
    const fill = makeSvg("circle", {
      class: "g-fill", cx: 30, cy: 30, r: GAUGE_R,
      "stroke-dasharray": GAUGE_C,
      "stroke-dashoffset": GAUGE_C,
      transform: "rotate(-90 30 30)"
    });
    svg.appendChild(fill);

    const val = makeSvg("text", { class: "g-val", x: 30, y: 34 });
    val.textContent = "--";
    svg.appendChild(val);

    const lbl = makeSvg("text", { class: "g-lbl", x: 30, y: 46 });
    lbl.textContent = def.label;
    svg.appendChild(lbl);

    wrap.appendChild(svg);
    gaugeBox.appendChild(wrap);
    gauges[def.name] = { fill: fill, val: val, arc: GAUGE_C };
  }

  // ---- 2 horizontal bars ----
  const BAR_DEFS = [
    { name: "disk", label: "DISK" },
    { name: "net", label: "NETWORK" }
  ];

  function addBar(def) {
    const row = document.createElement("div");
    row.className = "barrow";

    const lbl = document.createElement("span");
    lbl.className = "barlbl";
    lbl.textContent = def.label;

    const track = document.createElement("span");
    track.className = "bartrack";
    const fill = document.createElement("span");
    fill.className = "barfill" + (def.name === "net" ? " net" : "");
    track.appendChild(fill);

    const val = document.createElement("span");
    val.className = "barval";
    val.textContent = "--";

    row.appendChild(lbl);
    row.appendChild(track);
    row.appendChild(val);
    barBox.appendChild(row);
    bars[def.name] = { fill: fill, val: val };
  }

  GAUGE_DEFS.forEach(addGauge);
  BAR_DEFS.forEach(addBar);

  function setGauge(name, percent, text) {
    const g = gauges[name];
    if (!g) return;
    const pct = Math.max(0, Math.min(100, Number(percent) || 0));
    g.fill.style.strokeDashoffset = String(g.arc * (1 - pct / 100));
    g.fill.classList.remove("warn", "hot");
    if (pct >= 90) g.fill.classList.add("hot");
    else if (pct >= 70) g.fill.classList.add("warn");
    g.val.textContent = text;
  }

  function setBar(name, percent, text) {
    const b = bars[name];
    if (!b) return;
    const pct = Math.max(0, Math.min(100, Number(percent) || 0));
    b.fill.style.width = pct + "%";
    b.val.textContent = text;
  }

  function render(data) {
    if (!data) return;
    setGauge("cpu", data.cpu, Math.round(data.cpu) + "%");
    setGauge("ram", data.ram, Math.round(data.ram) + "%");

    const bat = data.battery || {};
    if (bat.percent === null || bat.percent === undefined) {
      setGauge("batt", 100, "PLUG");
    } else {
      setGauge("batt", bat.percent, bat.percent + "%");
    }

    setBar("disk", data.disk, data.disk + "%");

    const net = data.net || {};
    const down = Number(net.down) || 0;
    const up = Number(net.up) || 0;
    setBar("net", (down / REF_SPEED) * 100,
      down.toFixed(1) + " MB/s");
    // Spec ke hisaab se MB/s dikhana hai (na ki MB)
  bars.net.val.textContent = down.toFixed(1) + "/" + up.toFixed(1) + " MB/s";
  }

  window.PRABH_STATS = { render: render };
})();
