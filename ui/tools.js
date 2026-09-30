class ToolsPanel {
  constructor(token, onNotice) {
    this.token = token;
    this.onNotice = onNotice;
    this.listEl = document.getElementById("activity");
    this.cardEl = document.getElementById("confirmcard");
    this.toolEl = document.getElementById("cardtool");
    this.detailEl = document.getElementById("carddetail");
    this.countEl = document.getElementById("cardcount");
    this.allowBtn = document.getElementById("allow");
    this.denyBtn = document.getElementById("deny");
    this.killBtn = document.getElementById("kill");
    this.card = null;
    this.toolsOn = false;
    this.ticker = null;
    this.left = 0;
    const initial = (document.querySelector('meta[name="prabh-tools"]') || {}).content;
    this.setKill(initial === "1");

    this.allowBtn.addEventListener("click", (e) => this.decide(true, e));
    this.denyBtn.addEventListener("click", (e) => this.decide(false, e));
    this.killBtn.addEventListener("click", (e) => this.toggleKill(e));
  }

  addLine(text, kind) {
    const row = document.createElement("div");
    row.className = "act " + kind;
    row.textContent = text;
    this.listEl.appendChild(row);
    this.listEl.scrollTop = this.listEl.scrollHeight;
  }

  handle(ev) {
    if (ev.type === "activity") {
      this.addLine(ev.tool + " | " + ev.decision + " | " + ev.text, ev.decision);
    } else if (ev.type === "confirm") {
      this.showCard(ev);
    }
  }

  showCard(ev) {
    this.clearTicker();
    this.card = ev;
    this.left = ev.timeout;
    this.toolEl.textContent = ev.tool;
    this.detailEl.textContent = ev.detail;
    this.countEl.textContent = this.left + "s";
    this.allowBtn.disabled = false;
    this.denyBtn.disabled = false;
    this.cardEl.hidden = false;
    this.ticker = setInterval(() => {
      this.left -= 1;
      this.countEl.textContent = this.left + "s";
      if (this.left <= 0) this.close();
    }, 1000);
  }

  clearTicker() {
    if (this.ticker) clearInterval(this.ticker);
    this.ticker = null;
  }

  close() {
    this.clearTicker();
    this.card = null;
    this.cardEl.hidden = true;
  }

  async decide(allow, event) {
    if (!event.isTrusted) return;
    const card = this.card;
    if (!card) return;
    this.allowBtn.disabled = true;
    this.denyBtn.disabled = true;
    try {
      const reply = await fetch("/tool/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-prabh-token": this.token },
        body: JSON.stringify({ id: card.id, hash: card.hash, allow: allow }),
      });
      if (!reply.ok) {
        const data = await reply.json().catch(() => ({}));
        this.onNotice(data.detail || "Allow/Deny nahi hua.");
      } else {
        this.addLine(allow ? "TUNE ALLOW kiya" : "TUNE DENY kiya", allow ? "allow" : "deny");
      }
    } catch (err) {
      this.onNotice("Server se baat nahi ho payi.");
    }
    this.close();
  }

  setKill(on) {
    this.toolsOn = on;
    this.killBtn.classList.toggle("on", on);
    this.killBtn.textContent = on ? "TOOLS ON" : "TOOLS OFF";
  }

  async toggleKill(event) {
    if (!event.isTrusted) return;
    const next = !this.toolsOn;
    try {
      const reply = await fetch("/tools/toggle", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-prabh-token": this.token },
        body: JSON.stringify({ on: next }),
      });
      if (!reply.ok) throw new Error("toggle fail");
      const data = await reply.json();
      this.setKill(data.tools_on);
      this.addLine(
        data.tools_on ? "TOOLS ON — LLM PC ka kaam kar sakta hai" : "TOOLS OFF — sab band",
        data.tools_on ? "allow" : "deny"
      );
    } catch (err) {
      this.onNotice("Kill switch nahi chala. Dobara try karo.");
    }
  }

  async cancel() {
    this.clearTicker();
    this.cardEl.hidden = true;
    this.card = null;
    try {
      await fetch("/tools/cancel", {
        method: "POST",
        headers: { "x-prabh-token": this.token },
      });
      this.addLine("STOP — pending tool rok diya", "deny");
    } catch (err) {
      /* server band ho to kuch nahi karna */
    }
  }
}
