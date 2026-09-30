const TOKEN = window.PRABH_TOKEN || "";
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

function showNotice(text) {
  noticeEl.textContent = text || "";
}

function setStatus(value) {
  statusEl.textContent = value.toUpperCase();
  orbEl.classList.remove("listening", "thinking", "speaking");
  if (value !== "idle") orbEl.classList.add(value);
}

const ws = new WebSocket(`ws://${location.host}/ws?token=${encodeURIComponent(TOKEN)}`);
ws.onmessage = (e) => {
  const ev = JSON.parse(e.data);
  if (ev.type === "status") setStatus(ev.value);
  else if (ev.type === "message") {
    addMessage(ev.role, ev.text);
    if (ev.role === "assistant") speakAnswer(ev.text);
  } else if (ev.type === "log") {
    if (ev.data && ev.data.mode) {
      currentMode = ev.data.mode.toUpperCase();
      modeEl.textContent = "MODE: " + currentMode;
    }
    console.log("[prabh]", ev.level, ev.text);
  }
};

function send() {
  const text = inputEl.value.trim();
  if (!text || busy) return;
  inputEl.value = "";
  sendText(text);
}

async function sendText(text) {
  busy = true;
  showNotice("");
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ text }));
  } else {
    try {
      const reply = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-prabh-token": TOKEN },
        body: JSON.stringify({ text }),
      });
      const data = await reply.json();
      (data.events || []).forEach((ev) => {
        if (ev.type === "message") addMessage(ev.role, ev.text);
        if (ev.type === "status") setStatus(ev.value);
        if (ev.type === "log" && ev.data && ev.data.mode) {
          currentMode = ev.data.mode.toUpperCase();
          modeEl.textContent = "MODE: " + currentMode;
        }
      });
    } catch (err) {
      showNotice("Server se baat nahi ho payi.");
    }
    busy = false;
  }
}

const speaker = new Speaker(
  TOKEN,
  (err) => { showNotice(err); setBusy(false); setStatus("idle"); },
  (provider) => { setStatus("speaking"); console.log("awaaz:", provider); },
  () => { busy = false; setStatus("idle"); }
);

function speakAnswer(text) {
  speaker.speak(text, currentMode.toLowerCase());
}

const recorder = new Recorder(onAudioReady, (err) => {
  showNotice(err);
  micFlag.classList.remove("on");
  setStatus("idle");
  setBusy(false);
});

function setBusy(value) {
  busy = value;
}

function onAudioReady(blob) {
  micFlag.classList.remove("on");
  micBtn.classList.remove("recording");
  setStatus("transcribing");
  transcribe(blob);
}

async function transcribe(blob) {
  try {
    const reply = await fetch("/stt", {
      method: "POST",
      headers: {
        "Content-Type": blob.type || "audio/webm",
        "x-prabh-token": TOKEN,
      },
      body: blob,
    });
    if (!reply.ok) {
      const data = await reply.json().catch(() => ({}));
      showNotice(data.detail || "Sun nahi paya.");
      setStatus("idle");
      setBusy(false);
      return;
    }
    const data = await reply.json();
    setStatus("listening");
    if (!data.text || !data.text.trim()) {
      setStatus("idle");
      setBusy(false);
      return;
    }
    sendText(data.text);
  } catch (err) {
    showNotice("Sun nahi paya. Dobara try karo.");
    setStatus("idle");
    setBusy(false);
  }
}

micBtn.addEventListener("click", async () => {
  if (recorder.muted) {
    showNotice("Mic band hai. Pehle MUTE hatao.");
    return;
  }
  if (recorder.active) {
    recorder.stop();
    return;
  }
  showNotice("");
  setBusy(true);
  setStatus("listening");
  micFlag.classList.add("on");
  micBtn.classList.add("recording");
  await recorder.start();
});

muteBtn.addEventListener("click", () => {
  const muted = !recorder.muted;
  recorder.setMuted(muted);
  muteBtn.classList.toggle("active", muted);
  micBtn.classList.remove("recording");
  micFlag.classList.remove("on");
  showNotice(muted ? "Mic band hai. Bolna chahu to MUTE dabao." : "");
  setStatus("idle");
  setBusy(false);
});

stopBtn.addEventListener("click", () => {
  speaker.stop();
  recorder.setMuted(recorder.muted);
  micBtn.classList.remove("recording");
  micFlag.classList.remove("on");
  setStatus("idle");
  setBusy(false);
});

document.getElementById("send").addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });