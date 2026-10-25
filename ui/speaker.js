class Speaker {
  constructor(token, onError, onStart, onEnd) {
    this.token = token;
    this.onError = onError;
    this.onStart = onStart;
    this.onEnd = onEnd;
    this.audio = null;
  }

  async speak(text, mode) {
    this.stop();
    let reply;
    try {
      reply = await fetch("/tts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-jarvis-token": this.token,
        },
        body: JSON.stringify({ text, mode }),
      });
    } catch (err) {
      this.onError("Server se baat nahi ho payi.");
      return;
    }

    if (!reply.ok) {
      let detail = "Awaaz nahi ban paayi.";
      try {
        const data = await reply.json();
        if (data && data.detail) detail = data.detail;
      } catch (err) {
        detail = "Awaaz nahi ban paayi.";
      }
      this.onError(detail);
      return;
    }

    const provider = reply.headers.get("x-tts-provider") || "unknown";
    const blob = await reply.blob();
    this.audio = new Audio(URL.createObjectURL(blob));
    this.audio.onended = () => { this.cleanup(); this.onEnd(); };
    this.onStart(provider);

    try {
      await this.audio.play();
    } catch (err) {
      this.onError("Awaaz chalane ke liye kahin click karo.");
      this.cleanup();
      this.onEnd();
    }
  }

  stop() {
    if (!this.audio) return;
    this.audio.onended = null;
    this.audio.pause();
    this.audio.currentTime = 0;
    this.cleanup();
    this.onEnd();
  }

  cleanup() {
    if (this.audio && this.audio.src && this.audio.src.startsWith("blob:")) {
      URL.revokeObjectURL(this.audio.src);
    }
    this.audio = null;
  }
}