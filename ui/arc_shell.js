// ARC THEME — shell ka DOM (KAAM B).
//
// `arc_boot.js` 358 line par pahunch gaya tha (200-line niyam), is liye DOM
// ka hissa yahan nikal diya. Sirf markup banata hai — koi data, koi event
// wiring nahi (wo `arc_boot.js` me hai).
//
// Sab `createElement` + `textContent` — raw-HTML injection KABHI nahi.

(function () {
  "use strict";

  const DOM = window.PRABH_ARC_DOM;
  const NAME = DOM.name;

  // ---------------- top bar ----------------
  function top() {
    const bar = DOM.mk("header", "a-top");

    const brand = DOM.mk("div", "a-brand");
    brand.appendChild(DOM.mk("span", "a-dot"));
    brand.appendChild(DOM.mk("span", "a-name", "J A R V I S"));
    const st = DOM.mk("span", "a-status");
    st.appendChild(DOM.mk("span", null, "STATUS "));
    const word = DOM.mk("b", null, "STANDBY");
    word.id = "a-status-word";
    st.appendChild(word);
    brand.appendChild(st);
    bar.appendChild(brand);

    const right = DOM.mk("div", "a-topright");
    const clock = DOM.mk("span", "a-clock", "--:--:--");
    clock.id = "a-clock";
    const mute = DOM.mk("button", "a-btn", "MUTE");
    mute.id = "a-mute";
    mute.type = "button";
    const stop = DOM.mk("button", "a-btn", "STOP");
    stop.id = "a-stop";
    stop.type = "button";
    const full = DOM.mk("button", "a-btn", "FULL SCREEN");
    full.id = "a-full";
    full.type = "button";
    const chip = DOM.mk("span", "a-chip", "WAKE ON");
    chip.id = "a-wake";
    [clock, mute, stop, full, chip].forEach((n) => right.appendChild(n));
    bar.appendChild(right);
    return bar;
  }

  // ---------------- bottom bar ----------------
  function bottom() {
    const bar = DOM.mk("footer", "a-bottom");

    // badi mono line (typewriter) + chhota chat panel
    const lower = DOM.mk("div", "a-lower");
    const line = DOM.mk("p", "a-line", "");
    line.id = "a-line";
    lower.appendChild(line);
    const chat = DOM.mk("div", "a-chat");
    chat.id = "a-chat";
    lower.appendChild(chat);

    // SPACE/CLICK SPEAK · ESC STOP · type karo · LIVE
    const dock = DOM.mk("div", "a-dock");
    const keys = DOM.mk("div", "a-keys");
    [["SPACE / CLICK", "SPEAK"], ["ESC", "STOP"]].forEach(function (row) {
      const k = DOM.mk("span", "a-key");
      k.appendChild(DOM.mk("kbd", null, row[0]));
      k.appendChild(DOM.mk("span", null, row[1]));
      keys.appendChild(k);
    });
    dock.appendChild(keys);

    const input = DOM.mk("div", "a-input");
    const box = DOM.mk("input");
    box.id = "a-cmd";
    box.type = "text";
    box.autocomplete = "off";
    box.maxLength = 2000;
    box.placeholder = "type a command and press enter";
    input.appendChild(box);
    input.appendChild(DOM.mk("span", "a-live", "LIVE"));
    dock.appendChild(input);

    bar.appendChild(lower);
    bar.appendChild(dock);
    return bar;
  }

  // ---------------- poori shell ----------------
  function shell() {
    const root = DOM.mk("div", "a-root");
    root.appendChild(top());

    const cols = DOM.mk("div", "a-mid");
    const left = DOM.mk("aside", "a-col");
    left.appendChild(DOM.systemPanel());
    left.appendChild(DOM.uplinkPanel());
    const centre = DOM.mk("section", "a-col");
    centre.appendChild(DOM.reactor());
    const right = DOM.mk("aside", "a-col");
    right.appendChild(DOM.routingPanel());
    right.appendChild(DOM.activityPanel());
    right.appendChild(DOM.taskPanel());
    [left, centre, right].forEach((c) => cols.appendChild(c));

    root.appendChild(cols);
    root.appendChild(bottom());
    return root;
  }

  window.PRABH_ARC_SHELL = { shell: shell, name: NAME };
})();