#!/usr/bin/env python3
"""Draws the backgrounds of the two layouts. Original drawings, no game asset.

- me2 (mission-computer, img/bg.png): a dark amber room in the spirit of the
  Mass Effect 2 pause menu: a warm glow in the middle, concentric
  holographic rings, faint scan lines and a vignette.
- me1 (normandy-sr1, img/bg-me1.png): a deep blue console in the spirit of
  the Mass Effect 1 menus: a cold glow, a fine grid, chamfered panel
  outlines, faint scan lines and a vignette.
- me3 (war-room, img/bg-me3.png): a dark steel room in the spirit of the
  Mass Effect 3 mission computer: a cold grey-blue glow, a hub of thin
  rings, light streaks across, faint scan lines and a vignette.

Usage: python3 me-hud/tools/make_art.py [me1|me2|me3]   (all when omitted; needs Pillow)
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUTS = {"me2": os.path.join(HERE, "..", "img", "bg.png"), "me1": os.path.join(HERE, "..", "img", "bg-me1.png"),
        "me3": os.path.join(HERE, "..", "img", "bg-me3.png")}
W, H = 1920, 1080
CX, CY = W * 0.56, H * 0.46  # the rings sit right of centre: the sidebar covers the left


def radial_glow(base=(8, 5, 3), gain=(46, 20, 8)):
    """Glow in the middle (warm by default), near black at the edges."""
    small = Image.new("RGB", (W // 8, H // 8))
    px = small.load()
    sw, sh = small.size
    for y in range(sh):
        for x in range(sw):
            dx = (x * 8 - CX) / (W * 0.55)
            dy = (y * 8 - CY) / (H * 0.65)
            d = min(1.0, math.hypot(dx, dy))
            k = (1 - d) ** 1.8
            px[x, y] = tuple(int(b + g * k) for b, g in zip(base, gain))
    return small.resize((W, H), Image.BICUBIC)


def rings():
    """Concentric rings and arcs, drawn on a transparent layer then blurred for the glow."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    orange = (255, 138, 43)
    for r, width, alpha in ((140, 3, 70), (205, 2, 45), (290, 10, 22), (300, 1, 60),
                            (420, 2, 38), (520, 26, 10), (560, 1, 40), (720, 2, 26), (900, 1, 18)):
        box = (CX - r, CY - r, CX + r, CY + r)
        d.ellipse(box, outline=orange + (alpha,), width=width)
    # Broken arcs, like the menu's rotating dials.
    for r, start, end, width, alpha in ((250, 200, 330, 6, 60), (250, 20, 150, 6, 60),
                                        (360, 120, 175, 14, 40), (360, 300, 355, 14, 40),
                                        (470, 230, 310, 4, 55), (640, 160, 200, 8, 30),
                                        (640, 340, 20, 8, 30)):
        box = (CX - r, CY - r, CX + r, CY + r)
        d.arc(box, start, end, fill=orange + (alpha,), width=width)
    # Tick marks around one ring.
    for i in range(72):
        a = math.radians(i * 5)
        r1, r2 = 590, 590 + (18 if i % 6 == 0 else 8)
        d.line((CX + r1 * math.cos(a), CY + r1 * math.sin(a), CX + r2 * math.cos(a), CY + r2 * math.sin(a)),
               fill=orange + (50 if i % 6 == 0 else 26,), width=2)
    glow = layer.filter(ImageFilter.GaussianBlur(6))
    return Image.alpha_composite(glow, layer)


def scanlines():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for y in range(0, H, 3):
        d.line((0, y, W, y), fill=(0, 0, 0, 34))
    return layer


def vignette():
    small = Image.new("L", (W // 8, H // 8))
    px = small.load()
    sw, sh = small.size
    for y in range(sh):
        for x in range(sw):
            dx = (x / sw - 0.5) * 2
            dy = (y / sh - 0.5) * 2
            px[x, y] = int(200 * min(1.0, max(0.0, (math.hypot(dx, dy) - 0.75) / 0.7)))
    mask = small.resize((W, H), Image.BICUBIC)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    layer.putalpha(mask)
    return layer


def chamfer(x0, y0, x1, y1, c):
    """Outline of a panel with its corners cut, as in the Mass Effect 1 menus."""
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c), (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def console():
    """The ME1 console: a fine grid, chamfered panel outlines and light bars, blurred for the glow."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    blue = (90, 170, 255)
    for x in range(0, W, 48):
        d.line((x, 0, x, H), fill=blue + (9,), width=1)
    for y in range(0, H, 48):
        d.line((0, y, W, y), fill=blue + (9,), width=1)
    for box, c, width, alpha in (((330, 110, 1010, 560), 34, 2, 46), ((1060, 110, 1740, 560), 34, 2, 46),
                                 ((340, 120, 1000, 550), 28, 1, 26), ((1070, 120, 1730, 550), 28, 1, 26),
                                 ((560, 610, 1500, 960), 40, 3, 34), ((150, 70, 1820, 1010), 60, 1, 22)):
        d.polygon(chamfer(*box, c), outline=blue + (alpha,), width=width)
    for y, x0, x1, alpha in ((170, 380, 960, 40), (176, 380, 700, 24), (170, 1110, 1690, 40), (176, 1110, 1430, 24),
                             (660, 610, 1450, 34)):
        d.line((x0, y, x1, y), fill=blue + (alpha,), width=3)
    glow = layer.filter(ImageFilter.GaussianBlur(5))
    return Image.alpha_composite(glow, layer)


def hub():
    """The ME3 hub: a few thin rings in the middle and light streaks across, blurred for the glow."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steel = (150, 185, 220)
    cx, cy = W * 0.5, H * 0.44
    for r, width, alpha in ((60, 3, 70), (74, 1, 50), (190, 1, 30), (330, 2, 18), (520, 1, 14)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=steel + (alpha,), width=width)
    for start, end in ((30, 60), (120, 150), (210, 240), (300, 330)):
        d.arc((cx - 120, cy - 120, cx + 120, cy + 120), start, end, fill=steel + (45,), width=4)
    for y, alpha in ((H * 0.18, 16), (H * 0.62, 26), (H * 0.64, 12), (H * 0.86, 18)):
        d.line((0, y, W, y), fill=steel + (alpha,), width=2)
    glow = layer.filter(ImageFilter.GaussianBlur(6))
    return Image.alpha_composite(glow, layer)


def draw(style):
    if style == "me3":
        img = radial_glow(base=(5, 7, 10), gain=(22, 32, 46)).convert("RGBA")
        layers = (hub(), scanlines(), vignette())
    elif style == "me1":
        img = radial_glow(base=(3, 6, 14), gain=(10, 34, 70)).convert("RGBA")
        layers = (console(), scanlines(), vignette())
    else:
        img = radial_glow().convert("RGBA")
        layers = (rings(), scanlines(), vignette())
    for layer in layers:
        img = Image.alpha_composite(img, layer)
    out = OUTS[style]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.convert("RGB").save(out, optimize=True)
    print(os.path.normpath(out))


def main():
    styles = sys.argv[1:] or list(OUTS)
    for style in styles:
        if style not in OUTS:
            sys.exit(f"unknown style: {style} (me1, me2 or me3)")
        draw(style)


if __name__ == "__main__":
    main()
