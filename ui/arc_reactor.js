// ARC THEME — reactor SVG banata hai (KAAM B). Pure DOM, koi canvas nahi.
//
// Sirf `createElementNS` + `setAttribute` — raw-HTML injection kabhi nahi
// (AGENTS ka XSS niyam). Sab ghoomna CSS `transform: rotate` se hota hai,
// yaani sirf compositor ka kaam, i5 par sasta.
//
// Reference <https://jarvis.mukh1.com> ka LOOK dekha gaya hai; geometry,
// values aur code apne likhe hue hain (copy nahi).

(function () {
  "use strict";

  const NS = "http://www.w3.org/2000/svg";
  const C = 200;                 // centre (viewBox 400x400)

  function el(name, attrs) {
    const node = document.createElementNS(NS, name);
    for (const key in attrs) node.setAttribute(key, attrs[key]);
    return node;
  }

  function pt(angleDeg, radius) {
    const a = (angleDeg - 90) * Math.PI / 180;
    return [C + radius * Math.cos(a), C + radius * Math.sin(a)];
  }

  // Tik-marks ka ring — har `step` par ek, har 6th par lamba.
  function ticks(count, radius, majorEvery) {
    const g = el("g", {});
    for (let i = 0; i < count; i++) {
      const long = i % majorEvery === 0;
      const [x1, y1] = pt((360 / count) * i, radius);
      const [x2, y2] = pt((360 / count) * i, radius - (long ? 12 : 6));
      g.appendChild(el("line", {
        x1: x1.toFixed(2), y1: y1.toFixed(2),
        x2: x2.toFixed(2), y2: y2.toFixed(2),
        class: long ? "a-tick major" : "a-tick",
      }));
    }
    return g;
  }

  // Patle arcs — har group alag speed se ghoomti hai (CSS class `.a-spin`).
  function arcs(spec) {
    const g = el("g", {});
    spec.forEach(function (row, gi) {
      const grp = el("g", { class: "a-spin" + (row.rev ? " rev" : "") +
                                    (row.fast ? " fast" : "") });
      row.segs.forEach(function (s) {
        const [x1, y1] = pt(s[0], row.r);
        const [x2, y2] = pt(s[1], row.r);
        // Chhota gap chhodne ke liye thoda peeche kheencha — `stroke-linecap`
        // hi kaat-ta hai, is liye radius thoda alag rakhte hain.
        const [ax, ay] = pt(s[0] + 1.5, row.r);
        const [bx, by] = pt(s[1] - 1.5, row.r);
        grp.appendChild(el("path", {
          d: "M" + ax.toFixed(2) + " " + ay.toFixed(2) +
             " A" + row.r + " " + row.r + " 0 0 1 " +
             bx.toFixed(2) + " " + by.toFixed(2),
          class: "a-arc" + (row.thin ? " thin" : ""),
        }));
        void x1; void y1; void x2; void y2;
      });
      g.appendChild(grp);
      void gi;
    });
    return g;
  }

  // Chhah hexagon nodes — core ke gird.
  function hexagons(count, radius, size) {
    const g = el("g", {});
    for (let i = 0; i < count; i++) {
      const cx = C + radius * Math.cos(((360 / count) * i - 90) * Math.PI / 180);
      const cy = C + radius * Math.sin(((360 / count) * i - 90) * Math.PI / 180);
      const pts = [];
      for (let k = 0; k < 6; k++) {
        const a = (60 * k - 90) * Math.PI / 180;
        pts.push((cx + size * Math.cos(a)).toFixed(2) + "," +
                 (cy + size * Math.sin(a)).toFixed(2));
      }
      g.appendChild(el("polygon", { points: pts.join(" "), class: "a-hex" }));
    }
    return g;
  }

  // Ghoomte dots — do group, dono alag disha/speed.
  function orbitDots(spec) {
    const g = el("g", {});
    spec.forEach(function (row) {
      const grp = el("g", { class: "a-orbit" + (row.rev ? " rev" : "") });
      row.at.forEach(function (angle) {
        const [x, y] = pt(angle, row.r);
        grp.appendChild(el("circle", {
          cx: x.toFixed(2), cy: y.toFixed(2), r: row.size, class: "a-odot",
        }));
      });
      g.appendChild(grp);
    });
    return g;
  }

  function rings() {
    const g = el("g", {});
    [178, 150, 122].forEach(function (r) {
      g.appendChild(el("circle", {
        cx: C, cy: C, r: r, class: "a-ring",
        "stroke-dasharray": r > 160 ? "2 6" : "1 9",
      }));
    });
    return g;
  }

  function build(svg, opt) {
    // `viewBox` **pehle** set karna zaroori hai. Isse pehle set kiya tha, aur
    // uske baad children banaye — us waqt SVG ka intrinsic size 0 tha aur
    // **har** element ka `getBBox()` 0x0 aa raha tha (ticks/arcs/rings sab
    // invisible, jabki attributes sahi the). Source-check se ye nahi pakda —
    // sirf browser me dikhta hai.
    svg.setAttribute("viewBox", "0 0 400 400");
    svg.setAttribute("preserveAspectRatio", "xMidYMid meet");

    // Core gradient — SVG me CSS `radial-gradient()` valid NAHI hota
    // (AGENTS 3.2 ka wahi pakkaura), is liye yahi define karna padta hai.
    const defs = el("defs", {});
    const grad = el("radialGradient", { id: "aCoreGrad", cx: "50%", cy: "50%", r: "50%" });
    grad.appendChild(el("stop", { offset: "0%", "stop-color": "#ffe6c4" }));
    // Beech halka: core "chamakta" lagta hai aur andar ka number padhna
    // aasan rehta hai (pehle pure orange tha — number mushkil se dikhta tha).
    grad.appendChild(el("stop", { offset: "55%", "stop-color": opt.accent }));
    grad.appendChild(el("stop", { offset: "100%", "stop-color": opt.accent2 }));
    defs.appendChild(grad);
    svg.appendChild(defs);

    svg.appendChild(ticks(opt.ticks, 188, 6));
    svg.appendChild(arcs(ARC_SPEC));
    svg.appendChild(hexagons(opt.hex, 150, 7));
    svg.appendChild(rings());
    svg.appendChild(orbitDots(ORBIT_SPEC));
    svg.appendChild(el("circle", { cx: C, cy: C, r: 86, class: "a-core" }));
    return svg;
  }

  // Values `ui/arc_config.js` se aati hain (config ka JS saathi).
  const ARC_SPEC = [
    { r: 178, segs: [[10, 62], [96, 138], [186, 214], [250, 292]] },
    { r: 178, segs: [[40, 74], [150, 176], [232, 258]], rev: true, thin: true },
    { r: 122, segs: [[0, 46], [120, 158], [250, 286]], fast: true },
  ];
  const ORBIT_SPEC = [
    { r: 150, at: [20, 140, 260], size: 3.2 },
    { r: 122, at: [70, 200, 320], size: 2.4, rev: true },
  ];

  window.JARVIS_ARC_REACTOR = { build: build };
})();