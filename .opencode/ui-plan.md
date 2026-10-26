# HUD redesign — "STARK GOLD" (single theme)

Status: **awaiting owner approval**. Nothing built yet.

## Goal

Replace **both** existing HUD looks (`neon` cyan, `arc` orange) with one new
design: the golden/amber JARVIS hologram from the Iron Man / Avengers films.
One theme only. No switcher, no second DOM.

## What the real films actually look like (checked, not remembered)

Downloaded frames: `D:\Projects\jarvis\refs\` (5 stills + Iron Man 3 HUD).
What the real HUD does, and what every "JARVIS clone" on GitHub gets wrong:

| Real film HUD | What this repo does today | Change |
|---|---|---|
| Pure black, almost no panel fill | Translucent blue panels + backdrop blur | Drop the fill and the blur. Black only. |
| 1px hairlines, mostly open space | Every panel is a closed 1px box | Open frames: hairline top rule + corner brackets, no full box |
| Concentric reticles at **different depths**, rotating opposite ways | 4 flat rings, same plane | Add 3 counter-rotating arc segments + radial spokes behind |
| Tiny mono readouts, 8–10px, wide tracking | Already close | Keep, tighten |
| Warm gold bloom, everything else near-invisible | Cyan at uniform brightness | Gold only where it matters, dim the rest |
| Chamfered / angled shapes, zero rounded corners | Circles + 20px rounded mic | Chamfer everything except the icon dock |
| One red alert channel | Green "ok" + amber "warn" + red | Gold-hot = ok, ember = alert. No green. |

Note: the 2012 frames are cyan. The **gold** JARVIS is Iron Man 3 / Age of
Ultron — which is what the owner asked for. Structure comes from the frames,
palette is gold.

## Tokens

```
--void      #060403   page, warm black
--void-2    #0D0906   panel wash (3%)
--gold      #FFB43A   primary line, glow
--gold-hot  #FFE9B0   core, key numbers
--gold-mid  #C8842A   secondary text, icons
--gold-deep #6B4713   hairlines, tracks, ticks
--bone      #F4E7CE   body text
--ember     #FF5C33   alerts only
```

Type — drop Orbitron (biggest "gamer HUD" tell), add **Michroma**
(free Eurostile-Extended-alike, the actual film title face):

- `Michroma` 400 → wordmark, clock, temperature, orb label
- `Rajdhani` 400/500/600 → body, panel tabs, buttons (kept)
- `Share Tech Mono` 400 → every number and label (kept)

## Layout

Grid stays 24 / 50 / 26 — it is already debugged for 1366×768 overlap.
Only the chrome inside changes.

```
┌──────────────────────────────────────────────────────────────┐
│ J.A.R.V.I.S. ● IDLE   ├─┬─┬─┬─┬─┬─┬─┬─┬─┤   SYSTEM  MUTE     │
├────────────┬──────────────────────────────┬──────────────────┤
│ CHRONOMETER│           ╭ reticle ╮        │ WEATHER          │
│  ◜74◝      │          │ J A R V I S │      │  ◜ ◝   28°       │
│  14:32     │           ╰  READY   ╯       │  Clear Sky       │
│ SYSTEM     │         "Good evening, sir"  │ CONVERSATION     │
│  ◔ ◔ ◔     │                              │  YOU    ...      │
│ ACTIVITY   │                              │  JARVIS ...      │
├────────────┴──────────────────────────────┴──────────────────┤
│  ⬡ ⬡ ⬡      [ MIC ][ command… ][ SEND ]       ⬡ ⬡ ⬡          │
└──────────────────────────────────────────────────────────────┘
```

- Panel tab: thin outlined tag, left edge cut 45°, sits *on* the top hairline.
- Corner marks: 2 per panel (top-left, bottom-right), asymmetric on purpose.
- Orb: 7 layers — 72 ticks · ring · segmented dashes · **3 counter-rotating
  arcs** · progress · dotted · core with hot centre dot. Two orbiting
  satellites on the outer ring.
- Bottom dock icons stay circular (matches the reticle language); MIC and
  SEND become chamfered.

## Motion

One boot sequence only: grid fades in, rings expand from centre, hairlines
draw. Then ambient only — ring rotation (26s/40s), one 9s scan band, orb
breathe. No per-card hover wiggles. `prefers-reduced-motion` kills all of it.

## Files

**Look (the work):** `ui/hud_base.css` · `hud_panel.css` · `hud_center.css` ·
`hud_left.css` · `hud_right.css` · `hud_bottom.css` · `hud_card.css` ·
`hud_orb.js` · `index.html` · `fonts.css` + new `fonts/michroma.woff2`
(+ MANIFEST) · `config_hud.py`

**Delete (old themes):** `ui/arc.css`, `arc_layout.css`, `arc_core.css`,
`arc_bottom.css`, `arc_config.js`, `arc_reactor.js`, `arc_dom.js`,
`arc_live.js`, `arc_shell.js`, `arc_wire.js`, `arc_boot.js`, `arc_load.js`

**Config:** `HUD_THEMES = ("gold",)`, `HUD_THEME_DEFAULT = "gold"`,
`?theme=` whitelist kept (kills the XSS surface, one valid value).
Delete the whole `ARC_*` block.

**Tests (mechanical, same commit):** `tests/arccheck.py` (single `.hud` root,
loop over `config.HUD_THEMES`, drop `arc_layout` call) · `arc_probe.py`
(drop `.a-*`, `GOOD_QUERY = "theme=GOLD"`) · `arclib.py` (drop arc helpers) ·
`arc_layout.py` (repurpose geometry/clip/Hindi checks onto `.hud`, do not
lose them — they caught the 1366×768 overlap) · `hud_common.py` +
`hud_check_ui.py` file lists · `hudcheck_bar.py` (`theme="gold"`) ·
`test_hud_arc.py` docstring.

**Docs:** `.env.example` → `JARVIS_HUD_THEME=gold`.

## Order

1. Font + palette + base (see it render).
2. Panels + columns.
3. Orb (hero).
4. **Screenshot at 1200×720 → owner looks.**
5. Delete arc, collapse config, fix tests.
6. Full suite (81 suites), real OpenRouter call, commit + push.

## Done means

- 81/81 suites pass, no new failures.
- `127.0.0.1:8000` renders the gold HUD at 1200×720 with no JS error.
- No cyan and no orange left anywhere in `ui/`.
- `git grep -i "cyan\|#2ea8ff\|#ff8a2e"` → empty.
- Real `OPENROUTER_API_KEY` answers one chat turn.
