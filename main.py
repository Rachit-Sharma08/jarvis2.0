import time

import uvicorn

import config
from brain import checkup
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
    log.info("%s starting on %s:%s", config.ASSISTANT_NAME,
             config.SERVER_HOST, config.SERVER_PORT)
    log.info(
        "workspace=%s | tools=%s (UI toggle se ON karo)",
        config.WORKSPACE,
        "ON" if config.TOOLS_ENABLED_DEFAULT else "OFF",
    )
    if not config.has_groq() and not config.has_gemini():
        print("WARNING: .env me koi API key nahi hai. Jawab nahi aayenge.")
    # Halki jaanch: sirf models-list, koi token nahi (aam taur par 2s). Server se PEHLE
    # chalti hai, warna page load hone tak warning taiyaar na hota.
    began = time.perf_counter()
    problems = checkup.run()
    log.info("startup jaanch %.1fs me hui", time.perf_counter() - began)
    for problem in problems:
        print(f"WARNING: {problem}")
    print(f"{config.ASSISTANT_NAME} ready ->  http://localhost:{config.SERVER_PORT}")
    print("Ye ek local personal app hai, sirf is PC par chalta hai.")
    uvicorn.run(
        "server.app:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    # `python main.py --doctor` = sirf jaanch, server nahi. Owner ke liye:
    # "chalega ya nahi?" ka ek command wala jawab (doctor.py).
    import sys

    if "--doctor" in sys.argv[1:]:
        import doctor

        raise SystemExit(doctor.run())
    main()