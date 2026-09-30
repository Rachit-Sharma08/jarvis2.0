import uvicorn

import config
from log_setup import get_logger

log = get_logger("main")


def main() -> None:
    log.info("Prabh starting on %s:%s", config.SERVER_HOST, config.SERVER_PORT)
    if not config.has_groq() and not config.has_gemini():
        print("WARNING: .env me koi API key nahi hai. Jawab nahi aayenge.")
    print(f"Prabh ready ->  http://localhost:{config.SERVER_PORT}")
    uvicorn.run(
        "server.app:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()