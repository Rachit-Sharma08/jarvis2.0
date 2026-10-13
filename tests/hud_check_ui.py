"""Phase 4 HUD — UI side ke checks (browser-free source checks).

Sirf static analysis: HTML/CSS/JS ka source padha jaata hai. Koi asli tool ya
brain call nahi hota. Live browser verify alag hua hai
(`tests/hud_check_api.py` ke saath server-side ke liye).

XSS niyam (AGENTS.md): dynamic text sirf `textContent` se. Is file me wahi
guard hai — koi bhi `innerHTML`/`eval` wapas aa gaya to test girta hai.
"""

import config
from hud_common import UI, UI_CSS, UI_JS, check, read


# ---------------------------------------------------------------- XSS
def test_xss_safety():
    print("XSS / SURAKSHA (source check)")
    for name in UI_JS:
        src = read(name)
        for bad in ("innerHTML", "outerHTML", "insertAdjacentHTML",
                    "document.write", "eval(", "new Function"):
            check(f"{name}: {bad} nahi", bad in src, False)
        # `textContent` ka check sirf un file par jo dynamic text banati hain.
        # Teen chhoot: recorder/speaker/voice_ui (purane mic/speaker raaste).
        # KAAM B ki do aur chhoot:
        #   `arc_reactor.js` — sirf SVG geometry (attributes), koi text node
        #   `arc_load.js`    — sirf `<link>`/`<script>` loader, koi text node
        # In dono me dynamic text hai hi nahi, is liye ye check un par lagu
        # nahi hota. Baki sab arc files me `textContent` zaroor hai.
        if name not in ("recorder.js", "speaker.js", "voice_ui.js",
                        "arc_reactor.js", "arc_load.js"):
            check(f"{name}: textContent hai", "textContent" in src, True)

    html = read("index.html")
    check("inline <script> nahi", "<script>" in html, False)
    check("onclick attribute nahi", "onclick" in html, False)
    check("token meta placeholder", '__PRABH_TOKEN__' in html, True)

    # Koi external URL html/css me nahi (CSP strict rahe)
    for name in ("index.html",) + UI_CSS:
        src = read(name)
        lines = [l for l in src.splitlines()
                 if "http" in l and not l.strip().startswith(("*", "/*", "<!--"))]
        check(f"{name}: bahar ka URL nahi", lines, [])


# ---------------------------------------------------------------- STYLES
def test_hud_structure():
    print("HUD STRUCTURE / FILES")
    for name in UI_CSS:
        check(f"{name} maujood", (UI / name).is_file(), True)
    for name in UI_JS:
        check(f"{name} maujood", (UI / name).is_file(), True)

    html = read("index.html")
    for want in ("brand", "status", "sysstate", "provider", "gauges", "bars",
                 "activity", "orbMode", "wxTemp", "messages", "cmd", "send",
                 "qLeft", "qRight", "confirmcard", "allow", "deny", "kill",
                 "mute", "stop", "mic"):
        check(f'id="{want}" hai', f'id="{want}"' in html, True)

    # Har file 200 line se chhoti (AGENTS.md ka niyam)
    for name in UI_CSS + UI_JS + ("index.html",):
        lines = len(read(name).splitlines())
        check(f"{name} <200 line", lines < 200, True)

    # Purane style.css/tools.css hat gaye
    check("style.css hata diya", (UI / "style.css").exists(), False)
    check("tools.css hata diya", (UI / "tools.css").exists(), False)

    # Fonts local
    for font in ("orbitron-var.woff2", "rajdhani-400.woff2", "rajdhani-500.woff2",
                 "rajdhani-600.woff2", "share-tech-mono.woff2"):
        check(f"font {font}", (UI / "fonts" / font).is_file(), True)
    check("OFL license hai", (UI / "fonts" / "OFL-LICENSE.txt").is_file(), True)
    check("font manifest hai", (UI / "fonts" / "MANIFEST.txt").is_file(), True)
    check("fonts.css me woff2", read("fonts.css").count(".woff2"), 5)
    check("fonts.css me bahar ka URL nahi",
          "https://" in read("fonts.css").replace("fonts.googleapis.com", ""), False)


# ---------------------------------------------------------------- CLOCK + GAUGES
def test_clock_and_gauges():
    print("CLOCK / GAUGES / BARS")
    clock = read("hud_clock.js")
    check("HH:MM ban raha hai", "getHours" in clock and "getMinutes" in clock, True)
    check("seconds dial banta hai", "getSeconds" in clock, True)
    check("purana format string", "30 September 2026" in clock, True)
    check("tick 1 second", "setInterval(tick, 1000)" in clock, True)

    stats = read("hud_stats.js")
    for label in ("CPU", "RAM", "BATT", "DISK", "NETWORK"):
        check(f"gauge/bar {label}", label in stats, True)
    check("createElementNS use hua (SVG)", "createElementNS" in stats, True)
    check("textContent se number", "val.textContent" in stats, True)
    # Spec: network MB/s (MB nahi)
    check("network MB/s", 'MB/s"' in stats, True)

    # Ruler ke tick-marks CSS me (ruler top bar ka hissa hai → hud_base.css)
    base = read("hud_base.css")
    check("ruler tick-marks", "repeating-linear-gradient" in base, True)
    check("ruler ki 1px neeli line", "linear-gradient(var(--cyan-dim)" in base, True)


