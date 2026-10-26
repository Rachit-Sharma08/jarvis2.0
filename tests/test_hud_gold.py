"""Gold HUD ka Playwright test — theme whitelist + orb geometry + state.

Pehle ye kaam `test_hud_arc.py` + 4 helper files karta tha (do theme the).
Ab ek hi theme hai ("gold"), is liye sab kuch ek file me — 200-line niyam ke
andar. Purane arc helpers (`arccheck`/`arc_probe`/`arclib`/`arc_layout`)
delete ho gaye.

Kya check hota hai:
1. Default (bina `?theme=`) = **asli config ka default** (`config.hud_theme()`).
2. `?theme=<adhoora>` reject hota hai (attribute injection — XSS).
3. Orb ke asli layers bane hain (`getBBox()` > 0 — SVG namespace bug yahin
   pakda jaata tha).
4. App ke apne `JARVIS_ORB.setState()` se label badalta hai.
5. Koi JS error nahi, screenshot repo ke bahar.

Playwright na ho to SKIP (suite fail nahi hota) — browser-free check
`hud_check_ui.py` me hai.
"""

import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests import logsafe  # noqa: E402,F401  (test ka apna log)

import config  # noqa: E402  (logsafe ke BAAD — isi order ka niyam hai)
import hudserve  # noqa: E402
from hudserve import FakeHud  # noqa: E402

FAILED = []

# Attribute-injection ke pakkaure — in sab par `data-theme` sirf "gold" ho.
BAD_QUERIES = (
    "theme=<script>",
    "theme=neon",                       # purana theme, ab valid nahi
    "theme=" + "x" * 40,
    'theme=gold%22%20onload%3Dalert(1)',
)

# Orb ke hisse — har ek ka geometry > 0 hona chahiye. `getBBox()` asli draw
# proof hai; DOM me tag hona kaafi nahi.
PARTS = (".segtrack", ".seg", ".progtrack", ".prog", ".arcA", ".arcB", ".arcC",
         ".sphere", ".sheen", ".fil", ".dotted", ".core", ".tick")

GEOMETRY = """(parts) => {
  const s = document.querySelector('#orb');
  const out = {svg: 0, parts: {}};
  if (!s) return out;
  const box = s.getBoundingClientRect();
  out.svg = Math.round(Math.min(box.width, box.height));
  for (const sel of parts) {
    const e = s.querySelector(sel);
    if (!e) { out.parts[sel] = -1; continue; }
    let b = { width: 0, height: 0 };
    try { b = e.getBBox(); } catch (err) { b = { width: 0, height: 0 }; }
    // width*height galat pakkaura hai: tick-marks vertical lines hain
    // (width 0). width + height batata hai ki element ne size liya ya nahi.
    out.parts[sel] = Math.round(b.width + b.height);
  }
  return out;
}"""

# State -> orb ka label. Ye EXACT strings `ui/hud_orb.js` ke STATE_TEXT se.
STATE_LABEL = (
    ("idle", "READY"),
    ("listening", "LISTENING"),
    ("thinking", "THINKING"),
    ("speaking", "SPEAKING"),
)


def check(name, got, want=True):
    if got == want:
        print(f"  OK   {name}")
    else:
        FAILED.append(name)
        print(f"  FAIL {name} -> got {got!r}, want {want!r}")


def shots_dir() -> Path:
    """Screenshot repo ke BAHAR — `%TEMP%\\opencode\\hudshots`."""
    base = Path(tempfile.gettempdir()) / "opencode" / "hudshots"
    base.mkdir(parents=True, exist_ok=True)
    return base


def run_theme(page, url):
    want = config.hud_theme()
    print(f"DEFAULT THEME ({want})")
    page.goto(url, wait_until="load")
    page.wait_for_timeout(700)
    check("default: data-theme", page.evaluate(
        "document.documentElement.getAttribute('data-theme')"), want)

    print("THEME WHITELIST")
    for bad in BAD_QUERIES:
        page.goto(url + "?" + bad, wait_until="domcontentloaded")
        got = page.evaluate("document.documentElement.getAttribute('data-theme')")
        check(f"adhoori value reject ({bad[:18]})", got, want)
    # Bade akshar me `GOLD` — asli server lowercase karta hai (case-insensitive).
    page.goto(url + "?theme=GOLD", wait_until="domcontentloaded")
    check("GOLD (bade akshar) chalta hai", page.evaluate(
        "document.documentElement.getAttribute('data-theme')"), want)


def run_orb(page, url, out):
    print("ORB (headless, nakli data)")
    for w, h in ((1366, 768), (1200, 720)):
        page.set_viewport_size({"width": w, "height": h})
        page.goto(url, wait_until="load")
        page.wait_for_function("() => !!window.JARVIS_ORB", timeout=15000)
        page.wait_for_timeout(250)
        tag = f"{w}x{h}"

        geo = page.evaluate(GEOMETRY, list(PARTS))
        check(f"{tag} orb size", geo["svg"] >= 150, True)
        for sel in PARTS:
            # `.get()` — missing key par KeyError se test crash na ho.
            check(f"{tag} {sel} geometry", geo["parts"].get(sel, 0) > 0, True)

        for state, label in STATE_LABEL:
            page.evaluate("(s) => window.JARVIS_ORB.setState(s)", state)
            page.wait_for_timeout(80)
            check(f"{tag} orb state {state}", page.evaluate(
                "document.getElementById('orbState').textContent"), label)

        page.screenshot(path=str(out / f"gold_{w}x{h}.png"))


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP: Playwright install nahi hai (browser-free check "
              "hud_check_ui.py me hai).")
        return
    out = shots_dir()
    hudserve.DEFAULT_THEME = config.hud_theme()
    with FakeHud() as hud, sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)     # koi window nahi
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        errors = []
        page.on("pageerror",
                lambda e: errors.append(getattr(e, "stack", None) or str(e)))
        try:
            run_theme(page, hud.url)
            run_orb(page, hud.url, out)
            check("koi JS error nahi", errors, [])
            check("screenshot repo ke bahar",
                  str(out).startswith(tempfile.gettempdir()), True)
        finally:
            page.close()
            browser.close()
    print(f"  (screenshot: {out})")


if __name__ == "__main__":
    print(f"Asli config ka default theme: {config.hud_theme()!r}")
    main()
    print()
    if FAILED:
        print(f"{len(FAILED)} fail: {FAILED}")
        sys.exit(1)
    print("Gold HUD test pass (Playwright headless, nakli data).")
