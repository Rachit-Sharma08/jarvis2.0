// ACTIVITY panel: recent kaam, har line par UPPERCASE tag (DONE / ALLOW /
// DENIED / BLOCKED / PENDING) aur 2-line item (title + chhota subtitle).
//
// Ye file sirf list banati hai. Kaam kab chalega wo engine + gatekeeper decide
// karte hain — is file me koi tool chalta nahi, koi fetch nahi.
//
// Suraksha: har text `textContent` se, aur DOM sirf `createElement` se.
// Tool ka output LLM se aata hai — HTML banane wale koi API (string se markup
// wale) yahan BILKUL nahi, warna koi `<img onerror>` chala sakta hai.

(function () {
  const listEl = document.getElementById("activity");
  if (!listEl) return;

  const MAX_ROWS = 60;              // DOM bada na ho
  const SUB_LEN = 110;              // subtitle chhota

  // Server 'allow'/'deny' bhejta hai; UI ke liye naam saaf kar dete hain.
  const TAG = {
    allow: "ALLOW",
    deny: "DENIED",
    blocked: "BLOCKED",
    ask: "PENDING",
    pending: "PENDING",
    done: "DONE"
  };

  function tagFor(decision) {
    const key = String(decision || "").toLowerCase();
    return TAG[key] || "DONE";
  }

  function kindFor(decision) {
    const key = String(decision || "").toLowerCase();
    if (key === "allow" || key === "done") return "allow";
    if (key === "deny") return "deny";
    if (key === "blocked") return "blocked";
    return "pending";
  }

  function shorten(text) {
    const flat = String(text == null ? "" : text).replace(/\s+/g, " ").trim();
    if (flat.length <= SUB_LEN) return flat;
    return flat.slice(0, SUB_LEN) + "…";
  }

  // Ek row: [title / subtitle] .......... [TAG]
  function addRow(title, subtitle, decision) {
    const row = document.createElement("div");
    row.className = "actrow " + kindFor(decision);

    const textBox = document.createElement("div");
    textBox.className = "atext";

    const head = document.createElement("div");
    head.className = "atitle";
    head.textContent = shorten(title) || "…";
    textBox.appendChild(head);

    if (subtitle) {
      const sub = document.createElement("div");
      sub.className = "asub";
      sub.textContent = shorten(subtitle);
      textBox.appendChild(sub);
    }

    const tag = document.createElement("span");
    tag.className = "acttag";
    tag.textContent = tagFor(decision);

    row.appendChild(textBox);
    row.appendChild(tag);
    listEl.insertBefore(row, listEl.firstChild);   // naya upar

    while (listEl.children.length > MAX_ROWS) {
      listEl.removeChild(listEl.lastElementChild);
    }
  }

  function addActivity(ev) {
    const tool = String(ev.tool || "tool");
    const decision = ev.decision || "allow";
    addRow(tool, ev.text, decision);
  }

  function addNote(text, decision) {
    addRow(text, "", decision || "done");
  }

  // Purane tools.js ka API — confirm card wali line bhi yahin se jaati hai.
  function addLine(text, kind) {
    addRow(text, "", kind === "deny" ? "deny" : "allow");
  }

  window.JARVIS_ACTIVITY = {
    addActivity: addActivity,
    addNote: addNote,
    addLine: addLine,
    tagFor: tagFor,
    clear: function () { while (listEl.firstChild) listEl.removeChild(listEl.firstChild); }
  };
})();