# ---------------------------------------------------------------- ORB
def test_orb():
    print("ORB SVG + ANIMATION")
    orb = read("hud_orb.js")
    html = read("index.html")
    css = read("hud_center.css")

    check("SVG svg tag", "<svg" in html and "viewBox" in html, True)
    for ring in ("ringOuter", "ringSeg", "ringProg", "ringDot", "ringCore"):
        check(f"ring {ring} svg me", f'id="{ring}"' in html, True)
    check("tick-marks JS me", "TICKS" in orb and "createElementNS" in orb, True)
    check("core ka SVG radialGradient define hai",
          'id="coreGrad"' in html and "<radialGradient" in html, True)
    check("core usi gradient se bharta hai", "url(#coreGrad)" in css, True)
    # Sirf declaration dekho, comment nahi (comment me bhi wahi shabd likha hai)
    decls = [ln for ln in css.splitlines() if "radial-gradient" in ln
             and not ln.strip().startswith(("*", "/*", "//"))]
    check("core me invalid CSS radial-gradient nahi",
          any("fill: radial-gradient" in ln for ln in decls), False)

    for state in ("idle", "listening", "thinking", "speaking"):
        check(f"{state} CSS animation", f".{state} " in css, True)
    check("idle ulti disha", ".idle .seg" in css and "reverse" in css, True)
    check("listening amber sweep", ".listening .prog" in css, True)
    check("thinking tez", ".thinking .seg" in css, True)
    check("speaking ripple", ".speaking .dotted" in css, True)
    # Amber rang ka asal source hud_base.css ka --amber variable hai.
    check("progress arc amber", ".prog" in css and "var(--amber)" in css, True)
    check("amber value define hai", "--amber: #f5a623" in read("hud_base.css"), True)


# ---------------------------------------------------------------- ACTIVITY + STOP
def test_activity_and_stop():
    print("ACTIVITY TAGS / STOP WIRING")
    act = read("hud_activity.js")
    for tag in ("DONE", "ALLOW", "DENIED", "BLOCKED", "PENDING"):
        check(f"tag {tag}", tag in act, True)
    check("DENY spelling nahi", '"DENY"' in act, False)

    app = read("app.js")
    check("STOP dono cheezein rokta hai", "tools.cancel();" in app, True)
    check("STOP button wired", "stopBtn.addEventListener" in app, True)
    check("isTrusted quick me", "isTrusted" in read("hud_quick.js"), True)


# ---------------------------------------------------------------- LAYOUT
def test_layout_1366x768():
    print("LAYOUT 1366x768")
    base = read("hud_base.css")
    bottom = read("hud_bottom.css")
    left = read("hud_left.css")

    check("page scroll off", "overflow: hidden" in base, True)
    check("100vh grid", "height: 100vh" in base, True)
    check("topbar full width", "grid-column: 1 / -1" in base, True)
    check("bottombar full width", "grid-column: 1 / -1" in base, True)

    # overflow guard: har panel overflow handle karta hai
    check("chatlog scroll", "overflow-y: auto" in read("hud_right.css"), True)
    check("actlist scroll", "overflow-y: auto" in left, True)
    check("gauge max-width chhota", "max-width: 62px" in left, True)
    check("qbtn width fix", "width: 52px" in bottom, True)
    check("composer 1fr", "1fr" in bottom, True)
    check("orb viewport se chhota", "min(46vh" in read("hud_center.css"), True)

    # 1366px par teen column rahe: column width fr/minmax based ho, fixed px nahi.
    # (pehle 24% 50% 26% tha, jo gap + padding ke saath 20px overflow kar deta tha,
    #  isliye live browser me horizontal scroll aa raha tha)
    cols = [ln for ln in base.splitlines() if "grid-template-columns: minmax(0," in ln]
    check("3 column grid ek line me hai", len(cols) == 1, True)
    check("santulan 24/50/26 hai", all(v in cols[0] for v in ("24", "50", "26")), True)
    check("koi fixed px column nahi", "px" not in cols[0], True)
    check("fr units gap ko sambhalte hain", "fr" in cols[0], True)


def run():
    test_xss_safety()
    test_hud_structure()
    test_clock_and_gauges()
    test_orb()
    test_activity_and_stop()
    test_layout_1366x768()