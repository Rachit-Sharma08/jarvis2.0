const MAX_SECONDS = 30;
const MIN_MS = 600;

class Recorder {
  constructor(onDone, onError) {
    this.onDone = onDone;
    this.onError = onError;
    this.stream = null;
    this.recorder = null;
    this.chunks = [];
    this.timer = null;
    this.muted = false;
    // Round 2: recording ki asli length yahan gino. Server par timer nahi —
    // wahan network latency jud kar galat ms aata tha. <600ms wahi dab dab hai.
    this.startedAt = 0;
  }

  get active() {
    return this.recorder !== null && this.recorder.state === "recording";
  }

  async start() {
    if (this.active || this.muted) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      this.onError("Ye browser mic support nahi karta. Chrome ya Edge use karo.");
      return;
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      this.onError(
        err && err.name === "NotAllowedError"
          ? "Mic ki permission nahi mili. Browser me allow karo."
          : "Mic nahi mila. Plug lagao ya dusra mic chuno."
      );
      return;
    }

    try {
      this.chunks = [];
      this.recorder = new MediaRecorder(this.stream);
    } catch (err) {
      this.release();
      this.onError("Recording start nahi hui: " + err.message);
      return;
    }

    this.recorder.ondataavailable = (e) => { if (e.data.size) this.chunks.push(e.data); };
    this.recorder.onstop = () => {
      const type = this.recorder ? this.recorder.mimeType : "";
      const ms = this.elapsedMs();
      const blob = new Blob(this.chunks, { type: type || "audio/webm" });
      this.release();
      if (!blob.size) return;
      if (ms < MIN_MS) {
        this.onError("Bahut chhoti recording. Thodi der bolke try karo.");
        return;
      }
      this.onDone(blob, ms);
    };

    this.recorder.start();
    this.startedAt = Date.now();
    this.timer = setTimeout(() => this.stop(), MAX_SECONDS * 1000);
  }

  elapsedMs() {
    return this.startedAt ? Date.now() - this.startedAt : 0;
  }

  stop() {
    clearTimeout(this.timer);
    this.timer = null;
    if (this.recorder && this.recorder.state !== "inactive") {
      this.recorder.stop();
    } else {
      this.release();
    }
  }

  setMuted(muted) {
    this.muted = muted;
    this.stop();
    this.release();
  }

  release() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    this.recorder = null;
    this.startedAt = 0;
  }
}