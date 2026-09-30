const statusEl = document.getElementById("status");
const modeEl = document.getElementById("mode");
const orbEl = document.getElementById("orb");
const logEl = document.getElementById("messages");
const inputEl = document.getElementById("cmd");

function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = "msg " + role;
  const who = document.createElement("span");
  who.className = "who";
  who.textContent = role === "user" ? "YOU" : "PRABH";
  row.appendChild(who);
  row.appendChild(document.createTextNode(text));
  logEl.appendChild(row);
  logEl.parentElement.scrollTop = logEl.parentElement.scrollHeight;
}

function setStatus(value) {
  statusEl.textContent = value.toUpperCase();
  orbEl.classList.toggle("thinking", value === "thinking");
}

const TOKEN = window.PRABH_TOKEN || "";
const ws = new WebSocket(`ws://${location.host}/ws?token=${encodeURIComponent(TOKEN)}`);
ws.onmessage = (e) => {
  const ev = JSON.parse(e.data);
  if (ev.type === "status") setStatus(ev.value);
  else if (ev.type === "message") addMessage(ev.role, ev.text);
  else if (ev.type === "log") {
    if (ev.data && ev.data.mode) modeEl.textContent = "MODE: " + ev.data.mode.toUpperCase();
    console.log("[prabh]", ev.level, ev.text);
  }
};

function send() {
  const text = inputEl.value.trim();
  if (!text) return;
  inputEl.value = "";
  if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ text }));
  else fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json", "x-prabh-token": TOKEN },
    body: JSON.stringify({ text }),
  });
}

document.getElementById("send").addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });