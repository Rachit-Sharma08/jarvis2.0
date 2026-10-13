"""KAAM B — Arc ke JS probe + edge-case query (shared).

`arccheck.py` 200 cross karne par ye alag bana. Yahan sirf wahi hai jo
browser se **puchha** jaata hai (evaluate ka JS) aur woh queries jo
attribute-injection ka pakkaura hain.

`?theme=` ka whitelist test ke liye: sirf `"arc"`/`"neon"` maane jaate hain
(asli server: `server/app.py` ka `resolve_theme`). Kuch bhi aur — script tag,
spaces, 40 character ka gadbha — seedha default par girna chahiye.
"""

# JS: har element ka bbox + viewport se compare. `width*height` se pakkaura
# galat hai (tick vertical lines hain, unka area 0), is liye `width + height`.
GEOMETRY = """() => {
  const s = document.querySelector('.a-reactor');
  const parts = ['.a-tick', '.a-arc', '.a-core', '.a-ring', '.a-hex', '.a-odot'];
  const out = {svg: 0, parts: {}, total: 0};
  if (!s) return out;
  const box = s.getBoundingClientRect();
  out.svg = Math.round(Math.min(box.width, box.height));
  for (const sel of parts) {
    const e = s.querySelector(sel);
    if (!e) { out.parts[sel] = -1; continue; }
    let b = { width: 0, height: 0 };
    try { b = e.getBBox(); } catch (err) { b = { width: 0, height: 0 }; }
    // `width*height` galat pakkaura hai: tick-marks **vertical** lines hain
    // (width 0), is liye unka area 0 ho jaata hai jabki wo bilkul sahi draw
    // ho rahe hain. `width + height` batata hai ki element ne koi size liya
    // ya nahi; `total` me asli area jaata hai.
    out.parts[sel] = Math.round(b.width + b.height);
    out.total += Math.round(b.width * b.height);
  }
  return out;
}"""

# JS: clip/overflow pakkaura. `vw`/`vh` ka order saaf rakho — pehle yahan
# ulta likha tha aur har element "clipped" dikha jabki sab andar hi tha.
FITS = """(sels) => {
  const vw = window.innerWidth, vh = window.innerHeight;
  const out = { cut: [], overflow: [0, 0] };
  const hud = document.querySelector('.a-root');
  if (hud) out.overflow = [hud.scrollWidth - hud.clientWidth,
                           hud.scrollHeight - hud.clientHeight];
  for (const s of sels) {
    const e = document.querySelector(s);
    if (!e) continue;
    const b = e.getBoundingClientRect();
    if (b.width === 0 && b.height === 0) continue;
    if (b.bottom > vh + 0.5 || b.top < -0.5 || b.right > vw + 0.5 || b.left < -0.5)
      out.cut.push(s);
  }
  return out;
}"""

# Devanagari jo sach me batana hai (sirf ascii nahi) — nirmal UI / Noto se.
HINDI = "आपकी बैटरी साठ प्रतिशत है"

# Attribute-injection ke pakkaure. In sab par `data-theme` sirf `neon`/`arc`
# hona chahiye — kuch bhi aur attribute me chala gaya to XSS ka darra hai.
BAD_QUERIES = (
    "theme=<script>",
    "theme=NEON%20",
    "theme=" + "x" * 40,
    "theme=arc%22%20onload%3Dalert(1)",
)

# Bade akshar me `ARC` — asli server lowercase karta hai, is liye ye chalna
# chahiye (test ka maqsad: case-insensitivity, injection nahi).
GOOD_QUERY = "theme=ARC"

# Jo cheezein kabhi clip nahi honi chahiye.
MUST_FIT = (".a-root", ".a-top", ".a-mid", ".a-bottom", ".a-dock", "#a-cmd",
            ".a-line", ".a-chat", ".a-reactor", ".a-corenum")

# Reactor ke hisse — har ek ka geometry > 0 hona chahiye.
PARTS = (".a-tick", ".a-arc", ".a-core", ".a-ring", ".a-hex", ".a-odot")

# State -> label. Ye EXACT strings `ui/arc_live.js` ke STATES se aate hain.
STATE_LABEL = (
    ("thinking", "THINKING"),
    ("listening", "LISTENING"),
    ("muted", "MUTED"),
)