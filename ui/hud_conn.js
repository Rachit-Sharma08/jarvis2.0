// hud_conn.js — /brain/status poll + server-reload (app.js <200 niyam).
// Ye theme alag hai: SYSTEM pill ka poll + page ka reboot glue yahin rahta hai.
const Conn = (() => {
  let reconnecting = false;
  let closing = false;
  window.addEventListener("beforeunload", () => { closing = true; });

  function notice(text) {
    const el = document.getElementById("notice");
    if (el) el.textContent = text;
  }

  // Server restart par naya token banta hai. Purana page har request par 401
  // deta hai aur "connection toot gaya" par atak jaata hai (live bug, 26-Oct).
  // Server wapas aate hi page reload karo - naya token HTML ke saath aata hai.
  function reload() {
    if (reconnecting || closing) return;
    reconnecting = true;
    notice("Server se connection toot gaya. Reconnect kar raha hoon...");
    const retry = () => fetch("/", { cache: "no-store" })
      .then((reply) => {
        if (!reply.ok) throw new Error("http " + reply.status);
        location.reload();
      })
      .catch(() => setTimeout(retry, 2000));
    setTimeout(retry, 1000);
  }

  // ---- /brain/status: SYSTEM ONLINE/DEGRADED + provider/model; 401 = reload
  async function poll(token) {
    try {
      const reply = await fetch("/brain/status", {
        headers: { "x-jarvis-token": token },
        cache: "no-store"
      });
      if (reply.status === 401) {
        reload();
        return;
      }
      if (!reply.ok) throw new Error("http " + reply.status);
      window.JARVIS_STATUS.render(await reply.json());
    } catch (err) {
      window.JARVIS_STATUS.clearProvider();
    }
  }

  function start(token) {
    poll(token);
    setInterval(() => poll(token), 15000);
  }

  return { reload: reload, start: start };
})();

window.JARVIS_CONN = Conn;
