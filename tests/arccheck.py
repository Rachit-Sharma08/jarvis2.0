"""KAAM B — Arc Reactor theme ka Playwright check (browser me, nakli data).

Ye file `test_hud_arc.py` se chalti hai, sirf wiring + **theme** wale checks
karti hai. Baaki do hisse alag hain (14-Oct raat me 200-line niyam):

- `arclib.py`    — shared plumbing (`check`, `FAILED`, `wait_ready`, ...)
- `arc_layout.py` — clip/overflow/geometry/state/Hindi (sirf arc par)
- `arccheck.py` (ye) — default + `?theme=` whitelist (dono themes par)

Ye check karta hai:
1. Default (bina `?theme=`) = **asli config ka default**.
2. `?theme=arc` aur `?theme=neon` dono poore chalte hain.
3. `?theme=<adhoora>` reject hota hai (attribute injection — XSS).

**NAYA (14-Oct raat):** default `"neon"` se `"arc"` kar diya gaya (owner's
faisla). Is liye yahan koi theme **hard-code nahi** — `EXPECTED_DEFAULT`
`test_hud_arc.py` se `config.hud_theme()` ke through aata hai, aur nakli
server ka `DEFAULT_THEME` bhi wahin se bharta hai. Test ab asli config ke
khilaf hai, khayali value ke khilaf nahi.

**Pakka niyam:** default badalne par sirf test ka `want` mat badlo — uske
saath **doosre theme ka bhi raasta check karo** (`?theme=neon` wala check
yahi hai). Warna default flip karte hi pata hi nahi chalega ki purana look
phat se toota ya nahi — aur test chup-chaap pass rahega kyunki uske saare
selectors maujood hi nahi honge.

JS probes `arc_probe.py` me hain. Screenshot `%TEMP%\\opencode\\hudshots`
me — repo me NAHI.
"""

import tempfile

import arc_layout
import arc_probe
import hudserve
from arclib import FAILED, check, shots_dir, visible_css  # noqa: F401 (FAILED re-export)
from hudserve import FakeHud

# `test_hud_arc.py` ise `config.hud_theme()` se bharta hai. Khaali rahe to
# nakli server ka default maana jaata hai (self-check).
EXPECTED_DEFAULT = ""


def hudserve_theme_default():
    """Nakli server ka default theme — `hudserve.DEFAULT_THEME` se.

    Ye sirf **fallback** hai (jab `EXPECTED_DEFAULT` khaali ho). Asli maan
    rahe hue value test runner ke `config.hud_theme()` se aati hai. `hudserve`
    khud config import nahi karta — `.env` se bachne ke liye.
    """
    return hudserve.DEFAULT_THEME or "neon"


def _own_other(want):
    """Theme ke hisse se `(dikhne-wala, chhupne-wala)` selector jodi.

    Dono theme alag-alag DOM root rakhte hain: arc ka `.a-root`, purane
    neon ka `.hud`. Is liye har check ke liye pata hona zaroori hai ki
    default kaun sa hai.
    """
    if want == "arc":
        return ".a-root", ".hud"
    return ".hud", ".a-root"


def _hidden_want(other):
    """Chhupne wale selector ka expected hissa — dono alag hain.

    - `.a-root` (arc ka root) neon ke neeche **DOM me hota hi nahi** — arc
      ka JS chalta hi nahi, to `visible_css()` `"absent"` deta hai.
    - `.hud` (neon ka root) arc ke neeche **DOM me rehta hai**, sirf CSS
      `display:none` karta hai — to `"none"` milta hai.

    Ye do alag hain, is liye ek jaisa `"absent"` maanna galat hoga. Ye galti
    split ke waqt hui thi — test ne pakad liya (2 fail), is liye test sahi
    hai.
    """
    return "absent" if other == ".a-root" else "none"


def run_default(page, url):
    """Default (bina `?theme=`) = **asli** default, aur dono themes kholte hain.

    Default ab `"arc"` hai, par purana `"neon"` bhi poora hai — ye check
    dono ko `?theme=` se kholta hai, taaki default flip karne par pata chale
    ki doosra theme toota ya nahi.
    """
    want = EXPECTED_DEFAULT or hudserve_theme_default()
    print(f"DEFAULT THEME ({want})")
    page.set_viewport_size({"width": 1366, "height": 768})

    page.goto(url, wait_until="load")
    page.wait_for_timeout(700)
    check("default: data-theme", page.evaluate(
        "document.documentElement.getAttribute('data-theme')"), want)

    own, other = _own_other(want)
    check(f"default: {own} dikha", visible_css(page, own), "shown")
    check(f"default: {other} chhupa", visible_css(page, other), _hidden_want(other))

    # --- Ab dono themes `?theme=` se poori tarah kholte hain (regression) ---
    for name in ("arc", "neon"):
        own, other = _own_other(name)
        page.goto(url + "?theme=" + name, wait_until="load")
        page.wait_for_timeout(700)
        check(f"?theme={name}: data-theme", page.evaluate(
            "document.documentElement.getAttribute('data-theme')"), name)
        check(f"?theme={name}: {own} dikha", visible_css(page, own), "shown")
        check(f"?theme={name}: {other} chhupa", visible_css(page, other),
              _hidden_want(other))


def run_micro(page, url):
    """`?theme=<adhoora>` = default par girna chahiye (attribute injection)."""
    print("THEME WHITELIST")
    for bad in arc_probe.BAD_QUERIES:
        page.goto(url + "?" + bad, wait_until="domcontentloaded")
        got = page.evaluate("document.documentElement.getAttribute('data-theme')")
        check(f"adhoori value reject ({bad[:18]})", got in ("neon", "arc"), True)
    page.goto(url + "?" + arc_probe.GOOD_QUERY, wait_until="domcontentloaded")
    check("ARC (bade akshar) chalta hai", page.evaluate(
        "document.documentElement.getAttribute('data-theme')"), "arc")


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP: Playwright install nahi hai.")
        return
    out = shots_dir()
    with FakeHud() as hud, sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        errors = []
        page.on("pageerror",
                lambda e: errors.append(getattr(e, "stack", None) or str(e)))
        try:
            run_default(page, hud.url)
            run_micro(page, hud.url)
            arc_layout.run_theme(page, hud.url + "?theme=arc", out)
            check("koi JS error nahi", errors, [])
            check("screenshot repo ke bahar",
                  str(out).startswith(tempfile.gettempdir()), True)
        finally:
            page.close()
            browser.close()
    print(f"  (screenshot: {out})")