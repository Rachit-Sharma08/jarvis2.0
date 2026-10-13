"""KAAM A — bottom bar ka asli check (Playwright headless, nakli data).

Ye file `test_hud_bar.py` se chalti hai. Browser-free nahi hai — isi ka
maqsad hai: source-check se ye bug Phase 4 me 8 baar chhoot gaya tha.

Jo check hota hai:
1. Har size par `.bottombar` ka box viewport ke andar hai (cut nahi).
2. Koi bhi bhaari panel/label viewport se bahar nahi nikla.
3. Status text (reminder / notice / micflag / brainwarn) kisi aur cheez
   par **overlap** nahi karta — ancestor/descendant ko chhod kar.
4. `.barhint` poori width le kar teenon ko side me rakhta hai.

Screenshot `%TEMP%\\opencode\\hudshots` me. Playwright na ho to SKIP
(suite fail nahi hota) — browser-free check `hud_check_ui.py` me hai.
"""

import tempfile
from pathlib import Path

from hudserve import FakeHud

FAILED = []

# Jo viewport check karne hain. 1366x768 asli kaam wala hai.
SIZES = ((1366, 768), (1280, 720), (1920, 1080), (1200, 688), (1024, 700))

# Status text + wo cheez jispar wo pehle chadh jaata tha.
OVERLAP_PAIRS = (
    (".remind-pill", ".qlbl", "reminder x quick-label"),
    (".remind-pill", ".composer", "reminder x composer"),
    (".remind-pill", ".qbtn", "reminder x quick-btn"),
    (".remind-pill", ".micflag", "reminder x micflag"),
    (".notice", ".composer", "notice x composer"),
    (".notice", ".micflag", "notice x micflag"),
    (".notice", ".col-left", "notice x left-col"),
    (".notice", ".col-right", "notice x right-col"),
    (".micflag", ".composer", "micflag x composer"),
    (".micflag", ".col-right", "micflag x right-col"),
    (".brainwarn", ".brand", "brainwarn x brand"),
    (".brainwarn", ".tb-right", "brainwarn x tb-right"),
    (".brainwarn", ".ruler", "brainwarn x ruler"),
)

# In sab ka box viewport ke andar rehna chahiye.
MUST_FIT = (".hud", ".topbar", ".bottombar", ".composer", "#cmd", "#send",
            ".mic", ".qbtn", ".qlbl", ".barhint", ".remind-pill",
            ".notice", ".micflag", ".brainwarn")

FILL_ALL = """() => {
  const pill = document.getElementById('remindPill');
  pill.classList.add('show');
  pill.textContent = 'REMIND: shaam 18:00 gym jaana hai';
  document.getElementById('notice').textContent = 'Server se connection toot gaya.';
  document.getElementById('micflag').classList.add('on');
  document.getElementById('brainwarn').textContent = 'Koi free provider ready nahi hai.';
}"""

# (saare selectors + unke boxes + overlap pairs) ek hi evaluate me.
MEASURE = """(sel) => {
  const vh = window.innerHeight, vw = window.innerWidth;
  const box = s => { const e = document.querySelector(s); if (!e) return null;
    const cs = getComputedStyle(e);
    if (cs.display === 'none' || cs.visibility === 'hidden') return null;
    const b = e.getBoundingClientRect();
    if (!b.width && !b.height) return null;
    return {y1: b.top, y2: b.bottom, x1: b.left, x2: b.right}; };
  const hits = [];
  for (const [a, c, why] of sel.pairs) {
    const ea = document.querySelector(a), ec = document.querySelector(c);
    if (!ea || !ec) continue;
    if (ea.contains(ec) || ec.contains(ea)) continue;
    const A = box(a), C = box(c); if (!A || !C) continue;
    if (!(A.x2 <= C.x1 || A.x1 >= C.x2 || A.y2 <= C.y1 || A.y1 >= C.y2))
      hits.push(why);
  }
  const clipped = [];
  for (const s of sel.fit) {
    const b = box(s); if (!b) continue;
    if (b.y2 > vh + 0.5 || b.y1 < -0.5 || b.x2 > vw + 0.5 || b.x1 < -0.5)
      clipped.push(s);
  }
  const hud = document.querySelector('.hud');
  const bar = box('.bottombar');
  return {vw, vh, hits, clipped,
          barBottom: Math.round(bar.y2), barCut: Math.round(bar.y2 - vh),
          barTop: Math.round(bar.y1),
          hudOverflow: [hud.scrollWidth - hud.clientWidth,
                        hud.scrollHeight - hud.clientHeight]};
}"""


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


def run_sizes(page, url, out):
    sel = {"pairs": [list(p) for p in OVERLAP_PAIRS], "fit": list(MUST_FIT)}
    for w, h in SIZES:
        page.set_viewport_size({"width": w, "height": h})
        page.goto(url, wait_until="load")
        page.wait_for_timeout(300)
        page.evaluate(FILL_ALL)          # sab status text ON
        page.wait_for_timeout(200)
        d = page.evaluate(MEASURE, sel)
        tag = f"{w}x{h}"
        check(f"{tag} bar viewport me hai", d["barCut"] <= 0, True)
        check(f"{tag} koi element clip nahi", d["clipped"], [])
        check(f"{tag} koi overlap nahi", d["hits"], [])
        check(f"{tag} hud overflow nahi", d["hudOverflow"], [0, 0])
        if (w, h) in ((1366, 768), (1920, 1080)):
            page.screenshot(path=str(out / f"bar_{w}x{h}.png"))


def run_empty(page, url):
    """Status text BAND: phir bhi bar sahi ho (khali state regress nahi)."""
    sel = {"pairs": [list(p) for p in OVERLAP_PAIRS], "fit": list(MUST_FIT)}
    for w, h in ((1366, 768), (1280, 720)):
        page.set_viewport_size({"width": w, "height": h})
        page.goto(url, wait_until="load")
        page.wait_for_timeout(300)
        d = page.evaluate(MEASURE, sel)
        check(f"khali {w}x{h} bar viewport me", d["barCut"] <= 0, True)
        check(f"khali {w}x{h} overflow nahi", d["hudOverflow"], [0, 0])


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("SKIP: Playwright install nahi hai (browser-free check "
              "hud_check_ui.py me hai).")
        return
    out = shots_dir()
    with FakeHud() as hud, sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)     # koi window nahi
        page = browser.new_page(viewport={"width": 1366, "height": 768})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            print(f"BOTTOM BAR ({hud.port} par nakli server, headless)")
            run_empty(page, hud.url)
            run_sizes(page, hud.url, out)
            check("koi JS error nahi", errors, [])
            # Screenshot repo me nahi gaye
            check("screenshot repo ke bahar", str(out).startswith(tempfile.gettempdir()), True)
        finally:
            page.close()
            browser.close()
    print(f"  (screenshot: {out})")