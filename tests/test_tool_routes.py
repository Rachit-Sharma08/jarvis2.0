"""Tool endpoints ka test: security, Allow/Deny, kill switch, CSP.

Koi tool yahan ASLI me nahi chalta — sirf endpoints aur gatekeeper.
"""

import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

import config
from gatekeeper import keeper
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


def headers(token):
    return {"host": GOOD_HOST, "origin": GOOD_ORIGIN, "x-prabh-token": token}


def test_security_on_tool_endpoints(client):
    print("TOOL ENDPOINTS KI SECURITY")
    token = security.token()
    ok = headers(token)

    check(
        "/tools/toggle bina token",
        client.post("/tools/toggle", json={"on": True}, headers={"host": GOOD_HOST, "origin": GOOD_ORIGIN}).status_code,
        401,
    )
    check(
        "/tool/confirm bahar se",
        client.post("/tool/confirm", json={"id": "a", "hash": "b", "allow": True}, headers={**ok, "origin": "https://evil.com"}).status_code,
        403,
    )
    check(
        "/tools/toggle fake host",
        client.post("/tools/toggle", json={"on": True}, headers={**ok, "host": "evil.com"}).status_code,
        400,
    )
    check(
        "/tools/cancel bina token",
        client.post("/tools/cancel", headers={"host": GOOD_HOST, "origin": GOOD_ORIGIN}).status_code,
        401,
    )
    check(
        "/tools/status bina token",
        client.post("/tools/status", headers={"host": GOOD_HOST, "origin": GOOD_ORIGIN}).status_code,
        401,
    )


def test_toggle(client):
    print("KILL SWITCH")
    token = security.token()
    ok = headers(token)

    keeper.set_tools(False)
    reply = client.post("/tools/toggle", json={"on": False}, headers=ok)
    check("toggle off", reply.json()["tools_on"], False)

    denied, reason = keeper.review("get_time_date", {}, "sunday")
    check("off par sab block", denied, "deny")
    check("wajah saaf hai", "TOOLS OFF" in reason, True)

    reply = client.post("/tools/toggle", json={"on": True}, headers=ok)
    check("toggle on", reply.json()["tools_on"], True)
    status = client.post("/tools/status", headers=ok).json()
    check("status me tools_on", status["tools_on"], True)
    check("limit 20", status["limit"], config.TOOL_MAX_CALLS_PER_MINUTE)
    keeper.set_tools(True)


def test_confirm_endpoint(client):
    print("ALLOW / DENY ENDPOINT")
    token = security.token()
    ok = headers(token)

    keeper.APPROVALS.open("run_command", {"command": "echo hi"})
    card = keeper.APPROVALS.current()
    check("card id bana", bool(card.id), True)
    check("card hash bana", len(card.hash) == 16, True)

    bad = client.post("/tool/confirm", json={"id": card.id, "hash": "wrong", "allow": True}, headers=ok)
    check("galat hash -> 409", bad.status_code, 409)
    check("abhi bhi pending", keeper.APPROVALS.busy(), True)

    fake = client.post("/tool/confirm", json={"id": "fake", "hash": card.hash, "allow": True}, headers=ok)
    check("galat id -> 409", fake.status_code, 409)

    good = client.post("/tool/confirm", json={"id": card.id, "hash": card.hash, "allow": False}, headers=ok)
    check("sahi hash -> 200", good.status_code, 200)
    check("faisla deny", good.json()["decision"], "deny")

    again = client.post("/tool/confirm", json={"id": card.id, "hash": card.hash, "allow": True}, headers=ok)
    check("dobara use -> 409", again.status_code, 409)
    check("card pending nahi", keeper.APPROVALS.busy(), False)


def test_cancel(client):
    print("STOP / CANCEL")
    token = security.token()
    keeper.APPROVALS.open("write_file", {"path": "a", "content": "b"})
    check("card pending", keeper.APPROVALS.busy(), True)
    data = client.post("/tools/cancel", headers=headers(token)).json()
    check("card cancel hua", data["card_cancelled"], True)
    check("ab pending nahi", keeper.APPROVALS.busy(), False)


def test_csp_header(client):
    print("CSP AUR SCRIPT")
    token = security.token()
    page = client.get("/", headers={"host": GOOD_HOST})
    csp = page.headers.get("content-security-policy", "")
    check("CSP header laga", bool(csp), True)
    check("default-src self", "default-src 'self'" in csp, True)
    check("script-src self", "script-src 'self'" in csp, True)
    check("object-src none", "object-src 'none'" in csp, True)
    check("frame-ancestors none", "frame-ancestors 'none'" in csp, True)
    check("nosniff", page.headers.get("x-content-type-options"), "nosniff")
    check(
        "inline script nahi (CSP ke liye)",
        "<script>window.PRABH_TOKEN" in page.text,
        False,
    )
    check("token meta tag me", 'name="prabh-token"' in page.text, True)
    check("token page me hai", token in page.text, True)

    chat = client.post("/chat", json={"text": "hi"}, headers=headers(token))
    check("chat par bhi CSP", "default-src 'self'" in chat.headers.get("content-security-policy", ""), True)


def test_ui_uses_textcontent():
    print("UI SURAKSHA (source check)")
    ui = (config.UI_DIR)
    for name in ("app.js", "tools.js"):
        source = (ui / name).read_text(encoding="utf-8")
        check(f"{name}: innerHTML nahi", "innerHTML" in source, False)
        check(f"{name}: outerHTML nahi", "outerHTML" in source, False)
        check(f"{name}: insertAdjacentHTML nahi", "insertAdjacentHTML" in source, False)
        check(f"{name}: eval nahi", "eval(" in source, False)
    tools_js = (ui / "tools.js").read_text(encoding="utf-8")
    check("tools.js: textContent hai", "textContent" in tools_js, True)
    check("Allow/Deny par isTrusted check", "isTrusted" in tools_js, True)


def test_no_dangerous_endpoints():
    print("KHATARNAK ENDPOINT NAHI")
    from server.app import app

    paths = set(app.openapi()["paths"])
    check("/shell nahi", "/shell" in paths, False)
    check("/exec nahi", "/exec" in paths, False)
    check("/env nahi", "/env" in paths, False)
    check("/tool/confirm hai", "/tool/confirm" in paths, True)
    check("/tools/toggle hai", "/tools/toggle" in paths, True)
    check("/tools/cancel hai", "/tools/cancel" in paths, True)
    check("/stt voice bhi hai", "/stt" in paths, True)


client = TestClient(__import__("server.app", fromlist=["app"]).app)
test_security_on_tool_endpoints(client)
test_toggle(client)
test_confirm_endpoint(client)
test_cancel(client)
test_csp_header(client)
test_ui_uses_textcontent()
test_no_dangerous_endpoints()

print()
if FAILED:
    print(f"{len(FAILED)} test fail: {FAILED}")
    sys.exit(1)
print("Saare tool route test pass.")
