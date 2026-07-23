"""Procedural generators for BeadSnap's 9 parametric categories.

Each generate_<cat>() returns ~100 FusePattern dicts with genuine variety
(distinct algorithms and compositions, not just recolors). The icons category
is produced separately by gen_icons.py; threeD by gen_3d.py.

Boards use standard fuse-bead pegboard sizes (16, 24, 29 large-square, 32) so
patterns adapt to real pegboards. Rendering draws beads as touching circles.
"""
import math
import random

from beadlib import make_pattern, stable_id
from canvas import (Grid, star_points, reg_polygon, heart_points, crescent)

# ── Color groups (ids that exist in palette.json) ────────────────────────────
RAINBOW   = ["red", "orange", "yellow", "green", "blue", "dark_blue", "purple"]
RAINBOW6  = ["red", "orange", "yellow", "green", "blue", "purple"]
PASTELS   = ["light_pink", "peach", "lemon", "light_green", "toothpaste",
             "periwinkle", "light_lavender", "blush"]
BRIGHTS   = ["red", "orange", "yellow", "neon_green", "aqua", "blue", "magenta",
             "hot_pink", "purple", "turquoise"]
WARM      = ["dark_red", "red", "pumpkin", "orange", "cheddar", "yellow"]
COOL      = ["navy", "dark_blue", "blue", "sky_blue", "teal", "turquoise", "aqua"]
PINKS     = ["light_pink", "pink", "hot_pink", "magenta"]
PURPLES   = ["light_lavender", "lavender", "purple", "dark_purple", "plum"]
BLUES     = ["toothpaste", "light_blue", "sky_blue", "blue", "dark_blue", "navy"]
GREENS    = ["light_green", "neon_green", "green", "forest", "dark_green"]
GEM_HUES  = ["red", "hot_pink", "magenta", "purple", "dark_blue", "blue",
             "aqua", "teal", "green", "orange", "yellow"]
GEM_LIGHT = {"red": "blush", "hot_pink": "light_pink", "magenta": "light_pink",
             "purple": "light_lavender", "dark_blue": "sky_blue",
             "blue": "light_blue", "aqua": "toothpaste", "teal": "light_teal",
             "green": "light_green", "orange": "peach", "yellow": "lemon"}
FACES     = ["yellow", "banana", "lemon", "cheddar", "orange"]
NEUTRAL   = ["white", "cream", "light_gray", "gray", "silver", "tan"]


def _mask_cells(w, h, pts):
    """Cells covered by a filled polygon, as a set of (x, y)."""
    g = Grid(w, h)
    g.poly(pts, "M")
    return {(x, y) for x, y, _ in g.cells()}


# Colors too pale to sit on the white board without a tinted backing.
PALE = {"white", "cream", "ivory", "light_gray", "silver", "lemon",
        "toothpaste", "periwinkle", "light_lavender", "light_pink",
        "light_green", "light_blue", "light_teal", "peach", "blush", "clear"}
TINTS = {"white": "light_gray", "cream": "tan", "ivory": "tan",
         "light_gray": "gray", "silver": "gray", "lemon": "cheddar",
         "toothpaste": "sky_blue", "periwinkle": "lavender",
         "light_lavender": "lavender", "light_pink": "pink",
         "light_green": "green", "light_blue": "sky_blue",
         "light_teal": "teal", "peach": "orange", "blush": "pink",
         "clear": "light_gray"}


def _tint_if_pale(g, subject):
    """Fill a faint backing tint when the subject would vanish on white."""
    if subject in PALE:
        g.fill(TINTS.get(subject, "light_gray"))


def _finish(cat, title, grid, tags, key=None):
    return make_pattern(stable_id(cat, key or title), title, cat,
                        grid.w, grid.h, grid.cells(), tags)


# ── GEOMETRIC ────────────────────────────────────────────────────────────────

