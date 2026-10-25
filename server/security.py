import secrets

import config
from log_setup import get_logger

log = get_logger("security")

TOKEN_PLACEHOLDER = "__JARVIS_TOKEN__"
TOKEN_HEADER = "x-jarvis-token"

TOKEN = secrets.token_urlsafe(config.TOKEN_BYTES)


def token() -> str:
    """Har server start par naya token. Sirf is page ko milta hai."""
    return TOKEN


def verify_request(request, supplied: str):
    """Har HTTP endpoint ke liye ek hi tarika.

    Headers server/security.py se padhta hai taaki har route par wahi 4 cheez
    (origin/referer/fetch-site/token) jaye — koi route bhool na sake.
    `supplied` alag deta hai kyunki /ws me token query me hota hai.
    """
    return verify(
        request.headers.get("origin", ""),
        request.headers.get("host", ""),
        supplied,
        referer=request.headers.get("referer", ""),
        fetch_site=request.headers.get("sec-fetch-site", ""),
    )


def verify_host(host: str):
    """Sirf localhost aur 127.0.0.1 (DNS rebinding se bachne ke liye)."""
    if host not in config.allowed_hosts():
        log.warning("host reject: %s", host)
        return 400, "Ye server sirf localhost par khulta hai."
    return None


def origin_from_referer(referer: str):
    """Referer se sirf scheme://host:port nikalo (path/query hatao)."""
    if not referer or "://" not in referer:
        return ""
    scheme, _, rest = referer.partition("://")
    host = rest.split("/", 1)[0]
    if not host:
        return ""
    return f"{scheme}://{host}"


def same_origin_proof(origin: str, referer: str, fetch_site: str):
    """Browser ne Origin header kyun nahi bheja — aur kya wo same-origin hai?

    Browser same-origin GET request par `Origin` header BHEJTA HI NAHI (sirf
    POST/PUT/DELETE aur cross-origin request par bhejta hai). Isliye sirf
    `Origin` dekhna galat hoga: `/brain/status` aur `/hud/weather` jaise
    GET hamesha 403 milte, chahe page bilkul apna hi ho.

    Is liye jab Origin khali ho, tabhi do me se koi POSITIVE proof maango:

      1. `Referer` browser ka apna page URL hai, aur wo origin allowed list me ho
      2. `Sec-Fetch-Site: same-origin` — ye header browser khud lagata hai aur
         ek baar ki script/curl `Sec-Fetch-*` ko forge nahi kar sakti (custom
         header bhi browser-origin se hi jaata hai)

    Dono nahi milte to 403 waise hi rahega (khali Origin bina token wala
    koi bhi request andar nahi aayega).
    """
    if origin:
        return origin
    if referer and origin_from_referer(referer) in config.allowed_origins():
        return origin_from_referer(referer)
    if fetch_site == "same-origin":
        return config.SERVER_ORIGIN
    return ""


def verify(origin: str, host: str, supplied: str, referer: str = "", fetch_site: str = ""):
    """Host -> Origin -> Token. Access mile to None, warna (code, message)."""
    bad_host = verify_host(host)
    if bad_host:
        return bad_host

    checked = same_origin_proof(origin, referer, fetch_site)
    if checked not in config.allowed_origins():
        log.warning("origin reject: %s", origin or f"<khali, referer={referer or '-'},"
                                                 f" fetch_site={fetch_site or '-'}>")
        return 403, "Ye page bahar se nahi khulta."

    if not supplied or not secrets.compare_digest(supplied, TOKEN):
        log.warning("token reject (origin=%s)", checked)
        return 401, "Token galat ya missing. Page dobara kholo."

    return None