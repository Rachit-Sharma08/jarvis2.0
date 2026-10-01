"""Phase 4 HUD — same-origin GET ka security rule.

Ye ek alag file hai kyunki ye rule Phase 3 ke baad hi pata chala: browser
same-origin GET request par `Origin` header BHEJTA HI NAHI (sirf POST/PUT/
DELETE aur cross-origin request par bhejta hai).

Sirf `Origin` dekhne se `/brain/status` aur `/hud/weather` hamesha 403 milte —
jiska matlab browser me wo dono kabhi chalti hi nahi. Ab Origin khali ho to
do me se koi positive proof chahiye:

  1. `Referer` browser ka apna page URL ho, aur wo allowed origin list me ho
  2. `Sec-Fetch-Site: same-origin` — ye browser khud lagata hai

Proof me se koi na ho to 403 waise hi rehta hai. `Referrer-Policy:
same-origin` bhi zaroori hai warna browser Referer bhejega hi nahi.
"""

from hud_common import GOOD_HOST, GOOD_ORIGIN, check, headers
from server import security


def test_same_origin_get(client):
    print("SAME-ORIGIN GET (Referer / Sec-Fetch-Site)")
    token = security.token()
    host = {"host": GOOD_HOST, "x-prabh-token": token}

    # 1. bilkul kuch nahi -> 403 (purana strict rule)
    check("koi proof nahi -> 403",
          client.get("/hud/weather", headers=host).status_code, 403)

    # 2. browser same-origin GET: Origin khali, Referer apna page -> 200
    check("referer se andar",
          client.get("/hud/weather", headers={**host, "referer": GOOD_ORIGIN + "/"}).status_code, 200)

    # 3. Sec-Fetch-Site proof se bhi andar
    check("sec-fetch-site se andar",
          client.get("/hud/weather", headers={**host, "sec-fetch-site": "same-origin"}).status_code, 200)

    # 4. cross-site fetch -> 403
    check("cross-site -> 403",
          client.get("/hud/weather", headers={**host, "sec-fetch-site": "cross-site"}).status_code, 403)

    # 5. bhali Referer -> 403
    check("bad referer -> 403",
          client.get("/hud/weather", headers={**host, "referer": "https://evil.com/"}).status_code, 403)

    # 6. referer sahi hai, phir bhi token chahiye (proof kafi nahi)
    check("referer par bina token -> 401",
          client.get("/hud/weather", headers={"host": GOOD_HOST, "referer": GOOD_ORIGIN + "/"}).status_code, 401)

    # brain/status bhi wahi rule (live browser me 403 tha)
    check("/brain/status referer se andar",
          client.get("/brain/status", headers={**host, "referer": GOOD_ORIGIN + "/"}).status_code, 200)

    # Referrer-Policy same-origin hona zaroori hai, warna Referer aayega hi nahi
    check("Referrer-Policy same-origin",
          client.get("/", headers={"host": GOOD_HOST}).headers.get("referrer-policy"),
          "same-origin")


def test_verify_helper():
    """`verify()` ka naya signature teeno rasta ek jaisa chalna chahiye."""
    print("VERIFY HELPER (origin_from_referer / same_origin_proof)")
    good = security.token()

    check("referer se origin bana",
          security.origin_from_referer("http://localhost:8000/hud/stats"),
          f"http://localhost:{GOOD_HOST.split(':')[1]}")
    check("path hat jaata hai",
          security.origin_from_referer(f"http://127.0.0.1:{GOOD_HOST.split(':')[1]}/a/b?c=1"),
          f"http://127.0.0.1:{GOOD_HOST.split(':')[1]}")
    check("khaali referer", security.origin_from_referer(""), "")
    check("bina :// wala", security.origin_from_referer("localhost:8000"), "")

    # direct verify() call: referer de ke andar jaana chahiye
    denied = security.verify("", GOOD_HOST, good, referer=GOOD_ORIGIN + "/")
    check("verify() referer se None", denied, None)
    denied = security.verify("", GOOD_HOST, good)
    check("verify() bina proof 403", denied[0], 403)
    denied = security.verify("https://evil.com", GOOD_HOST, good,
                             referer=GOOD_ORIGIN + "/")
    check("verify() bad origin phir bhi 403", denied[0], 403)


def run(client):
    test_same_origin_get(client)
    test_verify_helper()