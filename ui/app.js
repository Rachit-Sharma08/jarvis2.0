const TOKEN = (document.querySelector('meta[name="prabh-token"]') || {}).content || "";
const statusEl = document.getElementById("status");
const modeEl = document.getElementById("mode");
const orbEl = document.getElementById("orb");
const logEl = document.getElementById("messages");
const inputEl = document.getElementById("cmd");
const micBtn = document.getElementById("mic");
const muteBtn = document.getElementById("mute");
const stopBtn = document.getElementById("stop");
const micFlag = document.getElementById("micflag");
const noticeEl = document.getElementById("notice");

let currentMode = "SUNDAY";
let busy = false;

function addMessage(role, text, label) {
  const row = document.createElement("div");
  row.className = "msg " + role;
  const who = document.createElement("span");
  who.className = "who";
  if (role === "user") {
    who.textContent = "YOU";
  } else {
    who.textContent = label || "PRABH";
  }
  row.appendChild(who);
  row.appendChild(document.createTextNode(text));
  logEl.appendChild(row);
  logEl.parentElement.scrollTop = logEl.parentElement.scrollHeight;
}

function showNotice(text) {
  noticeEl.textContent = text || "";
}

function setStatus(value) {
  statusEl.textContent = value.toUpperCase();
  orbEl.classList.remove("listening", "thinking", "speaking");
  if (value !== "idle") orbEl.classList.add(value);
}

const ws = new WebSocket(`ws://${location.host}/ws?token=${encodeURIComponent(TOKEN)}`);
const seenMessages = new Set();

function newRid() {
  return "r" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

// Ek hi request ka message sirf ek hi baar render hoga (duble delivery ka guard).
function alreadyShown(ev) {
  const key = (ev.rid || "n") + "|" + ev.role + "|" + ev.text;
  if (seenMessages.has(key)) return true;
  seenMessages.add(key);
  if (seenMessages.size > 200) seenMessages.clear();
  return false;
}

function handleEvent(ev) {
  if (ev.type === "status") {
    setStatus(ev.value);
    if (ev.value === "idle") busy = false;
  } else if (ev.type === "message") {
    if (alreadyShown(ev)) return;
    addMessage(ev.role, ev.text, ev.label);
    if (ev.role === "assistant") voice.speak(ev.text, currentMode);
  } else if (ev.type === "confirm" || ev.type === "activity") {
    tools.handle(ev);
  } else if (ev.type === "log") {
    if (ev.data && ev.data.mode) {
      currentMode = ev.data.mode.toUpperCase();
      modeEl.textContent = "MODE: " + currentMode;
    }
    console.log("[prabh]", ev.level, ev.text);
  }
}

ws.onmessage = (e) => handleEvent(JSON.parse(e.data));

function send() {
  const text = inputEl.value.trim();
  if (!text || busy) return;
  inputEl.value = "";
  sendText(text);
}

async function sendText(text) {
  busy = true;
  showNotice("");
  const rid = newRid();
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ text, rid }));
    return;
  }
  try {
    const reply = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-prabh-token": TOKEN },
      body: JSON.stringify({ text, rid }),
    });
    if (!reply.ok) throw new Error("http " + reply.status);
    const data = await reply.json();
    (data.events || []).forEach(handleEvent);
  } catch (err) {
    showNotice("Server se baat nahi ho payi.");
    setStatus("idle");
    busy = false;
  }
}

const tools = new ToolsPanel(TOKEN, (err) => showNotice(err));

const voice = new VoiceUI({
  TOKEN: TOKEN,
  el: { mic: micBtn, mute: muteBtn, stop: stopBtn, flag: micFlag },
  notice: (text) => showNotice(text),
  status: (value) => setStatus(value),
  busy: (value) => { busy = value; },
  sendText: (text) => sendText(text),
});

function stopEverything() {
  tools.cancel();
  voice.stop();
}

document.getElementById("send").addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });