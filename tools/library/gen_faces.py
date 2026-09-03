"""Emoji rebuilt for structural variety.

The old category was 200 boards of one yellow circle with different eyes and a
different mouth: 2833 pairs shared more than 95% of their cells, because a
mouth is thirty beads out of four hundred. Structural uniqueness passed at
100% the whole time, which is precisely why it needed a different measure.

Here the HEAD is the variable that carries most of the difference - shape,
ears, horns, halo, antenna, rays - and the expression changes eyes, mouth and
an accessory together rather than one at a time.
"""
import math

from beadlib import make_pattern, stable_id
from canvas import Grid
from gen_creatures import _emit, _frame, _outline, _pick_bg

PALE = ["cream", "ivory", "light_gray", "sky_blue", "toothpaste",
        "light_lavender", "banana", "peach", "light_pink", "silver"]

# (name, head plan, skin, accent)
HEADS = [
    ("Happy",   "round",   "yellow",     "orange"),
    ("Round",   "square",  "banana",     "cheddar"),
    ("Cat",     "cat",     "cheddar",    "orange"),
    ("Bear",    "bear",    "caramel",    "dark_brown"),
    ("Bunny",   "bunny",   "white",      "light_pink"),
    ("Heart",   "heart",   "hot_pink",   "magenta"),
    ("Star",    "star",    "banana",     "orange"),
    ("Sun",     "sun",     "yellow",     "orange"),
    ("Moon",    "moon",    "cream",      "silver"),
    ("Alien",   "alien",   "light_green", "green"),
    ("Robot",   "robot",   "silver",     "dark_gray"),
    ("Ghost",   "ghost",   "white",      "light_gray"),
    ("Devil",   "devil",   "magenta",    "dark_red"),
    ("Angel",   "angel",   "peach",      "banana"),
    ("Skull",   "skull",   "white",      "dark_gray"),
    ("Frog",    "frog",    "neon_green", "dark_green"),
    ("Pig",     "pig",     "light_pink", "hot_pink"),
    ("Monkey",  "monkey",  "brown",      "tan"),
    ("Owl",     "owl",     "caramel",    "cream"),
    ("Dog",     "dog",     "tan",        "dark_brown"),
]

# (suffix, eyes, mouth, extra)
FACES = [
    ("",          "dot",     "smile",   "none"),
    (" Grin",     "arc",     "grin",    "none"),
    (" Laughing", "closed",  "open",    "tears"),
    (" Sad",      "dot",     "frown",   "tear"),
    (" Wink",     "wink",    "smirk",   "none"),
    (" Love",     "heart",   "smile",   "blush"),
    (" Cool",     "shades",  "smirk",   "none"),
    (" Surprised","wide",    "o",       "none"),
    (" Angry",    "angry",   "zigzag",  "none"),
    (" Sleepy",   "closed",  "small",   "zzz"),
    (" Silly",    "spiral",  "tongue",  "none"),
    (" Starry",   "star",    "grin",    "sparkle"),
]


def _draw_face(g, spec, cx, cy, scale):
    plan, eyes, mouth, extra = spec["parts"]
    skin, accent = spec["cols"]
    u = scale
    R = 9.0 * u
    dark = "black"

    # ── head ────────────────────────────────────────────────────────────────
    if plan == "square":
        g.rect(cx - R * 0.92, cy - R * 0.92, cx + R * 0.92, cy + R * 0.92, skin)
    elif plan == "cat":
        for sgn in (-1, 1):
            g.poly([(cx + sgn * R * 0.35, cy - R * 0.7), (cx + sgn * R * 0.95, cy - R * 1.7),
                    (cx + sgn * R * 1.0, cy - R * 0.45)], skin)
        g.disc(cx, cy, R, skin)
    elif plan == "bear":
        for sgn in (-1, 1):
            g.disc(cx + sgn * R * 0.78, cy - R * 0.78, R * 0.38, skin)
        g.disc(cx, cy, R, skin)
    elif plan == "bunny":
        for sgn in (-1, 1):
            g.ellipse(cx + sgn * R * 0.38, cy - R * 1.5, R * 0.22, R * 0.68, skin)
            g.ellipse(cx + sgn * R * 0.38, cy - R * 1.5, R * 0.10, R * 0.44, accent)
        g.disc(cx, cy, R, skin)
    elif plan == "heart":
        g.disc(cx - R * 0.46, cy - R * 0.32, R * 0.62, skin)
        g.disc(cx + R * 0.46, cy - R * 0.32, R * 0.62, skin)
        g.poly([(cx - R * 1.02, cy - R * 0.06), (cx + R * 1.02, cy - R * 0.06),
                (cx, cy + R * 1.05)], skin)
    elif plan == "star":
        pts = []
        for i in range(10):
            rr = R * 1.15 if i % 2 == 0 else R * 0.52
            a = -math.pi / 2 + i * math.pi / 5
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        g.poly(pts, skin)
    elif plan == "sun":
        for i in range(12):
            a = i * math.pi / 6
            g.limb(cx + math.cos(a) * R * 0.9, cy + math.sin(a) * R * 0.9,
                   cx + math.cos(a) * R * 1.45, cy + math.sin(a) * R * 1.45, accent)
        g.disc(cx, cy, R, skin)
    elif plan == "moon":
        g.disc(cx, cy, R, skin)
        g.disc(cx + R * 0.85, cy - R * 0.2, R * 0.85, None)
        g.disc(cx - R * 0.18, cy, R * 0.86, skin)
    elif plan == "alien":
        g.ellipse(cx, cy - R * 0.1, R * 0.86, R * 1.08, skin)
        for sgn in (-1, 1):
            g.limb(cx + sgn * R * 0.3, cy - R * 1.0, cx + sgn * R * 0.7, cy - R * 1.7,
                   accent)
            g.disc(cx + sgn * R * 0.72, cy - R * 1.75, 1.4 * u, accent)
    elif plan == "robot":
        g.rect(cx - R * 0.9, cy - R * 0.8, cx + R * 0.9, cy + R * 0.9, skin)
        g.rect(cx - 0.7 * u, cy - R * 1.5, cx + 0.7 * u, cy - R * 0.8, accent)
        g.disc(cx, cy - R * 1.6, 1.6 * u, accent)
        for sgn in (-1, 1):
            g.rect(cx + sgn * R * 1.05, cy - R * 0.2, cx + sgn * R * 0.9, cy + R * 0.3, accent)
    elif plan == "ghost":
        g.disc(cx, cy - R * 0.25, R, skin)
        g.rect(cx - R, cy - R * 0.25, cx + R, cy + R * 0.55, skin)
        g.poly([(cx - R, cy + R * 0.55), (cx - R * 0.6, cy + R * 1.1),
                (cx - R * 0.2, cy + R * 0.55), (cx + R * 0.2, cy + R * 1.1),
                (cx + R * 0.6, cy + R * 0.55), (cx + R, cy + R * 1.1)], skin)
    elif plan == "devil":
        for sgn in (-1, 1):
            g.poly([(cx + sgn * R * 0.55, cy - R * 0.85), (cx + sgn * R * 1.05, cy - R * 1.75),
                    (cx + sgn * R * 0.95, cy - R * 0.6)], accent)
        g.disc(cx, cy, R, skin)
    elif plan == "angel":
        g.ring(cx, cy - R * 1.45, R * 0.5, accent, t=1.3 * u)
        g.disc(cx, cy, R, skin)
    elif plan == "skull":
        g.disc(cx, cy - R * 0.15, R, skin)
        g.rect(cx - R * 0.45, cy + R * 0.6, cx + R * 0.45, cy + R * 1.05, skin)
        g.rect(cx - R * 0.45, cy + R * 0.78, cx + R * 0.45, cy + R * 0.86, accent)
    elif plan == "frog":
        for sgn in (-1, 1):
            g.disc(cx + sgn * R * 0.62, cy - R * 0.88, R * 0.42, skin)
        g.ellipse(cx, cy + R * 0.1, R, R * 0.9, skin)
    elif plan == "pig":
        for sgn in (-1, 1):
            g.poly([(cx + sgn * R * 0.5, cy - R * 0.72), (cx + sgn * R * 0.98, cy - R * 1.3),
                    (cx + sgn * R * 0.95, cy - R * 0.5)], skin)
        g.disc(cx, cy, R, skin)
        g.ellipse(cx, cy + R * 0.45, R * 0.36, R * 0.26, accent)
    elif plan == "monkey":
        for sgn in (-1, 1):
            g.disc(cx + sgn * R * 1.0, cy - R * 0.05, R * 0.34, skin)
        g.disc(cx, cy, R, skin)
        g.ellipse(cx, cy + R * 0.3, R * 0.66, R * 0.5, accent)
    elif plan == "owl":
        g.disc(cx, cy, R, skin)
        for sgn in (-1, 1):
            g.poly([(cx + sgn * R * 0.35, cy - R * 0.85), (cx + sgn * R * 0.85, cy - R * 1.45),
                    (cx + sgn * R * 0.9, cy - R * 0.6)], skin)
            g.ring(cx + sgn * R * 0.42, cy - R * 0.15, R * 0.38, accent, t=1.0 * u)
    elif plan == "dog":
        for sgn in (-1, 1):
            g.ellipse(cx + sgn * R * 0.9, cy + R * 0.1, R * 0.3, R * 0.62, accent)
        g.disc(cx, cy, R, skin)
        g.ellipse(cx, cy + R * 0.42, R * 0.42, R * 0.3, accent)
    else:                                     # round
        g.disc(cx, cy, R, skin)

    # ── eyes ────────────────────────────────────────────────────────────────
    ey = cy - R * 0.28
    ex = R * 0.42
    for sgn in (-1, 1):
        px = cx + sgn * ex
        if eyes == "dot":
            # A SQUARE pupil, not a disc.
            #
            # disc(r=1.5u) is exactly the radius where rasterisation turns
            # lumpy: it lands on a different set of cells depending on where
            # the centre falls between pegs, so the two eyes of one face came
            # out different shapes and the whole face read as wonky. A rect
            # snapped to whole beads is identical on both sides every time, and
            # a square pupil is what pixel art uses at this scale anyway.
            r = max(1.0, round(1.4 * u))
            g.rect(round(px) - r + 1, round(ey) - r + 1,
                   round(px) + r - 1, round(ey) + r - 1, dark)
        elif eyes == "arc":
            g.line(px - 2.0 * u, ey + 0.6 * u, px, ey - 1.4 * u, dark, t=0.7 * u)
            g.line(px, ey - 1.4 * u, px + 2.0 * u, ey + 0.6 * u, dark, t=0.7 * u)
        elif eyes == "closed":
            g.line(px - 2.2 * u, ey, px + 2.2 * u, ey, dark, t=0.7 * u)
        elif eyes == "wink":
            if sgn < 0:
                g.disc(px, ey, 1.5 * u, dark)
            else:
                g.line(px - 2.2 * u, ey, px + 2.2 * u, ey, dark, t=0.7 * u)
        elif eyes == "heart":
            g.disc(px - 1.0 * u, ey - 0.6 * u, 1.2 * u, "red")
            g.disc(px + 1.0 * u, ey - 0.6 * u, 1.2 * u, "red")
            g.poly([(px - 2.1 * u, ey - 0.2 * u), (px + 2.1 * u, ey - 0.2 * u),
                    (px, ey + 2.2 * u)], "red")
        elif eyes == "shades":
            # A lens over each eye, joined by a thin bridge - not one bar.
            #
            # First attempt spanned 0.88R either side of centre with a 1-bead
            # nose gap, and at this scale the two lenses simply merged back
            # into the blindfold they were meant to replace. Sized off the eye
            # SPACING instead, so the gap is always visibly a gap.
            lw = max(2, round(2.4 * u))
            lh = max(1, round(1.4 * u))
            g.rect(round(px) - lw, round(ey) - lh,
                   round(px) + lw, round(ey) + lh, dark)
            if sgn > 0:
                # Drawn once, on the second eye: the bridge across the nose.
                g.rect(round(cx - ex) + lw, round(ey),
                       round(cx + ex) - lw, round(ey), dark)
        elif eyes == "wide":
            g.disc(px, ey, 2.4 * u, "white")
            g.disc(px, ey, 1.3 * u, dark)
        elif eyes == "angry":
            g.disc(px, ey + 0.4 * u, 1.4 * u, dark)
            g.line(px - sgn * 2.4 * u, ey - 2.6 * u, px + sgn * 2.0 * u, ey - 1.2 * u,
                   dark, t=0.7 * u)
        elif eyes == "spiral":
            for k in range(9):
                a = k * 0.7
                g.set(px + math.cos(a) * k * 0.28 * u, ey + math.sin(a) * k * 0.28 * u, dark)
        elif eyes == "star":
            # A four-point sparkle drawn on the grid, not eight diagonal rays.
            #
            # The old version swept four lines through the centre at 45 degree
            # steps; the diagonals rasterise unevenly against the axis-aligned
            # ones, so each eye came out a different lopsided scribble. Two
            # bars and a solid centre are symmetric by construction, and thick
            # enough to read as eyes rather than as specks.
            a = max(2, round(2.2 * u))
            t = max(1, round(0.8 * u))
            cxp, cyp = round(px), round(ey)
            g.rect(cxp - a, cyp - t + 1, cxp + a, cyp + t - 1, dark)
            g.rect(cxp - t + 1, cyp - a, cxp + t - 1, cyp + a, dark)

    # ── mouth ───────────────────────────────────────────────────────────────
    my = cy + R * 0.45
    if mouth == "smile":
        g.line(cx - 3.4 * u, my - 0.8 * u, cx, my + 1.0 * u, dark, t=0.7 * u)
        g.line(cx, my + 1.0 * u, cx + 3.4 * u, my - 0.8 * u, dark, t=0.7 * u)
    elif mouth == "grin":
        g.poly([(cx - 4.4 * u, my - 1.2 * u), (cx + 4.4 * u, my - 1.2 * u),
                (cx + 2.6 * u, my + 2.4 * u), (cx - 2.6 * u, my + 2.4 * u)], dark)
        g.rect(cx - 4.0 * u, my - 1.2 * u, cx + 4.0 * u, my - 0.4 * u, "white")
    elif mouth == "open":
        g.ellipse(cx, my + 0.6 * u, 3.4 * u, 2.8 * u, dark)
        g.ellipse(cx, my + 1.6 * u, 2.0 * u, 1.2 * u, "red")
    elif mouth == "frown":
        g.line(cx - 3.4 * u, my + 1.4 * u, cx, my - 0.6 * u, dark, t=0.7 * u)
        g.line(cx, my - 0.6 * u, cx + 3.4 * u, my + 1.4 * u, dark, t=0.7 * u)
    elif mouth == "smirk":
        g.line(cx - 1.0 * u, my, cx + 3.6 * u, my - 1.4 * u, dark, t=0.7 * u)
    elif mouth == "o":
        g.ring(cx, my + 0.4 * u, 2.4 * u, dark, t=1.0 * u)
    elif mouth == "zigzag":
        for k in range(-3, 3):
            g.line(cx + k * 1.6 * u, my + (0 if k % 2 else 2) * u,
                   cx + (k + 1) * 1.6 * u, my + (2 if k % 2 else 0) * u, dark, t=0.6 * u)
    elif mouth == "small":
        g.ellipse(cx, my, 1.6 * u, 1.0 * u, dark)
    elif mouth == "tongue":
        g.line(cx - 3.0 * u, my - 0.6 * u, cx, my + 1.0 * u, dark, t=0.7 * u)
        g.line(cx, my + 1.0 * u, cx + 3.0 * u, my - 0.6 * u, dark, t=0.7 * u)
        g.ellipse(cx + 1.0 * u, my + 2.2 * u, 1.8 * u, 2.0 * u, "hot_pink")

    # ── extra ───────────────────────────────────────────────────────────────
    if extra == "blush":
        for sgn in (-1, 1):
            g.ellipse(cx + sgn * R * 0.72, cy + R * 0.28, 2.0 * u, 1.2 * u, "light_pink")
    elif extra == "tear":
        g.poly([(cx - R * 0.42, cy - R * 0.05), (cx - R * 0.72, cy + R * 0.55),
                (cx - R * 0.26, cy + R * 0.55)], "sky_blue")
    elif extra == "tears":
        for sgn in (-1, 1):
            g.poly([(cx + sgn * R * 0.42, cy - R * 0.05),
                    (cx + sgn * R * 0.62, cy + R * 0.6),
                    (cx + sgn * R * 0.24, cy + R * 0.6)], "sky_blue")
    elif extra == "zzz":
        for k, sz in enumerate((1.6, 2.2, 2.8)):
            bx = cx + R * (0.8 + k * 0.42)
            by = cy - R * (0.7 + k * 0.42)
            g.rect(bx - sz * u, by - sz * u, bx + sz * u, by - sz * u + 0.8 * u, "sky_blue")
            g.rect(bx - sz * u, by + sz * u - 0.8 * u, bx + sz * u, by + sz * u, "sky_blue")
            g.line(bx + sz * u, by - sz * u, bx - sz * u, by + sz * u, "sky_blue", t=0.5 * u)
    elif extra == "sparkle":
        for dx, dy in ((-1.25, -1.15), (1.3, -0.95), (1.15, 1.2)):
            sx, sy = cx + R * dx, cy + R * dy
            g.line(sx - 2.2 * u, sy, sx + 2.2 * u, sy, "banana", t=0.6 * u)
            g.line(sx, sy - 2.2 * u, sx, sy + 2.2 * u, "banana", t=0.6 * u)

    _outline(g, dark, None)


def emoji():
    specs = []
    for fi, (suffix, eyes, mouth, extra) in enumerate(FACES):
        for hi, (hname, plan, skin, accent) in enumerate(HEADS):
            specs.append(dict(
                name=f"{hname}{suffix}", parts=(plan, eyes, mouth, extra),
                cols=(skin, accent),
                bg=_pick_bg(skin, PALE, hi + fi),
                tags=["emoji", hname.lower()], fill=0.94))
    return _emit("emoji", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_face(g, s, x, y, k),
                                   sp, sp["bg"], size=26, fill=sp["fill"]), 240)


GENERATORS = {"emoji": emoji}
