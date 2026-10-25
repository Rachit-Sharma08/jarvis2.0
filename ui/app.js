// app.js — sirf chat + WebSocket ka glue. Baaki sab apni file me hai:
//   hud_clock / hud_stats / hud_activity / hud_status / hud_orb /
//   hud_weather / hud_quick / tools / voice_ui
//
// Is file me koi panel ka DOM nahi banaya jaata — sab `#id` se uthaya jaata
// hai jo index.html me pehle se hai. Ye chhota rakhne ka reason yahi hai.

const TOKEN = (document.querySelector('meta[name="jarvis-token"]') || {}).content || "";
// Naam config se (config_name.py) — `prabh-name` meta se padho, fallback rakho.
const NAME = (document.querySelector('meta[name="jarvis-name"]') || {}).content || "Jarvis";
const LABEL = NAME.toUpperCase();
const logEl = document.getElementById("messages");
const inputEl = document.getElementById("cmd");
const micBtn = document.getElementById("mic");
const muteBtn = document.getElementById("mute");
const stopBtn = document.getElementById("stop");
const micFlag = document.getElementById("micflag");
const noticeEl = document.getElementById("notice");
const status = window.JARVIS_STATUS;
const orb = window.JARVIS_ORB;

let currentMode = "sunday";
let busy = false;

function addMessage(role, text, label) {
  const row = document.createElement("div");
  row.className = "msg " + role;

  const who = document.createElement("span");
  who.className = "who";
  who.textContent = role === "user" ? "YOU" : (label || LABEL);
  row.appendChild(who);

  const body = document.createElement("div");
  body.className = "body";
  // textContent hi — markdown symbols orb.js ke cleanText() ne pehle hataye
  body.textContent = orb.cleanText(text);
  row.appendChild(body);

  logEl.appendChild(row);
  logEl.scrollTop = logEl.scrollHeight;
}

function showNotice(text) {
  noticeEl.textContent = text || "";
}

function setStatus(value) {
  const key = String(value || "idle").toLowerCase();
  status.setStatus(key);
  orb.setState(key);
  if (key === "idle") busy = false;
}

// ---- /brain/status: SYSTEM ONLINE/DEGRADED + provider/model ----
let brainTimer = null;
async function loadBrain() {
  try {
    const reply = await fetch("/brain/status", {
      headers: { "x-jarvis-token": TOKEN },
      cache: "no-store"
    });
    if (!reply.ok) throw new Error("http " + reply.status);
    status.render(await reply.json());
  } catch (err) {
    status.clearProvider();
  }
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
  } else if (ev.type === "message") {
    if (alreadyShown(ev)) return;
    addMessage(ev.role, ev.text, ev.label);
    if (ev.role === "assistant") {
      orb.setLine(ev.text);
      // `via: "voice"` = jawab wake se aaya hai. Awaaz already Python ke
      // speaker se boli gayi (desktop/playback.py), is liye browser TTS yahin
      // SKIP. Likh kar bheja hua message par ye nahi lagta -> wo waise hi
      // bolega, jaise pehle.
      if (ev.via !== "voice") voice.speak(ev.text, currentMode);
    }
  } else if (ev.type === "confirm" || ev.type === "activity") {
    tools.handle(ev);
  } else if (ev.type === "stats") {
    if (window.JARVIS_STATS) window.JARVIS_STATS.render(ev.data);
  } else if (ev.type === "desktop") {
    if (window.JARVIS_DESKTOP) window.JARVIS_DESKTOP.render(ev.data);
  } else if (ev.type === "reminders") {
    const pill = document.getElementById('remindPill');
    if (pill) {
      const items = ev.data && ev.data.items ? ev.data.items : [];
      if (items.length) {
        pill.textContent = 'REMIND: ' + items.map(function(x){ return x.when + ' ' + x.text; }).join(' | ');
        pill.classList.add('show');
      } else {
        pill.classList.remove('show');
        pill.textContent = '';
      }
    }
  } else if (ev.type === "log") {
    if (ev.data && ev.data.mode) {
      // `currentMode` **mode id** hai (lowercase, jaise "sunday") - TTS isi ko
      // chahiye, warna `voice_for(provider, "SUNDAY")` match hi nahi karta.
      // Orb/brand ko dikhne wala naam chahiye, wo LABEL se aata hai.
      currentMode = String(ev.data.mode).toLowerCase();
      orb.setMode(LABEL);
      status.setMode(LABEL);
    }
    console.log("[prabh]", ev.level, ev.text);
  }
}

ws.onmessage = (e) => handleEvent(JSON.parse(e.data));
ws.onclose = () => showNotice("Server se connection toot gaya. Page dobara kholo.");

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
      headers: { "Content-Type": "application/json", "x-jarvis-token": TOKEN },
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
  // VoiceUI apne listener se sirf speaker/recorder rokta hai. Pending tool
  // card alag se cancel karna padta hai, warna card UI par atak jaayega.
  tools.cancel();
  voice.stop();
}

// STOP button dono kaam kare: awaaz + pending confirm card.
stopBtn.addEventListener("click", stopEverything);

document.getElementById("send").addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });

// Mode + brain pill load; brain har 15s refresh (pool badal sakta hai).
status.setMode(LABEL);
orb.setMode(LABEL);
loadBrain();
brainTimer = setInterval(loadBrain, 15000);