def generate_geometric():
    out = []
    combos = [("red", "white"), ("navy", "white"), ("black", "yellow"),
              ("teal", "cream"), ("hot_pink", "light_pink"), ("purple", "lemon"),
              ("forest", "light_green"), ("orange", "dark_blue"),
              ("dark_red", "cream"), ("blue", "aqua"), ("plum", "peach"),
              ("dark_green", "banana")]

    def add(title, g, tags, key):
        out.append(_finish("geometric", title, g, tags, key))

    # checkerboards
    for bs in (1, 2, 3, 4):
        for i, (a, b) in enumerate(combos):
            if len(out) >= 8 * bs:
                break
            s = 24 if bs < 3 else 30
            g = Grid(s, s)
            for y in range(s):
                for x in range(s):
                    g.set(x, y, a if ((x // bs) + (y // bs)) % 2 == 0 else b)
            add(f"{bs}x Checker {a}/{b}", g, ["checker", "geometric", a],
                f"checker-{bs}-{a}-{b}")
    # stripe families: vertical, horizontal, diagonal
    stripe_sets = [RAINBOW, RAINBOW6, PASTELS, WARM, COOL, BRIGHTS, PINKS, GREENS]
    for orient in ("vert", "horiz", "diag"):
        for si, cols in enumerate(stripe_sets):
            for wgt in (1, 2, 3):
                if len([o for o in out if o["tags"][0] == "stripe"]) >= 30:
                    break
                s = 28
                g = Grid(s, s)
                for y in range(s):
                    for x in range(s):
                        if orient == "vert":
                            idx = (x // wgt)
                        elif orient == "horiz":
                            idx = (y // wgt)
                        else:
                            idx = ((x + y) // wgt)
                        g.set(x, y, cols[idx % len(cols)])
                add(f"{orient.title()} Stripes {si+1}.{wgt}", g,
                    ["stripe", "geometric"], f"stripe-{orient}-{si}-{wgt}")
    # concentric squares (bullseye) and diamonds
    for i, cols in enumerate([RAINBOW, WARM, COOL, PASTELS, BRIGHTS, PURPLES,
                              GREENS, PINKS, BLUES, ["black", "red", "white"]]):
        s = 29
        g = Grid(s, s)
        c = s // 2
        for r in range(c + 1):
            col = cols[r % len(cols)]
            g.frame(c - r, c - r, c + r, c + r, col, 1)
        add(f"Bullseye Squares {i+1}", g, ["concentric", "geometric"],
            f"csq-{i}")
        g2 = Grid(s, s)
        for d in range(c + 1):
            col = cols[d % len(cols)]
            for x in range(s):
                y1 = abs((c - abs(x - c)))
            # diamond rings via |dx|+|dy| == d
            for y in range(s):
                for x in range(s):
                    if abs(x - c) + abs(y - c) == d:
                        g2.set(x, y, col)
        add(f"Diamond Rings {i+1}", g2, ["concentric", "geometric"], f"cdi-{i}")
    # nested frames
    for i, cols in enumerate([RAINBOW, COOL, WARM, PASTELS, BRIGHTS, PURPLES]):
        s = 28
        g = Grid(s, s)
        for k in range(s // 2):
            g.frame(k, k, s - 1 - k, s - 1 - k, cols[k % len(cols)], 1)
        add(f"Nested Frames {i+1}", g, ["frame", "geometric"], f"frame-{i}")
    # quadrants
    for i, cols in enumerate([("red", "yellow", "blue", "green"),
                              ("hot_pink", "purple", "aqua", "orange"),
                              ("navy", "cream", "teal", "banana")]):
        s = 24
        g = Grid(s, s)
        for y in range(s):
            for x in range(s):
                q = (0 if x < s / 2 else 1) + (0 if y < s / 2 else 2)
                g.set(x, y, cols[q])
        add(f"Four Quadrants {i+1}", g, ["quadrant", "geometric"], f"quad-{i}")
    # chevrons
    for i, cols in enumerate([RAINBOW6, WARM, COOL, PASTELS, BRIGHTS]):
        s = 28
        g = Grid(s, s)
        for y in range(s):
            for x in range(s):
                idx = (min(abs(x - (y % s)), s) + y) // 2
                v = (x + abs(y - (y // 4) * 4))
                g.set(x, y, cols[((x + (y // 3)) // 2 + (abs((x % 8) - 4))) % len(cols)])
        # cleaner chevron: zig pattern
        g = Grid(s, s)
        for y in range(s):
            for x in range(s):
                z = abs(((x + y) % 8) - 4)
                g.set(x, y, cols[(z + y // 4) % len(cols)])
        add(f"Chevron {i+1}", g, ["chevron", "geometric"], f"chev-{i}")
    # polka dots
    for i, (bg, dot) in enumerate([("light_pink", "white"), ("navy", "yellow"),
                                   ("teal", "cream"), ("black", "hot_pink"),
                                   ("cream", "red"), ("purple", "lemon")]):
        s = 26
        g = Grid(s, s)
        g.fill(bg)
        for cy in range(3, s, 6):
            for cx in range(3, s, 6):
                g.disc(cx, cy, 1.6, dot)
        add(f"Polka Dots {i+1}", g, ["dots", "geometric"], f"polka-{i}")
    # diagonal half-square triangles
    for i, (a, b) in enumerate(combos[:8]):
        s = 24
        g = Grid(s, s)
        for y in range(s):
            for x in range(s):
                blk = 6
                lx, ly = x % blk, y % blk
                g.set(x, y, a if lx + ly < blk else b)
        add(f"Triangle Tiles {i+1}", g, ["triangle", "geometric"], f"tri-{i}")

    return out[:100]


# ── MANDALAS ─────────────────────────────────────────────────────────────────

def generate_mandalas():
    out = []
    rnd = random.Random(7)
    palettes = [RAINBOW, WARM, COOL, PASTELS, BRIGHTS, PURPLES, GREENS, PINKS,
                BLUES, ["hot_pink", "purple", "aqua", "yellow", "white"],
                ["navy", "sky_blue", "white", "silver"],
                ["dark_purple", "magenta", "hot_pink", "lemon"]]
    i = 0
    while len(out) < 100:
        pal = palettes[i % len(palettes)]
        sym = [6, 8, 12][i % 3]
        s = [24, 29, 32][i % 3]
        g = Grid(s, s)
        cx = cy = (s - 1) / 2.0
        maxr = s / 2.0 - 1
        # center
        g.disc(cx, cy, rnd.uniform(1.2, 2.4), pal[0])
        rings = rnd.randint(3, 5)
        for ri in range(1, rings + 1):
            rr = maxr * ri / rings
            col = pal[ri % len(pal)]
            shape = (i + ri) % 4
            count = sym * (1 if ri % 2 else 2)
            if shape == 0:      # ring of dots
                for k in range(count):
                    a = 2 * math.pi * k / count
                    g.disc(cx + rr * math.cos(a), cy + rr * math.sin(a),
                           max(0.8, rr * 0.14), col)
            elif shape == 1:    # spokes
                for k in range(sym):
                    a = 2 * math.pi * k / sym
                    g.line(cx, cy, cx + rr * math.cos(a), cy + rr * math.sin(a), col)
            elif shape == 2:    # petals (small ellipses along radius)
                for k in range(count):
                    a = 2 * math.pi * k / count
                    px, py = cx + rr * 0.8 * math.cos(a), cy + rr * 0.8 * math.sin(a)
                    g.disc(px, py, max(1.0, rr * 0.18), col)
            else:               # concentric ring outline
                g.ring(cx, cy, rr, col, max(1.0, s * 0.045))
        # outer accent ring
        g.ring(cx, cy, maxr, pal[-1], 1.0)
        out.append(_finish("mandalas", f"Mandala {len(out)+1}", g,
                           ["mandala", "symmetry", f"{sym}fold"],
                           f"mandala-{i}-{sym}-{s}"))
        i += 1
    return out


# ── HEARTS ───────────────────────────────────────────────────────────────────

def _fill_heart(g, cx, cy, size, cid):
    g.poly(heart_points(cx, cy, size), cid)


def generate_hearts():
    out = []
    solids = ["red", "hot_pink", "magenta", "pink", "purple", "orange", "blue",
              "teal", "aqua", "yellow", "dark_red", "plum", "lavender",
              "light_pink", "turquoise", "neon_green"]
    # 1) single solid hearts, varied board + color
    for i, col in enumerate(solids):
        s = [20, 24, 29][i % 3]
        g = Grid(s, s)
        _tint_if_pale(g, col)
        _fill_heart(g, (s - 1) / 2, (s - 1) / 2 - 1, s * 0.92, col)
        out.append(_finish("hearts", f"{col.replace('_',' ').title()} Heart", g,
                           ["heart", "love", col], f"solid-{col}-{s}"))
    # 2) two-tone outline hearts
    for i, (a, b) in enumerate([("red", "white"), ("hot_pink", "lemon"),
                                ("purple", "light_lavender"), ("blue", "aqua"),
                                ("magenta", "light_pink"), ("teal", "cream"),
                                ("dark_red", "peach"), ("navy", "sky_blue")]):
        s = 26
        g = Grid(s, s)
        _fill_heart(g, (s - 1) / 2, (s - 1) / 2 - 1, s * 0.92, a)
        _fill_heart(g, (s - 1) / 2, (s - 1) / 2 - 1, s * 0.62, b)
        out.append(_finish("hearts", f"Outlined Heart {i+1}", g,
                           ["heart", "outline"], f"outline-{a}-{b}"))
    # 3) rainbow striped hearts
    for i, cols in enumerate([RAINBOW, PASTELS, WARM, COOL, BRIGHTS, PINKS,
                              PURPLES, ["red", "white", "hot_pink"]]):
        s = 28
        g = Grid(s, s)
        cells = _mask_cells(s, s, heart_points((s - 1) / 2, (s - 1) / 2 - 1, s * 0.92))
        ys = [y for _, y in cells] or [0]
        y0, y1 = min(ys), max(ys)
        bands = len(cols)
        for (x, y) in cells:
            bi = int((y - y0) / max(1, (y1 - y0 + 1)) * bands)
            g.set(x, y, cols[min(bi, bands - 1)])
        out.append(_finish("hearts", f"Rainbow Heart {i+1}", g,
                           ["heart", "rainbow", "stripes"], f"striped-{i}"))
    # 4) heart with border ring
    for i, (a, b) in enumerate([("white", "red"), ("lemon", "hot_pink"),
                                ("cream", "purple"), ("sky_blue", "navy")]):
        s = 27
        g = Grid(s, s)
        _fill_heart(g, (s - 1) / 2, (s - 1) / 2 - 1, s * 0.98, b)
        _fill_heart(g, (s - 1) / 2, (s - 1) / 2 - 1, s * 0.80, a)
        out.append(_finish("hearts", f"Bordered Heart {i+1}", g,
                           ["heart", "border"], f"border-{i}"))
    # 5) double / paired hearts
    for i, (a, b) in enumerate([("red", "hot_pink"), ("purple", "magenta"),
                                ("blue", "teal"), ("orange", "yellow")]):
        s = 29
        g = Grid(s, s)
        _fill_heart(g, s * 0.34, s * 0.42, s * 0.5, a)
        _fill_heart(g, s * 0.66, s * 0.56, s * 0.5, b)
        out.append(_finish("hearts", f"Two Hearts {i+1}", g,
                           ["heart", "pair"], f"pair-{i}"))
    # 6) grid of little hearts (tessellation)
    for i, (bg, cols) in enumerate([("cream", PINKS), ("navy", ["white", "yellow"]),
                                    ("light_lavender", PURPLES),
                                    ("white", RAINBOW6), ("black", BRIGHTS),
                                    ("toothpaste", ["hot_pink", "red"])]):
        s = 30
        g = Grid(s, s)
        g.fill(bg)
        k = 0
        for cy in range(5, s, 8):
            for cx in range(5, s, 8):
                _fill_heart(g, cx, cy, 7.5, cols[k % len(cols)])
                k += 1
        out.append(_finish("hearts", f"Heart Pattern {i+1}", g,
                           ["heart", "tessellation"], f"grid-{i}"))
    # 7) concentric two-tone hearts (rings)
    for i, cols in enumerate([("red", "white", "hot_pink"), ("purple", "lemon", "magenta"),
                              ("blue", "aqua", "white"), ("hot_pink", "lemon", "red"),
                              ("teal", "toothpaste", "aqua"), ("magenta", "light_pink", "purple")]):
        s = 27
        cc = (s - 1) / 2
        g = Grid(s, s)
        for ri, r in enumerate([0.98, 0.72, 0.46, 0.22]):
            _fill_heart(g, cc, cc - 1, s * r, cols[ri % len(cols)])
        out.append(_finish("hearts", f"Layered Heart {i+1}", g,
                           ["heart", "concentric"], f"layer-{i}"))
    # 8) diversified tail: cycle styles, never a plain-recolor run
    styles = ["solid", "outline", "striped", "bordered", "pair", "mini"]
    j = 0
    while len(out) < 100:
        style = styles[j % len(styles)]
        col = solids[j % len(solids)]
        col2 = solids[(j + 5) % len(solids)]
        s = [22, 24, 26][j % 3]
        cc = (s - 1) / 2
        g = Grid(s, s)
        if style == "solid":
            _tint_if_pale(g, col)
            _fill_heart(g, cc, cc - 1, s * (0.78 + 0.04 * (j % 3)), col)
        elif style == "outline":
            _fill_heart(g, cc, cc - 1, s * 0.92, col)
            _fill_heart(g, cc, cc - 1, s * 0.6, "white")
        elif style == "striped":
            cells = _mask_cells(s, s, heart_points(cc, cc - 1, s * 0.92))
            ys = [y for _, y in cells] or [0]
            y0, y1 = min(ys), max(ys)
            pal = [RAINBOW, PASTELS, WARM, COOL][j % 4]
            for (x, y) in cells:
                bi = int((y - y0) / max(1, (y1 - y0 + 1)) * len(pal))
                g.set(x, y, pal[min(bi, len(pal) - 1)])
        elif style == "bordered":
            _fill_heart(g, cc, cc - 1, s * 0.98, col2)
            _fill_heart(g, cc, cc - 1, s * 0.78, col)
        elif style == "pair":
            _fill_heart(g, s * 0.34, s * 0.42, s * 0.5, col)
            _fill_heart(g, s * 0.66, s * 0.56, s * 0.5, col2)
        else:  # mini grid
            g.fill("cream")
            k = 0
            pal = [PINKS, PURPLES, RAINBOW6, COOL][j % 4]
            for hy in range(5, s, 8):
                for hx in range(5, s, 8):
                    _fill_heart(g, hx, hy, 7.5, pal[k % len(pal)]); k += 1
        out.append(_finish("hearts", f"Heart Design {len(out)+1}", g,
                           ["heart", style], f"tail-{style}-{j}-{col}"))
        j += 1
    return out[:100]


# ── STARS ────────────────────────────────────────────────────────────────────

def _draw_star(g, cx, cy, r_out, n, col, ratio=0.45):
    g.poly(star_points(cx, cy, r_out, r_out * ratio, n), col)


def generate_stars():
    out = []
    hues = ["yellow", "banana", "cheddar", "orange", "hot_pink", "aqua", "red",
            "sky_blue", "lavender", "neon_green", "magenta", "turquoise"]
    # 1) solid n-point stars, varied points/size/color (28)
    i = 0
    for n in (5, 6, 8):
        for col in hues:
            if i >= 28:
                break
            s = [22, 26, 29][i % 3]
            c = (s - 1) / 2
            g = Grid(s, s)
            _tint_if_pale(g, col)
            _draw_star(g, c, c, s * 0.46, n, col, 0.42 if n == 5 else 0.5)
            out.append(_finish("stars", f"{n}-Point Star {i+1}", g,
                               ["star", f"{n}point", col], f"star-{n}-{col}-{s}"))
            i += 1
    # 2) nested two-tone stars (12)
    for i, (a, b) in enumerate([("yellow", "orange"), ("sky_blue", "navy"),
                                ("hot_pink", "lemon"), ("red", "yellow"),
                                ("aqua", "blue"), ("lavender", "purple"),
                                ("neon_green", "forest"), ("cheddar", "dark_red"),
                                ("magenta", "light_pink"), ("orange", "red"),
                                ("turquoise", "teal"), ("banana", "pumpkin")]):
        s = 27
        c = (s - 1) / 2
        g = Grid(s, s)
        _draw_star(g, c, c, s * 0.46, 5, a, 0.44)
        _draw_star(g, c, c, s * 0.27, 5, b, 0.44)
        out.append(_finish("stars", f"Nested Star {i+1}", g, ["star", "nested"], f"nested-{i}"))
    # 3) starbursts (10)
    for i, col in enumerate(["yellow", "orange", "cheddar", "hot_pink", "aqua",
                             "red", "banana", "neon_green", "magenta", "sky_blue"]):
        s = 29
        c = (s - 1) / 2
        g = Grid(s, s)
        rays = 12 + 2 * (i % 3)
        for k in range(rays):
            a = 2 * math.pi * k / rays
            rr = s * 0.46 if k % 2 == 0 else s * 0.3
            g.line(c, c, c + rr * math.cos(a), c + rr * math.sin(a), col)
        g.disc(c, c, s * 0.11, col)
        out.append(_finish("stars", f"Starburst {i+1}", g, ["star", "burst"], f"burst-{i}"))
    # 4) four-point sparkles / twinkles (8)
    for i, col in enumerate(["white", "lemon", "sky_blue", "aqua", "yellow",
                             "hot_pink", "lavender", "turquoise"]):
        s = 24
        c = (s - 1) / 2
        g = Grid(s, s)
        _tint_if_pale(g, col)
        for k in range(4):
            a = math.pi / 2 * k
            g.poly([(c, c), (c + s * 0.1 * math.cos(a + 0.4), c + s * 0.1 * math.sin(a + 0.4)),
                    (c + s * 0.46 * math.cos(a), c + s * 0.46 * math.sin(a)),
                    (c + s * 0.1 * math.cos(a - 0.4), c + s * 0.1 * math.sin(a - 0.4))], col)
        out.append(_finish("stars", f"Sparkle {i+1}", g, ["star", "sparkle", "twinkle"], f"spark-{i}"))
    # 5) star of david (6, no pale-on-white)
    for i, col in enumerate(["blue", "sky_blue", "purple", "hot_pink", "teal", "navy"]):
        s = 26
        c = (s - 1) / 2
        g = Grid(s, s)
        g.poly_outline(reg_polygon(c, c, s * 0.44, 3, rot=-math.pi / 2), col, t=1)
        g.poly_outline(reg_polygon(c, c, s * 0.44, 3, rot=math.pi / 2), col, t=1)
        out.append(_finish("stars", f"Star of David {i+1}", g, ["star", "sixpoint"], f"sod-{i}"))
    # 6) shooting stars (6)
    for i, (sc, tc) in enumerate([("yellow", "sky_blue"), ("banana", "lavender"),
                                  ("lemon", "aqua"), ("orange", "peach"),
                                  ("hot_pink", "light_pink"), ("aqua", "toothpaste")]):
        s = 26
        g = Grid(s, s)
        g.poly(star_points(s * 0.66, s * 0.32, s * 0.22, s * 0.1, 5), sc)
        for t in range(3):
            g.line(s * 0.52 - t, s * 0.46 + t, s * 0.1 - t, s * 0.72 + t, tc)
        out.append(_finish("stars", f"Shooting Star {i+1}", g, ["star", "shooting"], f"shoot-{i}"))
    # 7) star clusters: a big star with small ones on a tinted board (10)
    for i in range(10):
        s = 29
        c = (s - 1) / 2
        g = Grid(s, s)
        g.fill(["periwinkle", "light_lavender", "sky_blue", "light_pink"][i % 4])
        big = hues[i % len(hues)]
        _draw_star(g, c, c, s * 0.3, 5, big, 0.44)
        rnd = random.Random(200 + i)
        for _ in range(5):
            _draw_star(g, rnd.uniform(3, s - 4), rnd.uniform(3, s - 4),
                       rnd.uniform(2, 3), 5, rnd.choice(["yellow", "white", "hot_pink"]), 0.44)
        out.append(_finish("stars", f"Star Cluster {i+1}", g, ["star", "cluster"], f"clus-{i}"))
    # 8) star fields on dark boards (fill to 100, capped)
    j = 0
    while len(out) < 100:
        s = 29
        g = Grid(s, s)
        g.fill(["navy", "dark_blue", "dark_purple", "black"][j % 4])
        rnd = random.Random(300 + j)
        for _ in range(rnd.randint(9, 13)):
            _draw_star(g, rnd.randint(2, s - 3), rnd.randint(2, s - 3),
                       rnd.uniform(1.8, 3.2), 5, rnd.choice(["white", "yellow", "lemon", "sky_blue"]), 0.44)
        out.append(_finish("stars", f"Star Field {len(out)+1}", g,
                           ["star", "field", "night"], f"field-{j}"))
        j += 1
    return out[:100]


# ── FLOWERS ──────────────────────────────────────────────────────────────────

def _flower(g, cx, cy, petals, r_pet, pet_col, cen_col, r_cen):
    for k in range(petals):
        a = 2 * math.pi * k / petals - math.pi / 2
        px, py = cx + (r_cen + r_pet) * math.cos(a), cy + (r_cen + r_pet) * math.sin(a)
        g.disc(px, py, r_pet, pet_col)
    g.disc(cx, cy, r_cen, cen_col)


def generate_flowers():
    out = []
    combos = [("hot_pink", "yellow"), ("red", "banana"), ("purple", "lemon"),
              ("white", "yellow"), ("orange", "dark_brown"), ("light_pink", "cheddar"),
              ("lavender", "orange"), ("aqua", "hot_pink"), ("magenta", "lemon"),
              ("sky_blue", "yellow"), ("neon_green", "red"), ("blush", "plum")]
    # classic round-petal flowers
    for i, (p, c) in enumerate(combos):
        for petals in (5, 6, 8):
            if len(out) >= 42:
                break
            s = [22, 26, 29][petals % 3] if False else 26
            g = Grid(s, s)
            cc = (s - 1) / 2
            _flower(g, cc, cc, petals, s * 0.15, p, c, s * 0.12)
            out.append(_finish("flowers", f"{p.replace('_',' ').title()} Bloom {petals}p", g,
                               ["flower", "bloom", p], f"bloom-{p}-{c}-{petals}"))
    # daisies (white/colored petals, contrasting center)
    for i, (p, c) in enumerate([("white", "yellow"), ("light_pink", "cheddar"),
                                ("lemon", "orange"), ("periwinkle", "yellow"),
                                ("blush", "dark_brown"), ("toothpaste", "hot_pink")]):
        s = 27
        cc = (s - 1) / 2
        g = Grid(s, s)
        for k in range(12):
            a = 2 * math.pi * k / 12 - math.pi / 2
            g.ellipse(cc + s * 0.3 * math.cos(a), cc + s * 0.3 * math.sin(a),
                      s * 0.08, s * 0.05, p)
        g.disc(cc, cc, s * 0.13, c)
        out.append(_finish("flowers", f"Daisy {i+1}", g, ["flower", "daisy"], f"daisy-{i}"))
    # sunflowers
    for i, cen in enumerate(["dark_brown", "brown", "rust"]):
        s = 29
        cc = (s - 1) / 2
        g = Grid(s, s)
        for ring, pr in ((16, 0.36), (12, 0.28)):
            for k in range(ring):
                a = 2 * math.pi * k / ring
                g.disc(cc + s * pr * math.cos(a), cc + s * pr * math.sin(a),
                       s * 0.07, "yellow" if ring == 16 else "cheddar")
        g.disc(cc, cc, s * 0.18, cen)
        out.append(_finish("flowers", f"Sunflower {i+1}", g, ["flower", "sunflower"], f"sun-{i}"))
    # tulips with stems
    for i, (p, st) in enumerate([("red", "green"), ("hot_pink", "forest"),
                                 ("purple", "dark_green"), ("orange", "green"),
                                 ("yellow", "forest"), ("magenta", "dark_green")]):
        s = 29
        g = Grid(s, s)
        cx = (s - 1) / 2
        g.poly([(cx - 5, 8), (cx + 5, 8), (cx + 4, 14), (cx, 12), (cx - 4, 14)], p)
        g.ellipse(cx - 4, 8, 2.4, 3, p)
        g.ellipse(cx + 4, 8, 2.4, 3, p)
        g.ellipse(cx, 7, 2.4, 3.4, p)
        g.line(cx, 14, cx, s - 3, st, t=0)
        g.disc(cx, 14, 0.6, st)
        g.poly([(cx, 20), (cx - 6, 22), (cx, 24)], st)
        g.poly([(cx, 22), (cx + 6, 24), (cx, 26)], st)
        out.append(_finish("flowers", f"Tulip {i+1}", g, ["flower", "tulip"], f"tulip-{i}"))
    # roses (concentric rings)
    for i, cols in enumerate([("dark_red", "red", "hot_pink"),
                              ("purple", "magenta", "light_pink"),
                              ("orange", "cheddar", "yellow"),
                              ("dark_purple", "plum", "lavender")]):
        s = 26
        cc = (s - 1) / 2
        g = Grid(s, s)
        for ri, r in enumerate([0.44, 0.32, 0.2, 0.09]):
            g.disc(cc, cc, s * r, cols[ri % len(cols)])
        out.append(_finish("flowers", f"Rose {i+1}", g, ["flower", "rose"], f"rose-{i}"))
    # top up with more blooms
    j = 0
    while len(out) < 100:
        p, c = combos[j % len(combos)]
        petals = (5, 6, 8)[j % 3]
        s = 24
        cc = (s - 1) / 2
        g = Grid(s, s)
        _flower(g, cc, cc, petals, s * 0.16, c, p, s * 0.12)
        out.append(_finish("flowers", f"Little Flower {len(out)+1}", g,
                           ["flower", p], f"little-{j}-{p}-{petals}"))
        j += 1
    return out[:100]


# ── RAINBOWS ─────────────────────────────────────────────────────────────────

def generate_rainbows():
    out = []
    orders = [RAINBOW, list(reversed(RAINBOW)), RAINBOW6, PASTELS,
              ["red", "orange", "yellow", "green", "aqua", "blue", "purple"],
              ["hot_pink", "orange", "lemon", "neon_green", "aqua", "blue", "magenta"]]
    # arc rainbows over sky/white with cloud ends
    for i, order in enumerate(orders):
        for bg in ("white", "sky_blue"):
            s = 29
            g = Grid(s, s)
            g.fill(bg)
            cx, cy = (s - 1) / 2, s - 2
            t = 1.6
            for bi, col in enumerate(order):
                rr = s * 0.46 - bi * t
                for y in range(s):
                    for x in range(s):
                        d = math.hypot(x - cx, y - cy)
                        if rr - t <= d <= rr and y <= cy:
                            g.set(x, y, col)
            g.disc(cx - s * 0.42, cy, 2.2, "white")
            g.disc(cx + s * 0.42, cy, 2.2, "white")
            out.append(_finish("rainbows", f"Rainbow Arc {len(out)+1}", g,
                               ["rainbow", "arc"], f"arc-{i}-{bg}"))
    # full spectrum stripes
    for i, order in enumerate(orders):
        for orient in ("horiz", "vert"):
            s = 28
            g = Grid(s, s)
            band = s / len(order)
            for y in range(s):
                for x in range(s):
                    idx = int((y if orient == "horiz" else x) / band)
                    g.set(x, y, order[min(idx, len(order) - 1)])
            out.append(_finish("rainbows", f"Spectrum {len(out)+1}", g,
                               ["rainbow", "stripes"], f"spec-{i}-{orient}"))
    # ombre gradients (single-hue ramps)
    ramps = [["light_pink", "pink", "hot_pink", "magenta"],
             ["toothpaste", "light_blue", "sky_blue", "blue", "dark_blue"],
             ["lemon", "yellow", "cheddar", "orange", "pumpkin"],
             ["light_green", "neon_green", "green", "forest", "dark_green"],
             ["light_lavender", "lavender", "purple", "dark_purple"],
             ["peach", "orange", "red", "dark_red"]]
    for i, ramp in enumerate(ramps):
        for orient in ("horiz", "vert"):
            s = 26
            g = Grid(s, s)
            band = s / len(ramp)
            for y in range(s):
                for x in range(s):
                    idx = int((y if orient == "horiz" else x) / band)
                    g.set(x, y, ramp[min(idx, len(ramp) - 1)])
            out.append(_finish("rainbows", f"Ombre {len(out)+1}", g,
                               ["rainbow", "ombre", "gradient"], f"ombre-{i}-{orient}"))
    # sunsets: warm bands + sun
    for i, sky in enumerate([["dark_purple", "purple", "hot_pink", "orange", "yellow"],
                             ["navy", "blue", "magenta", "pumpkin", "cheddar"],
                             ["dark_blue", "purple", "red", "orange", "lemon"]]):
        s = 28
        g = Grid(s, s)
        band = s / len(sky)
        for y in range(s):
            for x in range(s):
                g.set(x, y, sky[min(int(y / band), len(sky) - 1)])
        g.disc((s - 1) / 2, s * 0.62, s * 0.16, "yellow")
        out.append(_finish("rainbows", f"Sunset {i+1}", g, ["rainbow", "sunset"], f"sunset-{i}"))
    # diagonal spectrum (8)
    for i, order in enumerate(orders):
        if i >= 8:
            break
        s = 28
        g = Grid(s, s)
        band = (2 * s) / len(order)
        for y in range(s):
            for x in range(s):
                g.set(x, y, order[min(int((x + y) / band), len(order) - 1)])
        out.append(_finish("rainbows", f"Diagonal Spectrum {i+1}", g,
                           ["rainbow", "diagonal"], f"diag-{i}"))
    # concentric rainbow rings / full circle (8)
    for i, order in enumerate(orders):
        if i >= 8:
            break
        s = 29
        g = Grid(s, s)
        g.fill("white")
        cc = (s - 1) / 2
        for bi, col in enumerate(order):
            g.ring(cc, cc, s * 0.46 - bi * 1.6, col, 1.6)
        out.append(_finish("rainbows", f"Rainbow Rings {i+1}", g,
                           ["rainbow", "rings", "concentric"], f"rings-{i}"))
    # double rainbows over sky (6)
    for i, order in enumerate(orders):
        if i >= 6:
            break
        s = 29
        g = Grid(s, s)
        g.fill("sky_blue")
        cx, cy = (s - 1) / 2, s - 1
        for offset, thick in ((0, 1.3), (len(order) + 1, 0.9)):
            for bi, col in enumerate(order):
                rr = s * 0.5 - (bi + offset) * 1.3
                if rr < 2:
                    continue
                for y in range(s):
                    for x in range(s):
                        d = math.hypot(x - cx, y - cy)
                        if rr - thick <= d <= rr and y <= cy:
                            g.set(x, y, col)
        out.append(_finish("rainbows", f"Double Rainbow {i+1}", g,
                           ["rainbow", "double"], f"double-{i}"))
    # rainbow chevrons (10)
    for i, order in enumerate(orders + [BRIGHTS, ["red", "orange", "yellow", "green", "aqua", "blue"],
                                        ["hot_pink", "orange", "lemon", "neon_green", "aqua", "purple"],
                                        PASTELS]):
        if i >= 10:
            break
        s = 28
        g = Grid(s, s)
        for y in range(s):
            for x in range(s):
                z = abs(((x + y) % (2 * len(order))) - len(order))
                g.set(x, y, order[(z + y // 3) % len(order)])
        out.append(_finish("rainbows", f"Rainbow Chevron {i+1}", g,
                           ["rainbow", "chevron"], f"chev-{i}"))
    # rainbow confetti dots (10)
    for i in range(10):
        s = 27
        g = Grid(s, s)
        g.fill(["white", "navy", "sky_blue", "cream", "black"][i % 5])
        rnd = random.Random(600 + i)
        pal = [RAINBOW, BRIGHTS, PASTELS][i % 3]
        for cy in range(3, s, 5):
            for cx in range(3, s, 5):
                g.disc(cx + rnd.randint(-1, 1), cy + rnd.randint(-1, 1), 1.5, rnd.choice(pal))
        out.append(_finish("rainbows", f"Rainbow Confetti {i+1}", g,
                           ["rainbow", "confetti", "dots"], f"conf-{i}"))
    # more sunsets (5)
    for i, sky in enumerate([["dark_purple", "magenta", "hot_pink", "orange", "yellow", "lemon"],
                             ["navy", "purple", "red", "orange", "cheddar", "banana"],
                             ["dark_blue", "blue", "magenta", "pumpkin", "yellow", "cream"],
                             ["plum", "hot_pink", "orange", "cheddar", "lemon", "cream"],
                             ["dark_purple", "blue", "teal", "orange", "red", "yellow"]]):
        s = 28
        g = Grid(s, s)
        band = s / len(sky)
        for y in range(s):
            for x in range(s):
                g.set(x, y, sky[min(int(y / band), len(sky) - 1)])
        g.disc((s - 1) / 2, s * 0.6, s * 0.15, "yellow")
        out.append(_finish("rainbows", f"Sunset {i+4}", g, ["rainbow", "sunset"], f"sunset2-{i}"))
    # top up: rainbows with a cloud (capped by everything above ~ up to 100)
    j = 0
    while len(out) < 100:
        order = orders[j % len(orders)]
        s = 27
        g = Grid(s, s)
        g.fill("sky_blue")
        cx, cy = (s - 1) / 2, s - 1
        for bi, col in enumerate(order):
            rr = s * 0.5 - bi * 1.5
            for y in range(s):
                for x in range(s):
                    d = math.hypot(x - cx, y - cy)
                    if rr - 1.5 <= d <= rr and y <= cy:
                        g.set(x, y, col)
        g.disc(6, 7, 2.4, "white"); g.disc(9, 7, 3, "white"); g.disc(12, 7, 2.4, "white")
        g.disc(s - 8, s - 6, 2.2, "white"); g.disc(s - 11, s - 6, 2.6, "white")
        out.append(_finish("rainbows", f"Rainbow Sky {len(out)+1}", g,
                           ["rainbow", "cloud"], f"sky-{j}"))
        j += 1
    return out[:100]


# ── SPACE ────────────────────────────────────────────────────────────────────

def _starry(g, seed, n=10):
    rnd = random.Random(seed)
    for _ in range(n):
        g.set(rnd.randint(0, g.w - 1), rnd.randint(0, g.h - 1),
              rnd.choice(["white", "lemon", "sky_blue"]))


def _banded_planet(g, cc, s, base, band, style):
    g.disc(cc, cc, s * 0.34, base)
    R2 = (s * 0.34) ** 2
    if style == 0:      # horizontal bands
        for yy in range(int(cc - s * 0.34), int(cc + s * 0.34)):
            if (yy // 3) % 2 == 0:
                for xx in range(s):
                    if (xx - cc) ** 2 + (yy - cc) ** 2 <= R2:
                        g.set(xx, yy, band)
    elif style == 1:    # swirl spots
        rnd = random.Random(int(cc * 7) + s)
        for _ in range(4):
            g.disc(rnd.uniform(cc - 5, cc + 5), rnd.uniform(cc - 5, cc + 5),
                   rnd.uniform(1.5, 3), band)
    else:               # crescent shading
        g.disc(cc - s * 0.1, cc - s * 0.1, s * 0.24, band)


def generate_space():
    out = []
    # banded planets (20)
    planets = [("blue", "sky_blue"), ("orange", "cheddar"), ("red", "dark_red"),
               ("purple", "lavender"), ("teal", "aqua"), ("green", "light_green"),
               ("magenta", "hot_pink"), ("dark_blue", "blue"), ("pumpkin", "yellow"),
               ("dark_purple", "plum"), ("rust", "orange"), ("forest", "neon_green"),
               ("hot_pink", "light_pink"), ("turquoise", "toothpaste"),
               ("plum", "magenta"), ("caramel", "cream"), ("navy", "sky_blue"),
               ("dark_green", "light_green"), ("brown", "tan"), ("blue", "aqua")]
    for i, (base, band) in enumerate(planets):
        s = 29
        g = Grid(s, s)
        g.fill("navy"); _starry(g, i, 12)
        _banded_planet(g, (s - 1) / 2, s, base, band, i % 3)
        out.append(_finish("space", f"Planet {i+1}", g, ["space", "planet"], f"planet-{i}"))
    # Earth (4)
    for i in range(4):
        s = 29
        g = Grid(s, s)
        g.fill("navy"); _starry(g, 15 + i, 12)
        cc = (s - 1) / 2
        g.disc(cc, cc, s * 0.34, "blue")
        rnd = random.Random(400 + i)
        for _ in range(5):
            g.disc(rnd.uniform(cc - 6, cc + 6), rnd.uniform(cc - 6, cc + 6),
                   rnd.uniform(1.5, 3), rnd.choice(["green", "forest", "green"]))
        out.append(_finish("space", f"Earth {i+1}", g, ["space", "earth", "planet"], f"earth-{i}"))
    # ringed planets / Saturn (8)
    for i, (base, ring) in enumerate([("cheddar", "cream"), ("sky_blue", "white"),
                                      ("orange", "lemon"), ("lavender", "periwinkle"),
                                      ("teal", "toothpaste"), ("pumpkin", "banana"),
                                      ("magenta", "light_pink"), ("caramel", "tan")]):
        s = 29
        g = Grid(s, s)
        g.fill("navy"); _starry(g, 20 + i, 12)
        cc = (s - 1) / 2
        g.ellipse(cc, cc, s * 0.46, s * 0.16, ring)
        g.ellipse(cc, cc, s * 0.34, s * 0.09, "navy")
        g.disc(cc, cc, s * 0.26, base)
        out.append(_finish("space", f"Ringed Planet {i+1}", g, ["space", "saturn"], f"ring-{i}"))
    # moons with craters (6)
    for i, col in enumerate(["light_gray", "silver", "gray", "cream", "tan", "light_gray"]):
        s = 26
        g = Grid(s, s)
        g.fill("dark_blue"); _starry(g, 40 + i, 10)
        cc = (s - 1) / 2
        g.disc(cc, cc, s * 0.34, col)
        rnd = random.Random(50 + i)
        for _ in range(5):
            g.disc(rnd.uniform(cc - 5, cc + 5), rnd.uniform(cc - 5, cc + 5), rnd.uniform(1, 2), "gray")
        out.append(_finish("space", f"Moon {i+1}", g, ["space", "moon"], f"moon-{i}-{col}"))
    # crescent moons (6)
    for i, col in enumerate(["cream", "banana", "silver", "light_gray", "lemon", "white"]):
        s = 24
        g = Grid(s, s)
        g.fill("navy"); _starry(g, 60 + i, 10)
        cc = (s - 1) / 2
        crescent(g, cc, cc, s * 0.34, col, s * 0.18)
        out.append(_finish("space", f"Crescent Moon {i+1}", g, ["space", "crescent"], f"cres-{i}"))
    # rockets (12)
    for i, (body, fin) in enumerate([("red", "silver"), ("white", "red"),
                                     ("orange", "navy"), ("silver", "blue"),
                                     ("hot_pink", "purple"), ("aqua", "dark_blue"),
                                     ("yellow", "red"), ("sky_blue", "navy"),
                                     ("magenta", "purple"), ("cream", "red"),
                                     ("neon_green", "forest"), ("lavender", "purple")]):
        s = 29
        g = Grid(s, s)
        g.fill("navy"); _starry(g, 70 + i, 12)
        cx = (s - 1) / 2
        g.ellipse(cx, s * 0.5, s * 0.12, s * 0.3, body)
        g.poly([(cx, 2), (cx - s * 0.12, s * 0.28), (cx + s * 0.12, s * 0.28)], "red")
        g.disc(cx, s * 0.42, s * 0.06, "sky_blue")
        g.poly([(cx - s * 0.12, s * 0.62), (cx - s * 0.26, s * 0.78), (cx - s * 0.12, s * 0.78)], fin)
        g.poly([(cx + s * 0.12, s * 0.62), (cx + s * 0.26, s * 0.78), (cx + s * 0.12, s * 0.78)], fin)
        g.poly([(cx - s * 0.08, s * 0.8), (cx, s * 0.97), (cx + s * 0.08, s * 0.8)], "orange")
        g.poly([(cx - s * 0.05, s * 0.82), (cx, s * 0.9), (cx + s * 0.05, s * 0.82)], "yellow")
        out.append(_finish("space", f"Rocket {i+1}", g, ["space", "rocket"], f"rocket-{i}"))
    # UFO / flying saucer (10)
    for i, (dome, body) in enumerate([("aqua", "silver"), ("neon_green", "gray"),
                                      ("hot_pink", "light_gray"), ("sky_blue", "silver"),
                                      ("lemon", "gray"), ("lavender", "silver"),
                                      ("turquoise", "light_gray"), ("orange", "gray"),
                                      ("light_green", "silver"), ("magenta", "gray")]):
        s = 27
        g = Grid(s, s)
        g.fill("dark_blue"); _starry(g, 90 + i, 12)
        cx, cy = (s - 1) / 2, s * 0.55
        g.ellipse(cx, cy, s * 0.4, s * 0.13, body)      # saucer
        g.ellipse(cx, cy - s * 0.09, s * 0.18, s * 0.14, dome)  # dome
        for k in (-1, 0, 1):
            g.disc(cx + k * s * 0.16, cy + s * 0.02, 1.2, "yellow")  # lights
        for k in (-1, 1):
            g.line(cx + k * s * 0.28, cy + s * 0.13, cx + k * s * 0.34, cy + s * 0.3, "aqua")  # beams
        out.append(_finish("space", f"UFO {i+1}", g, ["space", "ufo", "saucer"], f"ufo-{i}"))
    # comets (6)
    for i, (head, tail) in enumerate([("white", "sky_blue"), ("lemon", "orange"),
                                      ("aqua", "toothpaste"), ("banana", "cheddar"),
                                      ("hot_pink", "light_pink"), ("sky_blue", "periwinkle")]):
        s = 26
        g = Grid(s, s)
        g.fill("dark_blue"); _starry(g, 80 + i, 10)
        g.disc(s * 0.68, s * 0.32, s * 0.1, head)
        for t in range(4):
            g.line(s * 0.6, s * 0.4, s * 0.16 - t, s * 0.74 + t, tail)
        out.append(_finish("space", f"Comet {i+1}", g, ["space", "comet"], f"comet-{i}"))
    # aliens (8)
    for i, skin in enumerate(["neon_green", "light_green", "aqua", "turquoise",
                              "lavender", "sky_blue", "green", "hot_pink"]):
        s = 26
        g = Grid(s, s)
        g.fill("dark_purple"); _starry(g, 110 + i, 10)
        cc = (s - 1) / 2
        g.ellipse(cc, cc, s * 0.26, s * 0.34, skin)          # big head
        g.ellipse(cc - s * 0.11, cc, s * 0.07, s * 0.11, "black")  # slanted eyes
        g.ellipse(cc + s * 0.11, cc, s * 0.07, s * 0.11, "black")
        g.line(cc - 2, cc + s * 0.22, cc + 2, cc + s * 0.22, "black")  # mouth
        out.append(_finish("space", f"Alien {i+1}", g, ["space", "alien"], f"alien-{i}"))
    # constellations (8)
    for i in range(8):
        s = 29
        g = Grid(s, s)
        g.fill("navy")
        rnd = random.Random(500 + i)
        pts = [(rnd.randint(3, s - 4), rnd.randint(3, s - 4)) for _ in range(rnd.randint(5, 7))]
        for a in range(len(pts) - 1):
            g.line(pts[a][0], pts[a][1], pts[a + 1][0], pts[a + 1][1], "dark_blue")
        for (px, py) in pts:
            _draw_star(g, px, py, 2.4, 5, rnd.choice(["white", "yellow", "sky_blue"]), 0.44)
        out.append(_finish("space", f"Constellation {i+1}", g,
                           ["space", "constellation"], f"const-{i}"))
    # satellites (4)
    for i, panel in enumerate(["sky_blue", "aqua", "blue", "turquoise"]):
        s = 26
        g = Grid(s, s)
        g.fill("navy"); _starry(g, 120 + i, 10)
        cc = (s - 1) / 2
        g.rect(cc - 2, cc - 3, cc + 2, cc + 3, "silver")     # body
        g.rect(cc - 9, cc - 2, cc - 4, cc + 2, panel)        # left panel
        g.rect(cc + 4, cc - 2, cc + 9, cc + 2, panel)        # right panel
        g.line(cc, cc - 3, cc, cc - 7, "silver")             # antenna
        g.disc(cc, cc - 7, 1.2, "red")
        out.append(_finish("space", f"Satellite {i+1}", g, ["space", "satellite"], f"sat-{i}"))
    # suns (fill to 100, capped ~8)
    j = 0
    while len(out) < 100:
        s = 27
        g = Grid(s, s)
        g.fill("navy" if j % 2 else "dark_blue")
        cc = (s - 1) / 2
        col = ["yellow", "cheddar", "orange", "banana"][j % 4]
        rays = 12 + 2 * (j % 3)
        for k in range(rays):
            a = 2 * math.pi * k / rays
            g.line(cc, cc, cc + s * 0.44 * math.cos(a), cc + s * 0.44 * math.sin(a), col)
        g.disc(cc, cc, s * 0.2, col)
        out.append(_finish("space", f"Sun {len(out)+1}", g, ["space", "sun"], f"sunstar-{j}"))
        j += 1
    return out[:100]


# ── EMOJI ────────────────────────────────────────────────────────────────────

def _arc(g, cx, cy, w, depth, col, smile=True):
    """Mouth arc. smile=True dips down in the middle; False arcs up (frown)."""
    steps = max(6, int(w * 2))
    for i in range(steps + 1):
        t = i / steps
        x = cx - w / 2 + t * w
        dip = depth * (1 - (2 * t - 1) ** 2)   # >= 0, peaks at center
        y = cy + dip if smile else cy - dip
        g.disc(x, y, 0.75, col)


def _mouth(g, cc, s, kind, face):
    my = cc + s * 0.15
    if kind == "smile":
        _arc(g, cc, my, s * 0.34, s * 0.11, "black", smile=True)
    elif kind == "frown":
        _arc(g, cc, my + s * 0.05, s * 0.3, s * 0.1, "black", smile=False)
    elif kind == "line":
        g.line(cc - s * 0.14, my, cc + s * 0.14, my, "black")
    elif kind == "grin":
        # open smiling mouth: filled lower half-oval with a tooth strip
        g.ellipse(cc, my, s * 0.2, s * 0.13, "dark_red")
        g.rect(cc - s * 0.2, my - s * 0.14, cc + s * 0.2, my - 1, face)  # cut top → "D"
        g.rect(cc - s * 0.18, my - 1, cc + s * 0.18, my + 1, "white")    # teeth
    elif kind == "open":
        g.ellipse(cc, my + 1, s * 0.16, s * 0.15, "dark_red")
        g.ellipse(cc, my + s * 0.09, s * 0.09, s * 0.06, "red")          # tongue
    elif kind == "o":
        g.disc(cc, my, s * 0.1, "dark_red"); g.ring(cc, my, s * 0.12, "black", 1)
    elif kind == "smallo":
        g.disc(cc, my, s * 0.05, "dark_red"); g.ring(cc, my, s * 0.07, "black", 1)
    elif kind == "tongue":
        _arc(g, cc, my, s * 0.32, s * 0.1, "black", smile=True)
        g.disc(cc + s * 0.05, my + s * 0.08, s * 0.06, "hot_pink")
    elif kind == "kiss":
        g.disc(cc, my, s * 0.05, "red")
        _arc(g, cc, my - 1, s * 0.14, s * 0.05, "red", smile=True)


def generate_emoji():
    out = []
    expressions = [
        ("Happy", "dots", "smile", None),
        ("Grinning", "dots", "grin", None),
        ("Big Smile", "arcs", "grin", None),
        ("Winking", "wink", "smile", None),
        ("Love", "hearts", "smile", None),
        ("Cool", "shades", "smile", None),
        ("Sad", "dots", "frown", None),
        ("Crying", "dots", "frown", "tear"),
        ("Surprised", "wide", "o", None),
        ("Silly", "dots", "tongue", None),
        ("Neutral", "dots", "line", None),
        ("Laughing", "arcs", "open", None),
        ("Kiss", "dots", "kiss", None),
        ("Star Eyes", "stars", "grin", None),
        ("Sleepy", "arcs", "smallo", None),
        ("Angry", "brows", "frown", None),
    ]
    while len(out) < 100:
        idx = len(out)
        name, eyes, mouth, extra = expressions[idx % len(expressions)]
        face = FACES[(idx // len(expressions)) % len(FACES)]
        s = 24
        g = Grid(s, s)
        cc = (s - 1) / 2
        g.disc(cc, cc, s * 0.45, face)
        ex, ey, er = s * 0.17, s * 0.1, s * 0.065
        if eyes == "dots":
            g.disc(cc - ex, cc - ey, er, "black"); g.disc(cc + ex, cc - ey, er, "black")
        elif eyes == "wide":
            g.disc(cc - ex, cc - ey, er * 1.5, "white"); g.disc(cc + ex, cc - ey, er * 1.5, "white")
            g.disc(cc - ex, cc - ey, er * 0.8, "black"); g.disc(cc + ex, cc - ey, er * 0.8, "black")
        elif eyes == "wink":
            g.disc(cc - ex, cc - ey, er, "black")
            _arc(g, cc + ex, cc - ey, er * 2, er, "black", smile=True)
        elif eyes == "arcs":
            _arc(g, cc - ex, cc - ey, er * 2, er, "black", smile=True)
            _arc(g, cc + ex, cc - ey, er * 2, er, "black", smile=True)
        elif eyes == "hearts":
            _fill_heart(g, cc - ex, cc - ey, 6, "red"); _fill_heart(g, cc + ex, cc - ey, 6, "red")
        elif eyes == "stars":
            g.poly(star_points(cc - ex, cc - ey, er * 1.7, er * 0.7, 5), "sky_blue")
            g.poly(star_points(cc + ex, cc - ey, er * 1.7, er * 0.7, 5), "sky_blue")
        elif eyes == "shades":
            g.rect(cc - ex - er * 1.3, cc - ey - er, cc - ex + er * 1.3, cc - ey + er, "black")
            g.rect(cc + ex - er * 1.3, cc - ey - er, cc + ex + er * 1.3, cc - ey + er, "black")
            g.line(cc - ex + er, cc - ey, cc + ex - er, cc - ey, "black")
        elif eyes == "brows":
            g.disc(cc - ex, cc - ey, er, "black"); g.disc(cc + ex, cc - ey, er, "black")
            g.line(cc - ex - er, cc - ey - er - 1, cc - ex + er, cc - ey - 1, "dark_brown")
            g.line(cc + ex - er, cc - ey - 1, cc + ex + er, cc - ey - er - 1, "dark_brown")
        _mouth(g, cc, s, mouth, face)
        if extra == "tear":
            g.disc(cc - ex, cc + s * 0.05, 1.5, "sky_blue")
        if name in ("Happy", "Love", "Silly", "Kiss"):
            g.disc(cc - s * 0.3, cc + s * 0.06, 1.7, "blush")
            g.disc(cc + s * 0.3, cc + s * 0.06, 1.7, "blush")
        out.append(_finish("emoji", f"{name} Face {len(out)+1}", g,
                           ["emoji", "face", name.split()[0].lower()],
                           f"emoji-{name}-{face}-{len(out)}"))
    return out[:100]


# ── GEMS ─────────────────────────────────────────────────────────────────────

def generate_gems():
    out = []

    def sparkle(g, x, y):
        g.set(x, y, "white"); g.set(x - 1, y, "white"); g.set(x + 1, y, "white")
        g.set(x, y - 1, "white"); g.set(x, y + 1, "white")

    # round brilliant
    for i, hue in enumerate(GEM_HUES):
        s = 24
        cc = (s - 1) / 2
        g = Grid(s, s)
        g.disc(cc, cc, s * 0.42, hue)
        g.disc(cc, cc - s * 0.12, s * 0.24, GEM_LIGHT.get(hue, "white"))
        for k in range(8):
            a = 2 * math.pi * k / 8
            g.line(cc, cc, cc + s * 0.42 * math.cos(a), cc + s * 0.42 * math.sin(a),
                   "white" if k % 2 else GEM_LIGHT.get(hue, "white"))
        sparkle(g, int(cc - s * 0.14), int(cc - s * 0.16))
        out.append(_finish("gems", f"Round Gem {hue.replace('_',' ').title()}", g,
                           ["gem", "round", hue], f"round-{hue}"))
    # princess (diamond square)
    for i, hue in enumerate(GEM_HUES):
        s = 24
        cc = (s - 1) / 2
        g = Grid(s, s)
        g.poly(reg_polygon(cc, cc, s * 0.44, 4, rot=0), hue)
        g.poly(reg_polygon(cc, cc, s * 0.22, 4, rot=0), GEM_LIGHT.get(hue, "white"))
        g.line(cc - s * 0.44, cc, cc + s * 0.44, cc, "white")
        g.line(cc, cc - s * 0.44, cc, cc + s * 0.44, "white")
        sparkle(g, int(cc - 3), int(cc - 3))
        out.append(_finish("gems", f"Princess Gem {hue.replace('_',' ').title()}", g,
                           ["gem", "princess", hue], f"princess-{hue}"))
    # marquise (pointed oval)
    for i, hue in enumerate(GEM_HUES[:11]):
        s = 24
        cc = (s - 1) / 2
        g = Grid(s, s)
        g.poly([(cc, 3), (cc + s * 0.2, cc), (cc, s - 4), (cc - s * 0.2, cc)], hue)
        g.line(cc, 3, cc, s - 4, GEM_LIGHT.get(hue, "white"))
        sparkle(g, int(cc), int(cc - 3))
        out.append(_finish("gems", f"Marquise Gem {i+1}", g,
                           ["gem", "marquise", hue], f"marq-{hue}"))
    # emerald cut (stepped rectangle)
    for i, hue in enumerate(GEM_HUES[:11]):
        s = 22
        g = Grid(s, s)
        cx = (s - 1) / 2
        g.rect(cx - 6, 4, cx + 6, s - 5, hue)
        g.frame(cx - 6, 4, cx + 6, s - 5, GEM_LIGHT.get(hue, "white"), 1)
        g.frame(cx - 3, 7, cx + 3, s - 8, "white", 1)
        out.append(_finish("gems", f"Emerald Cut {i+1}", g,
                           ["gem", "emerald", hue], f"emerald-{hue}"))
    # heart gems (11)
    for i, hue in enumerate(GEM_HUES):
        s = 22
        g = Grid(s, s)
        _fill_heart(g, (s - 1) / 2, (s - 1) / 2 - 1, s * 0.9, hue)
        _fill_heart(g, (s - 1) / 2, (s - 1) / 2 - 1, s * 0.5, GEM_LIGHT.get(hue, "white"))
        sparkle(g, int((s - 1) / 2 - 2), int((s - 1) / 2 - 3))
        out.append(_finish("gems", f"Heart Gem {i+1}", g, ["gem", "heart", hue], f"heartgem-{hue}"))
    # oval gems (8)
    for i, hue in enumerate(GEM_HUES[:8]):
        s = 22
        cc = (s - 1) / 2
        g = Grid(s, s)
        g.ellipse(cc, cc, s * 0.24, s * 0.42, hue)
        g.ellipse(cc, cc - s * 0.1, s * 0.13, s * 0.2, GEM_LIGHT.get(hue, "white"))
        for k in range(6):
            a = 2 * math.pi * k / 6
            g.line(cc, cc, cc + s * 0.22 * math.cos(a), cc + s * 0.4 * math.sin(a), "white")
        sparkle(g, int(cc - 2), int(cc - s * 0.18))
        out.append(_finish("gems", f"Oval Gem {i+1}", g, ["gem", "oval", hue], f"oval-{hue}"))
    # trillion (triangle) gems (8)
    for i, hue in enumerate(GEM_HUES[:8]):
        s = 22
        cc = (s - 1) / 2
        g = Grid(s, s)
        g.poly(reg_polygon(cc, cc + 1, s * 0.42, 3, rot=-math.pi / 2), hue)
        g.poly(reg_polygon(cc, cc + 1, s * 0.2, 3, rot=-math.pi / 2), GEM_LIGHT.get(hue, "white"))
        sparkle(g, int(cc), int(cc - 2))
        out.append(_finish("gems", f"Trillion Gem {i+1}", g, ["gem", "trillion", hue], f"tri-{hue}"))
    # cushion (rounded square) gems (8)
    for i, hue in enumerate(GEM_HUES[:8]):
        s = 22
        cc = (s - 1) / 2
        g = Grid(s, s)
        g.disc(cc, cc, s * 0.38, hue)
        g.rect(cc - s * 0.3, cc - s * 0.3, cc + s * 0.3, cc + s * 0.3, hue)
        g.disc(cc, cc - s * 0.08, s * 0.16, GEM_LIGHT.get(hue, "white"))
        g.line(cc - s * 0.3, cc, cc + s * 0.3, cc, "white")
        g.line(cc, cc - s * 0.3, cc, cc + s * 0.3, "white")
        sparkle(g, int(cc - 3), int(cc - 3))
        out.append(_finish("gems", f"Cushion Gem {i+1}", g, ["gem", "cushion", hue], f"cush-{hue}"))
    # teardrop / pear gems (10, capped)
    for i, hue in enumerate(GEM_HUES[:10]):
        s = 22
        cx = (s - 1) / 2
        g = Grid(s, s)
        g.poly([(cx, 3), (cx + s * 0.24, s * 0.55), (cx, s - 3), (cx - s * 0.24, s * 0.55)], hue)
        g.disc(cx, s * 0.62, s * 0.12, GEM_LIGHT.get(hue, "white"))
        sparkle(g, int(cx - 2), int(s * 0.4))
        out.append(_finish("gems", f"Teardrop Gem {i+1}", g, ["gem", "pear", hue], f"pear-{hue}"))
    # gem clusters: three small gems (fill to 100)
    j = 0
    trios = [("red", "hot_pink", "purple"), ("blue", "aqua", "teal"),
             ("yellow", "orange", "red"), ("magenta", "purple", "dark_blue"),
             ("green", "aqua", "blue"), ("hot_pink", "magenta", "purple"),
             ("orange", "yellow", "green"), ("teal", "blue", "purple"),
             ("red", "orange", "yellow"), ("purple", "blue", "aqua")]
    while len(out) < 100:
        a, b, c = trios[j % len(trios)]
        s = 24
        g = Grid(s, s)
        for (px, py, hue, r) in [(s * 0.5, s * 0.34, a, s * 0.16),
                                 (s * 0.36, s * 0.6, b, s * 0.13),
                                 (s * 0.64, s * 0.6, c, s * 0.13)]:
            g.poly(reg_polygon(px, py, r, 4, rot=0), hue)
            g.poly(reg_polygon(px, py, r * 0.5, 4, rot=0), GEM_LIGHT.get(hue, "white"))
        out.append(_finish("gems", f"Gem Cluster {len(out)+1}", g,
                           ["gem", "cluster", "jewels"], f"cluster-{j}"))
        j += 1
    return out[:100]


GENERATORS = {
    "geometric": generate_geometric,
    "mandalas": generate_mandalas,
    "hearts": generate_hearts,
    "stars": generate_stars,
    "flowers": generate_flowers,
    "rainbows": generate_rainbows,
    "space": generate_space,
    "emoji": generate_emoji,
    "gems": generate_gems,
}


def generate():
    out = []
    for cat, fn in GENERATORS.items():
        out += fn()
    return out


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1 and sys.argv[1] in GENERATORS:
        pats = GENERATORS[sys.argv[1]]()
    else:
        pats = generate()
    json.dump({"version": 1, "patterns": pats}, open("/tmp/gen.json", "w"))
    from collections import Counter
    print("total", len(pats))
    print(Counter(p["category"] for p in pats))
