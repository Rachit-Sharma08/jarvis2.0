"""KAAM B — Arc Reactor theme ka Playwright check (browser me, nakli data).

Ye check karta hai:
1. 1366x768 + 1920x1080 par koi clip/overflow nahi.
2. Input bar (`.a-dock`) dono size par poori dikh rahi hai.
3. Reactor SVG ka **asli geometry** (`getBBox()` > 0) — na ki sirf "svg tag
   maujood hai". (Namespace wala asli bug yahin pakda: tag to tha, par
   `getBBox()` sab 0x0 tha.)
4. State badalne par label badle.
5. Hindi (Devanagari) text typewriter line par sahi baithta hai.
6. Default (bina `?theme=`) = purana neela HUD, aur `?theme=` whitelist.

JS probes `arc_probe.py` me hain (200-line niyam). Screenshot
`%TEMP%\\opencode\\hudshots` me — repo me NAHI.
"""

import tempfile
from pathlib import Path

import arc_probe
from hudserve import FakeHud

FAILED = []

SIZES = ((1366, 768), (1920, 1080))


def check(name, got, want=True):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def shots_dir() -> Path:
    base = Path(tempfile.gettempdir()) / "opencode" / "hudshots"
    base.mkdir(parents=True, exist_ok=True)
    return base


def wait_ready(page):
    """Arc tab POORA boot ho jaaye.

    `arc_load.js` `<head>` me hai aur CSS/JS DOMContentLoaded par lagata hai,
    is liye `load` ke turant baad `window.PRABH_ARC` shayad na bana ho. Ek
    fixed `wait_for_timeout` guess tha aur 1920x1080 par boot miss ho gaya —
    is liye ab hum **condition** ka intezaar karte hain, time ka nahi.
    """
    page.wait_for_function("() => !!window.PRABH_ARC && !!document.querySelector('.a-reactor')",
                           timeout=15000)
    page.wait_for_timeout(250)      # ek frame CSS/animation ke liye


def set_state(page, state):
    """Asli `setState` se call — DOM ko haath se nahi badalte."""
    page.evaluate("(s) => window.PRABH_ARC_LIVE.setState(s)", state)


def run_theme(page, url, out):
    print("ARC THEME (headless, nakli data)")
    for w, h in SIZES:
        page.set_viewport_size({"width": w, "height": h})
        page.goto(url, wait_until="load")
        wait_ready(page)
        tag = f"{w}x{h}"

        fits = page.evaluate(arc_probe.FITS, list(arc_probe.MUST_FIT))
        check(f"{tag} clip nahi", fits["cut"], [])
        check(f"{tag} overflow nahi", fits["overflow"], [0, 0])

        # Input bar poori dikhe (spec: 1366x768 par saaf).
        dock = page.evaluate(
            "(() => { const e = document.querySelector('.a-dock');"
            " if (!e) return null; const b = e.getBoundingClientRect();"
            " return [Math.round(b.width), Math.round(b.height)]; })()")
        check(f"{tag} input bar hai", bool(dock and dock[0] > 200 and dock[1] > 20), True)

        # Reactor ka ASLI geometry — tag hone se kaam nahi chalta.
        geo = page.evaluate(arc_probe.GEOMETRY)
        check(f"{tag} reactor size", geo["svg"] >= 150, True)
        for sel in arc_probe.PARTS:
            # `.get(...)` — missing key par `KeyError` se test **crash** ho
            # jaata tha (suite ruk jaati, wajah adhoori). Missing ko 0
            # maankar FAIL dena chahiye, crash nahi.
            check(f"{tag} {sel} geometry", geo["parts"].get(sel, 0) > 0, True)
        page.screenshot(path=str(out / f"arc_{w}x{h}.png"))

        # State badalne par label badle.
        for state, label in arc_probe.STATE_LABEL:
            set_state(page, state)
            page.wait_for_timeout(120)
            check(f"{tag} status {state}", page.evaluate(
                "document.getElementById('a-status-word').textContent"), label)
            check(f"{tag} core {state}", page.evaluate(
                "document.getElementById('a-corestate').textContent"), label)

        # Hindi text — typewriter line par.
        page.evaluate("(t) => window.PRABH_ARC.typewriter(t)", arc_probe.HINDI)
        page.wait_for_timeout(1400)
        check(f"{tag} Hindi typewriter", page.evaluate(
            "document.getElementById('a-line').textContent"), arc_probe.HINDI)
        check(f"{tag} Hindi line width > 0", page.evaluate(
            "(() => { const e = document.getElementById('a-line');"
            " return Math.round(e.scrollWidth); })()") > 50, True)
        page.screenshot(path=str(out / f"arc_hindi_{w}x{h}.png"))


def run_default(page, url):
    """Default (bina `?theme=`) = purana neela HUD. Test koi bhi na ho."""
    print("DEFAULT THEME (neela — purana HUD)")
    page.set_viewport_size({"width": 1366, "height": 768})
    page.goto(url, wait_until="load")
    page.wait_for_timeout(700)
    check("neela: purana .hud hai", page.evaluate(
        "getComputedStyle(document.querySelector('.hud')).display") != "none", True)
    check("neela: arc chhupa", page.evaluate("!!document.querySelector('.a-root')"), False)
    check("neela: data-theme", page.evaluate(
        "document.documentElement.getAttribute('data-theme')"), "neon")


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
            run_theme(page, hud.url + "?theme=arc", out)
            check("koi JS error nahi", errors, [])
            check("screenshot repo ke bahar",
                  str(out).startswith(tempfile.gettempdir()), True)
        finally:
            page.close()
            browser.close()
    print(f"  (screenshot: {out})")