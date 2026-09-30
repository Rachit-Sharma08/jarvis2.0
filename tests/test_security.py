import importlib
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import config
import main
from server import security

FAILED = []
GOOD_HOST = f"localhost:{config.SERVER_PORT}"
GOOD_ORIGIN = f"http://localhost:{config.SERVER_PORT}"


def check(name, got, want):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def test_bind_address():
    print("LOCAL ONLY BIND")
    check("host 127.0.0.1 hai", config.SERVER_HOST, "127.0.0.1")
    check("host 0.0.0.0 nahi hai", config.SERVER_HOST == "0.0.0.0", False)
    check("local_only true", config.is_local_only(), True)

    config.SERVER_HOST = "0.0.0.0"
    try:
        try:
            main.ensure_local_only()
            check("0.0.0.0 par server chalu nahi hoga", "chalu ho gaya", "ruk gaya")
        except SystemExit:
            check("0.0.0.0 par server chalu nahi hoga", "ruk gaya", "ruk gaya")
    finally:
        config.SERVER_HOST = "127.0.0.1"
    check("phir se normal", main.ensure_local_only(), None)


def test_allowed_lists():
    print("ALLOWED LISTS")
    check("hosts sirf local", config.allowed_hosts(), {GOOD_HOST, f"127.0.0.1:{config.SERVER_PORT}"})
    check(
        "origins sirf local",
        config.allowed_origins(),
        {GOOD_ORIGIN, f"http://127.0.0.1:{config.SERVER_PORT}"},
    )
    check("bahar ka host nahi", "evil.com" in config.allowed_hosts(), False)


def test_token_is_fresh_each_start():
    print("TOKEN")
    old = security.token()
    importlib.reload(security)
    new = security.token()
    check("naya server = naya token", old != new, True)
    check("token lambi hai", len(new) >= 32, True)


def test_verify_rules():
    print("VERIFY")
    good = security.token()
    check("sab sahi -> chalega", security.verify(GOOD_ORIGIN, GOOD_HOST, good), None)
    check("127 bhi chalega", security.verify(f"http://127.0.0.1:{config.SERVER_PORT}", f"127.0.0.1:{config.SERVER_PORT}", good), None)
    check("host galat -> 400", security.verify(GOOD_ORIGIN, "evil.com:8000", good)[0], 400)
    check("host khali -> 400", security.verify(GOOD_ORIGIN, "", good)[0], 400)
    check("origin bahar se -> 403", security.verify("https://evil.com", GOOD_HOST, good)[0], 403)
    check("origin https localhost -> 403", security.verify(f"https://localhost:{config.SERVER_PORT}", GOOD_HOST, good)[0], 403)
    check("origin khali -> 403", security.verify("", GOOD_HOST, good)[0], 403)
    check("token galat -> 401", security.verify(GOOD_ORIGIN, GOOD_HOST, "abc")[0], 401)
    check("token khali -> 401", security.verify(GOOD_ORIGIN, GOOD_HOST, "")[0], 401)
    check("token aadha sahi -> 401", security.verify(GOOD_ORIGIN, GOOD_HOST, good[:-1] + "x")[0], 401)


def test_http_rules():
    print("HTTP (/chat aur /)")
    token = security.token()
    client = TestClient(__import__("server.app", fromlist=["app"]).app)

    ok = {"host": GOOD_HOST, "origin": GOOD_ORIGIN, "x-prabh-token": token}

    page = client.get("/", headers={"host": GOOD_HOST})
    check("page khuli", page.status_code, 200)
    check("page me token hai", token in page.text, True)
    check("placeholder gaya", "__PRABH_TOKEN__" in page.text, False)

    check("page: host check", client.get("/", headers={"host": "evil.com"}).status_code, 400)

    good = client.post("/chat", json={"text": "hi"}, headers=ok)
    check("sahi token se /chat", good.status_code, 200)
    check("koi CORS header nahi", "access-control-allow-origin" in good.headers, False)

    no_token = {"host": GOOD_HOST, "origin": GOOD_ORIGIN}
    check("/chat bina token", client.post("/chat", json={"text": "hi"}, headers=no_token).status_code, 401)
    check("/chat galat token", client.post("/chat", json={"text": "hi"}, headers={**ok, "x-prabh-token": "abc"}).status_code, 401)
    check("/chat bahar se", client.post("/chat", json={"text": "hi"}, headers={**ok, "origin": "https://evil.com"}).status_code, 403)
    check("/chat bina origin", client.post("/chat", json={"text": "hi"}, headers={"host": GOOD_HOST, "x-prabh-token": token}).status_code, 403)
    check("/chat fake host", client.post("/chat", json={"text": "hi"}, headers={**ok, "host": "evil.com"}).status_code, 400)
    return client


def test_websocket_rules(client):
    print("WEBSOCKET (/ws)")
    token = security.token()

    with client.websocket_connect(f"/ws?token={token}", headers={"host": GOOD_HOST, "origin": GOOD_ORIGIN}) as sock:
        check("sahi token se /ws", sock.receive_json(), {"type": "status", "value": "idle"})

    for name, url, headers in [
        ("bina token", "/ws", {"host": GOOD_HOST, "origin": GOOD_ORIGIN}),
        ("galat token", "/ws?token=abc", {"host": GOOD_HOST, "origin": GOOD_ORIGIN}),
        ("bahar se", f"/ws?token={token}", {"host": GOOD_HOST, "origin": "https://evil.com"}),
        ("fake host", f"/ws?token={token}", {"host": "evil.com", "origin": GOOD_ORIGIN}),
    ]:
        rejected = False
        try:
            with client.websocket_connect(url, headers=headers) as sock:
                sock.receive_json()
        except Exception:
            rejected = True
        check(f"/ws {name} -> band", rejected, True)


test_bind_address()
test_allowed_lists()
test_token_is_fresh_each_start()
test_verify_rules()
http_client = test_http_rules()
test_websocket_rules(http_client)

print()
if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Saare security test pass.")