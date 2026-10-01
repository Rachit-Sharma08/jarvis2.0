// BOTTOM BAR ke 6 quick buttons: BROWSER, YOUTUBE, WHATSAPP (left) aur
// MUSIC, FILES, SCAN (right). Icons inline SVG — bahar ki koi image nahi.
//
// SABSE IMPORTANT: click karne par ye seedha tool nahi chalata. Ye sirf
// POST /hud/quick {id} bhejta hai, aur server wahan `engine.run_tool()` se
// gatekeeper (kill switch + rate limit + confirm card) ke paar se guzarata hai.
// Is file me koi fetch chala ke tool karna nahi hai, koi bypass nahi.
//
// TOOLS OFF ho to sab button disabled dikhte hain. Server par bhi guard hai —
// user se chhupa kar click kar de to gatekeeper DENY dega.

(function () {
  const leftEl = document.getElementById("qLeft");
  const rightEl = document.getElementById("qRight");
  if (!leftEl || !rightEl) return;

  const TOKEN = (document.querySelector('meta[name="prabh-token"]') || {}).content || "";
  const SVG_NS = "http://www.w3.org/2000/svg";

  // Sirf 3 buttons har taraf. Config (config_hud.QUICK_BUTTONS) se order
  // alag rakha hai yahan, taaki HTML/JS dono na badlein — list server se
  // `/hud/quick` ke 404 se bachati hai aur id yahin se aata hai.
  const LEFT = ["browser", "youtube", "whatsapp"];
  const RIGHT = ["music", "files", "scan"];

  // Inline SVG paths (stroke-based, currentColor). Koi external file nahi.
  const ICONS = {
    browser: "M3 11h18M3 11a9 9 0 0 1 18 0M12 11v9",
    youtube: "M3 8h18v10H3zM10 10.5l5 2.5-5 2.5z",
    whatsapp: "M4 4h16v16H4zM8 9c0 4 3 7 7 7",
    music: "M9 18V6l10-2v12M9 18a2 2 0 1 1-4 0 2 2 0 0 1 4 0zM19 16a2 2 0 1 1-4 0 2 2 0 0 1 4 0z",
    files: "M3 6h7l2 3h9v11H3z",
    scan: "M4 8V4h4M20 8V4h-4M4 16v4h4M20 16v4h-4M4 12h16"
  };

  const LABELS = {
    browser: "BROWSER", youtube: "YOUTUBE", whatsapp: "WHATSAPP",
    music: "MUSIC", files: "FILES", scan: "SCAN"
  };

  let toolsOn = ((document.querySelector('meta[name="prabh-tools"]') || {}).content) === "1";
  const buttons = {};

  function makeIcon(id) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", ICONS[id] || ICONS.scan);
    svg.appendChild(path);
    return svg;
  }

  function makeButton(id) {
    const btn = document.createElement("button");
    btn.className = "qbtn";
    btn.type = "button";
    btn.title = LABELS[id] || id;

    const ico = document.createElement("span");
    ico.className = "qico";
    ico.appendChild(makeIcon(id));

    const lbl = document.createElement("span");
    lbl.className = "qlbl";
    lbl.textContent = LABELS[id] || id;

    btn.appendChild(ico);
    btn.appendChild(lbl);
    btn.disabled = !toolsOn;
    btn.addEventListener("click", (e) => onClick(id, e));
    buttons[id] = btn;
    return btn;
  }

  LEFT.forEach((id) => leftEl.appendChild(makeButton(id)));
  RIGHT.forEach((id) => rightEl.appendChild(makeButton(id)));

  // ---- click: sirf POST /hud/quick, kaam server + gatekeeper karega ----
  async function onClick(id, event) {
    if (!event.isTrusted) return;
    if (!toolsOn) {
      if (window.PRABH_ACTIVITY) {
        window.PRABH_ACTIVITY.addNote("TOOLS OFF hai — quick button band", "deny");
      }
      return;
    }
    try {
      const reply = await fetch("/hud/quick", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-prabh-token": TOKEN },
        body: JSON.stringify({ id: id })
      });
      if (!reply.ok) {
        const data = await reply.json().catch(() => ({}));
        if (window.PRABH_ACTIVITY) {
          window.PRABH_ACTIVITY.addNote(
            "Quick fail: " + (data.detail || reply.status), "deny");
        }
      }
    } catch (err) {
      if (window.PRABH_ACTIVITY) {
        window.PRABH_ACTIVITY.addNote("Quick: server se baat nahi hui", "deny");
      }
    }
  }

  // TOOLS toggle badle to button enable/disable (tools.js ise bulata hai).
  function setTools(on) {
    toolsOn = !!on;
    for (const id in buttons) {
      buttons[id].disabled = !toolsOn;
    }
  }

  setTools(toolsOn);
  window.PRABH_QUICK = { setTools: setTools, isOn: () => toolsOn };
})();
