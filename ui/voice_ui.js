// Mic + speaker + STT ka UI. app.js sirf chat/websocket chalata hai.
//
// Ye class `Recorder` aur `Speaker` (recorder.js / speaker.js) ko wire karta hai.
// app.js ise banata hai aur `voice.speak(text, mode)` + `voice.stop()` call karta hai.

class VoiceUI {
  constructor(opts) {
    this.opts = opts;                       // {TOKEN, notice, status, busy, sendText, el}
    this.el = opts.el;                      // {mic, mute, stop, flag}

    this.speaker = new Speaker(
      opts.TOKEN,
      (err) => this.fail(err),
      (provider) => { opts.status("speaking"); console.log("awaaz:", provider); },
      () => this.done()
    );
    this.recorder = new Recorder(
      (blob, ms) => this.onAudio(blob, ms),
      (err) => this.fail(err)
    );

    this.el.mic.addEventListener("click", () => this.micClick());
    this.el.mute.addEventListener("click", () => this.muteClick());
    this.el.stop.addEventListener("click", () => this.stop());
  }

  fail(err) {
    this.opts.notice(err);
    this.stop();
  }

  done() {
    this.opts.busy(false);
    this.opts.status("idle");
  }

  // Jawab bolwana. Mode ke hisaab se awaaz chunta hai (mode id: sunday / prabh —
// user ko sirf naam dikhta hai: Jarvis).
  speak(text, mode) {
    this.speaker.speak(text, String(mode).toLowerCase());
  }

  async micClick() {
    if (this.recorder.muted) {
      this.opts.notice("Mic band hai. Pehle MUTE hatao.");
      return;
    }
    if (this.recorder.active) {
      this.recorder.stop();
      return;
    }
    this.opts.notice("");
    this.opts.busy(true);
    this.opts.status("listening");
    this.el.flag.classList.add("on");
    this.el.mic.classList.add("recording");
    await this.recorder.start();
  }

  muteClick() {
    const muted = !this.recorder.muted;
    this.recorder.setMuted(muted);
    this.el.mute.classList.toggle("active", muted);
    this.opts.notice(muted ? "Mic band hai. Bolna chahu to MUTE dabao." : "");
    this.stop();
  }

  stop() {
    this.speaker.stop();
    this.el.mic.classList.remove("recording");
    this.el.flag.classList.remove("on");
    this.opts.status("idle");
    this.opts.busy(false);
  }

  onAudio(blob, ms) {
    this.el.flag.classList.remove("on");
    this.el.mic.classList.remove("recording");
    this.opts.status("transcribing");
    this.transcribe(blob, ms);
  }

  async transcribe(blob, ms) {
    // Recording ki asli length browser se. Server 600ms se chhoti recording
    // turant rok deta hai — mic chhoone wala dab dab pehle yahin rok jayega.
    const headers = { "Content-Type": blob.type || "audio/webm", "x-jarvis-token": this.opts.TOKEN };
    if (ms) headers["x-audio-ms"] = String(Math.round(ms));
    try {
      const reply = await fetch("/stt", { method: "POST", headers: headers, body: blob });
      const data = await reply.json().catch(() => ({}));
      if (!reply.ok) {
        this.opts.notice(data.detail || "Sun nahi paya.");
        this.stop();
        return;
      }
      this.opts.status("listening");
      if (!data.text || !data.text.trim()) {
        this.stop();
        return;
      }
      this.opts.sendText(data.text);
    } catch (err) {
      this.opts.notice("Sun nahi paya. Dobara try karo.");
      this.stop();
    }
  }
}
