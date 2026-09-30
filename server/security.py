import secrets

import config
from log_setup import get_logger

log = get_logger("security")

TOKEN_PLACEHOLDER = "__PRABH_TOKEN__"
TOKEN_HEADER = "x-prabh-token"

TOKEN = secrets.token_urlsafe(config.TOKEN_BYTES)


def token() -> str:
    """Har server start par naya token. Sirf is page ko milta hai."""
    return TOKEN


def verify_host(host: str):
    """Sirf localhost aur 127.0.0.1 (DNS rebinding se bachne ke liye)."""
    if host not in config.allowed_hosts():
        log.warning("host reject: %s", host)
        return 400, "Ye server sirf localhost par khulta hai."
    return None


def verify(origin: str, host: str, supplied: str):
    """Host -> Origin -> Token. Access mile to None, warna (code, message)."""
    bad_host = verify_host(host)
    if bad_host:
        return bad_host

    if origin not in config.allowed_origins():
        log.warning("origin reject: %s", origin or "<khali>")
        return 403, "Ye page bahar se nahi khulta."

    if not supplied or not secrets.compare_digest(supplied, TOKEN):
        log.warning("token reject (origin=%s)", origin)
        return 401, "Token galat ya missing. Page dobara kholo."

    return None