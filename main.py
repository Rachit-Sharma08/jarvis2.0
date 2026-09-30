import uvicorn

import config
from log_setup import get_logger

log = get_logger("main")


def ensure_local_only() -> None:
    if not config.is_local_only():
        log.error("SERVER_HOST=%s allowed nahi hai", config.SERVER_HOST)
        raise SystemExit(
            "Ye app sirf localhost par chalne ke liye hai. "
            "config.py me SERVER_HOST = '127.0.0.1' rakho."
        )


def main() -> None:
    ensure_local_only()
    config.ensure_workspace()
    log.info("Prabh starting on %s:%s", config.SERVER_HOST, config.SERVER_PORT)
    log.info(
        "workspace=%s | tools=%s (UI toggle se ON karo)",
        config.WORKSPACE,
        "ON" if config.TOOLS_ENABLED_DEFAULT else "OFF",
    )
    if not config.has_groq() and not config.has_gemini():
        print("WARNING: .env me koi API key nahi hai. Jawab nahi aayenge.")
    print(f"Prabh ready ->  http://localhost:{config.SERVER_PORT}")
    print("Ye ek local personal app hai, sirf is PC par chalta hai.")
    uvicorn.run(
        "server.app:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()