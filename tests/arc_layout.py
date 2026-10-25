"""Arc theme ka LAYOUT/GEOMETRY hissa — 14-Oct raat me `arccheck.py` se nikla.

Ye file sirf **arc** ki shakal check karti hai (clip, overflow, input bar,
reactor geometry, state label, Hindi typewriter) — har size par.

Split ka wajah: `arccheck.py` 200 cross kar gaya tha (200-line niyam). Ye
`arccheck.py` se alag rakha gaya kyunki ye **dono themes** par nahi chalta —
sirf arc par — jabki theme wala hissa (`?theme=` ka whitelist, default) dono
par chalta hai.

`check`/`FAILED` `arclib` se aate hain (circular import se bachne ke liye
plumbing alag rakha gaya hai).
"""

import arc_probe
from arclib import check, set_state, wait_ready

# Jo viewport check karne hain.
SIZES = ((1366, 768), (1920, 1080))


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

        # State badalne par label badle (app ke apne `setState` se).
        for state, label in arc_probe.STATE_LABEL:
            set_state(page, state)
            page.wait_for_timeout(120)
            check(f"{tag} status {state}", page.evaluate(
                "document.getElementById('a-status-word').textContent"), label)
            check(f"{tag} core {state}", page.evaluate(
                "document.getElementById('a-corestate').textContent"), label)

        # Hindi text — typewriter line par (Devanagari width kaat-te nahi).
        page.evaluate("(t) => window.JARVIS_ARC.typewriter(t)", arc_probe.HINDI)
        page.wait_for_timeout(1400)
        check(f"{tag} Hindi typewriter", page.evaluate(
            "document.getElementById('a-line').textContent"), arc_probe.HINDI)
        check(f"{tag} Hindi line width > 0", page.evaluate(
            "(() => { const e = document.getElementById('a-line');"
            " return Math.round(e.scrollWidth); })()") > 50, True)
        page.screenshot(path=str(out / f"arc_hindi_{w}x{h}.png"))