import config
from brain import router
from core import events, modes
from log_setup import get_logger

log = get_logger("engine")

MAX_TURNS = 20


class Engine:
    def __init__(self):
        self.mode = config.DEFAULT_MODE
        self.history = []

    def run_tool(self, name: str, args: dict) -> str:
        """Only one path for running tools. Gatekeeper will sit here later."""
        log.info("tool blocked (none exist yet): %s", name)
        return "Abhi koi tool available nahi hai."

    def handle(self, text: str):
        """Message aaya -> mode chuna -> brain se jawab -> events."""
        yield events.status("listening")

        if not text or not text.strip():
            yield events.log("khaali message bheja gaya", "warn")
            yield events.status("idle")
            return

        new_mode, clean_text = modes.detect_mode(text, self.mode)
        if new_mode != self.mode:
            self.history.clear()
            log.info("mode %s -> %s", self.mode, new_mode)
            self.mode = new_mode
            yield events.log(
                f"mode badla: {modes.display_name(new_mode)}", data={"mode": new_mode}
            )

        self.history.append({"role": "user", "content": clean_text})
        yield events.message("user", clean_text)
        self._trim()
        yield events.status("thinking")

        try:
            answer, brain_name = router.ask(self.history, modes.persona_for(self.mode))
        except Exception as exc:
            log.error("engine: brain crash: %s: %s", type(exc).__name__, exc)
            answer = "Kuch gadbad ho gayi. Dobara try karo."
            brain_name = "none"

        self.history.append({"role": "assistant", "content": answer})
        self._trim()
        yield events.log(f"jawab {brain_name} se aaya")
        yield events.message("assistant", answer)
        yield events.status("speaking")
        yield events.status("idle")

    def _trim(self):
        if len(self.history) > MAX_TURNS:
            self.history = self.history[-MAX_TURNS:]