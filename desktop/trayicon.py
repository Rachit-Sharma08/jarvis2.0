"""Tray icon ke pictures — Pillow se, koi file nahi.

Ek hi kaam: state (idle / listening / muted / error / off) se ek chhoti si
image banana. Mic ka nishaan **har state me** rehta hai (user ka niyam) —
sirf rang badalta hai, aur mic band ho to us par tir khaata hai.

Pillow pehle se venv me hai (Phase 4 me aaya tha), is liye is file me koi
naya package nahi lag raha.
"""

from PIL import Image, ImageDraw

import config

SIZE = 64
_RING = 4          # ring ki motai
_MIC_W = 11        # mic ki jooti (width)
_MIC_H = 22        # mic ki jooti (height)


def _hex_to_rgba(colour: str, alpha: int = 255) -> tuple:
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def _mic(draw: ImageDraw.ImageDraw, colour: tuple) -> None:
    """Mic ka nishaan: jooti + arc + base line. Centre (SIZE/2, SIZE/2 - 2)."""
    cx = SIZE // 2
    top = SIZE // 2 - 15
    left = cx - _MIC_W // 2
    # jooti
    draw.rounded_rectangle(
        [left, top, left + _MIC_W, top + _MIC_H], radius=_MIC_W // 2, fill=colour
    )
    # arc — mic ko pakadne wala
    draw.arc(
        [cx - 13, top + 6, cx + 13, top + 24], start=0, end=180,
        fill=colour, width=_RING,
    )
    # base line
    draw.line([cx, top + 24, cx, top + 30], fill=colour, width=_RING)
    draw.line([cx - 8, top + 30, cx + 8, top + 30], fill=colour, width=_RING)


def _slash(draw: ImageDraw.ImageDraw, colour: tuple) -> None:
    """Mic band hai — us par tir. Yeh nishaan 'sun nahi raha' batata hai."""
    draw.line([12, 12, SIZE - 12, SIZE - 12], fill=colour, width=_RING + 2)


def image(state: str) -> Image.Image:
    """State se tray icon. Rang `config.TRAY_COLORS` se, mic hamesha."""
    colour = _hex_to_rgba(config.tray_color(state))
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # Gehre peeche ka disk — halka rang bhi saaf dikhe.
    draw.ellipse([2, 2, SIZE - 3, SIZE - 3], fill=(8, 14, 24, 235))
    draw.ellipse(
        [2, 2, SIZE - 3, SIZE - 3], outline=colour, width=_RING
    )
    _mic(draw, colour)
    if state in (config.TRAY_MUTED, config.TRAY_OFF):
        _slash(draw, _hex_to_rgba("#e0483c") if state == config.TRAY_MUTED else colour)
    return canvas
