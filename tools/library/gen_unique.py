"""200-unique overhauled generators.

Each category here produces 200 STRUCTURALLY-distinct designs (variety comes
from shape/composition, never from color). uniqueness.dedup guarantees no two
shipped patterns share a color-agnostic signature.
"""
import math

from beadlib import make_pattern, stable_id
from canvas import Grid, star_points, reg_polygon, heart_points
from uniqueness import signature

PAIRS = [("navy", "white"), ("red", "cream"), ("teal", "banana"),
         ("hot_pink", "light_pink"), ("purple", "lemon"), ("forest", "light_green"),
         ("orange", "dark_blue"), ("dark_red", "peach"), ("blue", "aqua"),
         ("plum", "banana"), ("black", "yellow"), ("dark_green", "cream"),
         ("magenta", "toothpaste"), ("rust", "cream"), ("dark_purple", "aqua")]
TRIOS = [("red", "white", "navy"), ("teal", "cream", "orange"),
         ("purple", "lemon", "hot_pink"), ("forest", "banana", "dark_red"),
         ("navy", "sky_blue", "white"), ("black", "red", "yellow")]


def _emit(cat, gens, target=200):
    """Run builders, tag with palette, dedup by structure, take `target`."""
    out, seen = [], set()
    i = 0
    for title, g, tags in gens:
        pat = make_pattern(stable_id(cat, f"{title}-{i}"), title, cat,
                           g.w, g.h, g.cells(), tags + [cat])
        sig = signature(pat)
        if sig in seen:
            i += 1
            continue
        seen.add(sig)
        out.append(pat)
        i += 1
        if len(out) >= target:
            break
    return out


# ── GEOMETRIC ────────────────────────────────────────────────────────────────

def _geo_configs():
    S = 28
    gens = []

    def add(title, tags, fn):
        g = Grid(S, S)
        fn(g)
        gens.append((title, g, tags))

    def pair(i):
        return PAIRS[i % len(PAIRS)]

    n = 0
    # stripes: 4 orientations x widths
    for oi, orient in enumerate(("vert", "horiz", "diag", "anti")):
        for w in range(1, 8):
            a, b = pair(n); n += 1
            def fn(g, orient=orient, w=w, a=a, b=b):
                for y in range(g.h):
                    for x in range(g.w):
                        k = {"vert": x, "horiz": y, "diag": x + y, "anti": x - y + g.h}[orient]
                        g.set(x, y, a if (k // w) % 2 == 0 else b)
            add(f"{orient.title()} Stripes w{w}", ["stripe"], fn)
    # checkerboards + offset
    for bs in range(1, 8):
        a, b = pair(n); n += 1
        add(f"Checker {bs}", ["checker"],
            lambda g, bs=bs, a=a, b=b: [g.set(x, y, a if ((x // bs) + (y // bs)) % 2 == 0 else b)
                                        for y in range(g.h) for x in range(g.w)])
    # concentric shapes
    def draw_concentric(g, shape, t, cols):
        c = (g.w - 1) / 2
        for y in range(g.h):
            for x in range(g.w):
                if shape == "square":
                    d = max(abs(x - c), abs(y - c))
                elif shape == "diamond":
                    d = abs(x - c) + abs(y - c)
                elif shape == "circle":
                    d = math.hypot(x - c, y - c)
                else:  # cross-rings
                    d = min(abs(x - c), abs(y - c))
                g.set(x, y, cols[int(d // t) % len(cols)])
    for shape in ("square", "diamond", "circle", "crossring"):
        for t in (1, 2, 3):
            cols = TRIOS[n % len(TRIOS)]; n += 1
            add(f"Concentric {shape} t{t}", ["concentric"],
                lambda g, shape=shape, t=t, cols=cols: draw_concentric(g, shape, t, cols))
    # nested frames
    for gap in (1, 2, 3, 4):
        a, b = pair(n); n += 1
        def fn(g, gap=gap, a=a, b=b):
            for k in range(g.w // 2):
                g.frame(k, k, g.w - 1 - k, g.h - 1 - k, a if (k // gap) % 2 == 0 else b, 1)
        add(f"Nested Frames g{gap}", ["frame"], fn)
    # cross / plus / X
    for w in range(1, 5):
        a, b = pair(n); n += 1
        def fn(g, w=w, a=a, b=b):
            c = g.w // 2
            g.fill(b); g.rect(c - w, 0, c + w, g.h - 1, a); g.rect(0, c - w, g.w - 1, c + w, a)
        add(f"Plus w{w}", ["cross"], fn)
    for w in range(1, 4):
        a, b = pair(n); n += 1
        def fn(g, w=w, a=a, b=b):
            g.fill(b)
            for x in range(g.w):
                for dw in range(-w, w + 1):
                    g.set(x, x + dw, a); g.set(x, g.h - 1 - x + dw, a)
        add(f"X-Cross w{w}", ["cross"], fn)
    # grids of shapes
    def shapegrid(g, spacing, shape, a, b):
        g.fill(b)
        r = spacing * 0.32
        for cy in range(spacing // 2, g.h, spacing):
            for cx in range(spacing // 2, g.w, spacing):
                if shape == "dot":
                    g.disc(cx, cy, r, a)
                elif shape == "square":
                    g.rect(cx - r, cy - r, cx + r, cy + r, a)
                elif shape == "diamond":
                    g.poly(reg_polygon(cx, cy, r + 0.5, 4, rot=0), a)
                elif shape == "triangle":
                    g.poly(reg_polygon(cx, cy, r + 0.6, 3, rot=-math.pi / 2), a)
                elif shape == "ring":
                    g.ring(cx, cy, r + 0.5, a, 1)
                elif shape == "plus":
                    g.rect(cx - 0.6, cy - r, cx + 0.6, cy + r, a); g.rect(cx - r, cy - 0.6, cx + r, cy + 0.6, a)
                elif shape == "cross":
                    g.line(cx - r, cy - r, cx + r, cy + r, a); g.line(cx - r, cy + r, cx + r, cy - r, a)
                elif shape == "star":
                    g.poly(star_points(cx, cy, r + 1, (r + 1) * 0.45, 5), a)
                elif shape == "heart":
                    g.poly(heart_points(cx, cy, spacing * 0.9), a)
    for shape in ("dot", "square", "diamond", "triangle", "ring", "plus", "cross", "star", "heart"):
        for spacing in (4, 5, 6, 7):
            a, b = pair(n); n += 1
            add(f"{shape.title()} Grid s{spacing}", ["grid", shape],
                lambda g, spacing=spacing, shape=shape, a=a, b=b: shapegrid(g, spacing, shape, a, b))
    # chevron / zigzag
    for period in range(2, 8):
        cols = TRIOS[n % len(TRIOS)]; n += 1
        def fn(g, period=period, cols=cols):
            for y in range(g.h):
                for x in range(g.w):
                    z = abs(((x + y) % (2 * period)) - period)
                    g.set(x, y, cols[(z + y // period) % len(cols)])
        add(f"Chevron p{period}", ["chevron"], fn)
    for period in range(3, 8):
        a, b = pair(n); n += 1
        def fn(g, period=period, a=a, b=b):
            for y in range(g.h):
                off = abs((y % (2 * period)) - period)
                for x in range(g.w):
                    g.set(x, y, a if ((x + off) // period) % 2 == 0 else b)
        add(f"Zigzag p{period}", ["zigzag"], fn)
    # half-square triangles
    for orient in range(4):
        for block in (3, 4, 5, 6, 7):
            a, b = pair(n); n += 1
            def fn(g, orient=orient, block=block, a=a, b=b):
                for y in range(g.h):
                    for x in range(g.w):
                        lx, ly = x % block, y % block
                        cond = {0: lx + ly < block, 1: lx + ly >= block,
                                2: lx < ly, 3: lx >= ly}[orient]
                        g.set(x, y, a if cond else b)
            add(f"Triangles o{orient} b{block}", ["triangle"], fn)
    # sunburst / pie
    for rays in (6, 8, 10, 12, 16, 20, 24):
        a, b = pair(n); n += 1
        def fn(g, rays=rays, a=a, b=b):
            c = (g.w - 1) / 2
            g.fill(b)
            for y in range(g.h):
                for x in range(g.w):
                    ang = math.atan2(y - c, x - c)
                    if int((ang + math.pi) / (2 * math.pi) * rays) % 2 == 0:
                        g.set(x, y, a)
        add(f"Sunburst r{rays}", ["sunburst"], fn)
    # bullseye thin rings
    for count in (3, 4, 5, 6, 7, 8):
        cols = TRIOS[n % len(TRIOS)]; n += 1
        def fn(g, count=count, cols=cols):
            c = (g.w - 1) / 2
            maxr = g.w / 2
            for i in range(count):
                g.ring(c, c, maxr * (count - i) / count, cols[i % len(cols)], maxr / count)
        add(f"Bullseye {count}", ["bullseye"], fn)
    # waves
    for period in range(3, 9):
        a, b = pair(n); n += 1
        def fn(g, period=period, a=a, b=b):
            for y in range(g.h):
                for x in range(g.w):
                    yy = y + 2 * math.sin(x * 2 * math.pi / period)
                    g.set(x, y, a if int(yy // 2) % 2 == 0 else b)
        add(f"Waves p{period}", ["wave"], fn)
    # brick / basketweave / herringbone
    for off in (2, 3, 4):
        a, b = pair(n); n += 1
        def fn(g, off=off, a=a, b=b):
            bh = 3
            for y in range(g.h):
                row = y // bh
                for x in range(g.w):
                    g.set(x, y, a if ((x + row * off) // (off * 2)) % 2 == 0 else b)
            for y in range(0, g.h, bh):
                for x in range(g.w):
                    g.set(x, y, b)
        add(f"Brick o{off}", ["brick"], fn)
    for block in (2, 3, 4):
        a, b = pair(n); n += 1
        def fn(g, block=block, a=a, b=b):
            for y in range(g.h):
                for x in range(g.w):
                    cellx, celly = x // block, y // block
                    horiz = (cellx + celly) % 2 == 0
                    inner = (y % block) if horiz else (x % block)
                    g.set(x, y, a if inner < block - 1 else b)
        add(f"Basketweave b{block}", ["basketweave"], fn)
    # spiral (square)
    for d in (1, -1):
        a, b = pair(n); n += 1
        def fn(g, d=d, a=a, b=b):
            g.fill(b)
            x = y = 0
            dx, dy = (d, 0)
            steps = g.w
            col = a
            x, y = 0, 0
            cx = cy = 0
            # simple concentric-square spiral approximation
            lo, hi = 0, g.w - 1
            toggle = True
            while lo <= hi:
                if toggle:
                    g.frame(lo, lo, hi, hi, a, 1)
                lo += 1; hi -= 1; toggle = not toggle
        add(f"Spiral {d}", ["spiral"], fn)
    # quadrants / corner triangles
    for cfg in range(4):
        cols = TRIOS[n % len(TRIOS)]; n += 1
        def fn(g, cfg=cfg, cols=cols):
            c = g.w / 2
            for y in range(g.h):
                for x in range(g.w):
                    q = (0 if x < c else 1) + (0 if y < c else 2)
                    g.set(x, y, cols[(q + cfg) % len(cols)])
        add(f"Quadrants {cfg}", ["quadrant"], fn)
    # gingham
    for block in (2, 3, 4):
        d, m, l = TRIOS[n % len(TRIOS)]; n += 1
        def fn(g, block=block, d=d, m=m, l=l):
            for y in range(g.h):
                for x in range(g.w):
                    vx = (x // block) % 2 == 0
                    vy = (y // block) % 2 == 0
                    g.set(x, y, d if (vx and vy) else (m if (vx or vy) else l))
        add(f"Gingham b{block}", ["gingham"], fn)
    # diagonal lattice
    for spacing in (3, 4, 5, 6, 7):
        a, b = pair(n); n += 1
        def fn(g, spacing=spacing, a=a, b=b):
            g.fill(b)
            for k in range(-g.h, g.w, spacing):
                for x in range(g.w):
                    g.set(x, x - k, a); g.set(x, k - x + g.h, a)
        add(f"Lattice s{spacing}", ["lattice"], fn)
    # wider stripes 8-11
    for orient in ("vert", "horiz", "diag", "anti"):
        for w in (8, 9, 10):
            a, b = pair(n); n += 1
            def fn(g, orient=orient, w=w, a=a, b=b):
                for y in range(g.h):
                    for x in range(g.w):
                        k = {"vert": x, "horiz": y, "diag": x + y, "anti": x - y + g.h}[orient]
                        g.set(x, y, a if (k // w) % 2 == 0 else b)
            add(f"{orient.title()} Bands w{w}", ["stripe"], fn)
    # concentric polygons
    for sides in (3, 5, 6, 8):
        for t in (2, 3):
            cols = TRIOS[n % len(TRIOS)]; n += 1
            def fn(g, sides=sides, t=t, cols=cols):
                c = (g.w - 1) / 2
                for i in range(g.w // 2, 0, -1):
                    g.poly(reg_polygon(c, c, i, sides, rot=-math.pi / 2), cols[(i // t) % len(cols)])
            add(f"Concentric {sides}-gon t{t}", ["concentric"], fn)
    # polygon grids
    def polygrid(g, spacing, sides, a, b):
        g.fill(b)
        r = spacing * 0.36
        for cy in range(spacing // 2, g.h, spacing):
            for cx in range(spacing // 2, g.w, spacing):
                g.poly(reg_polygon(cx, cy, r + 0.5, sides, rot=-math.pi / 2), a)
    for sides in (5, 6, 8):
        for spacing in (5, 6, 7):
            a, b = pair(n); n += 1
            add(f"{sides}-gon Grid s{spacing}", ["grid"],
                lambda g, spacing=spacing, sides=sides, a=a, b=b: polygrid(g, spacing, sides, a, b))
    # truchet quarter-arc tilings
    for variant in range(6):
        a, b = pair(n); n += 1
        def fn(g, variant=variant, a=a, b=b):
            tile = 7
            g.fill(b)
            for ty in range(0, g.h, tile):
                for tx in range(0, g.w, tile):
                    flip = ((tx // tile + ty // tile + variant) % 2 == 0) if variant < 2 \
                        else ((tx // tile * 3 + ty // tile * 7 + variant) % 2 == 0)
                    cx, cy = (tx, ty) if flip else (tx + tile, ty)
                    for yy in range(tile):
                        for xx in range(tile):
                            if abs(math.hypot(tx + xx - cx, ty + yy - cy) - tile * 0.5) < 1.2:
                                g.set(tx + xx, ty + yy, a)
                    cx2, cy2 = (tx + tile, ty + tile) if flip else (tx, ty + tile)
                    for yy in range(tile):
                        for xx in range(tile):
                            if abs(math.hypot(tx + xx - cx2, ty + yy - cy2) - tile * 0.5) < 1.2:
                                g.set(tx + xx, ty + yy, a)
        add(f"Truchet {variant}", ["truchet"], fn)
    # argyle
    for cfg in range(3):
        a, b, c3 = TRIOS[n % len(TRIOS)]; n += 1
        def fn(g, cfg=cfg, a=a, b=b, c3=c3):
            cell = 8
            g.fill(b)
            for cy in range(0, g.h + cell, cell):
                for cx in range(0, g.w + cell, cell):
                    g.poly(reg_polygon(cx, cy, cell * 0.7, 4, rot=0), a if (cx // cell + cy // cell) % 2 else c3)
            for k in range(-g.h, g.w, cell):
                for x in range(g.w):
                    g.set(x, x - k, c3)
        add(f"Argyle {cfg}", ["argyle"], fn)
    # radial checker (angular x ring)
    for cfg in ((6, 4), (8, 4), (12, 5), (8, 6)):
        sectors, rings = cfg
        a, b = pair(n); n += 1
        def fn(g, sectors=sectors, rings=rings, a=a, b=b):
            c = (g.w - 1) / 2
            for y in range(g.h):
                for x in range(g.w):
                    ang = int((math.atan2(y - c, x - c) + math.pi) / (2 * math.pi) * sectors)
                    rr = int(math.hypot(x - c, y - c) / (g.w / 2) * rings)
                    g.set(x, y, a if (ang + rr) % 2 == 0 else b)
        add(f"Radial Check {sectors}x{rings}", ["radial"], fn)
    # rotated (diagonal) checkerboard
    for block in (2, 3, 4, 5):
        a, b = pair(n); n += 1
        def fn(g, block=block, a=a, b=b):
            for y in range(g.h):
                for x in range(g.w):
                    u = (x + y) // block
                    v = (x - y + g.h) // block
                    g.set(x, y, a if (u + v) % 2 == 0 else b)
        add(f"Diag Checker b{block}", ["checker"], fn)
    # target / dartboard rings with cross
    for count in (5, 7):
        cols = TRIOS[n % len(TRIOS)]; n += 1
        def fn(g, count=count, cols=cols):
            c = (g.w - 1) / 2
            maxr = g.w / 2
            for i in range(count):
                g.ring(c, c, maxr * (count - i) / count, cols[i % len(cols)], maxr / count)
            g.rect(c - 0.5, 0, c + 0.5, g.h - 1, cols[-1]); g.rect(0, c - 0.5, g.w - 1, c + 0.5, cols[-1])
        add(f"Dartboard {count}", ["target"], fn)
    # top-up: more parameter values on reliable families
    for orient in ("vert", "horiz", "diag", "anti"):
        for w in (11, 12, 13):
            a, b = pair(n); n += 1
            def fn(g, orient=orient, w=w, a=a, b=b):
                for y in range(g.h):
                    for x in range(g.w):
                        k = {"vert": x, "horiz": y, "diag": x + y, "anti": x - y + g.h}[orient]
                        g.set(x, y, a if (k // w) % 2 == 0 else b)
            add(f"{orient.title()} Wide w{w}", ["stripe"], fn)
    for period in (8, 9, 10):
        cols = TRIOS[n % len(TRIOS)]; n += 1
        def fn(g, period=period, cols=cols):
            for y in range(g.h):
                for x in range(g.w):
                    z = abs(((x + y) % (2 * period)) - period)
                    g.set(x, y, cols[(z + y // period) % len(cols)])
        add(f"Wide Chevron p{period}", ["chevron"], fn)
    for rays in (5, 7, 9, 14, 18, 32):
        a, b = pair(n); n += 1
        def fn(g, rays=rays, a=a, b=b):
            c = (g.w - 1) / 2
            g.fill(b)
            for y in range(g.h):
                for x in range(g.w):
                    ang = math.atan2(y - c, x - c)
                    if int((ang + math.pi) / (2 * math.pi) * rays) % 2 == 0:
                        g.set(x, y, a)
        add(f"Ray Burst {rays}", ["sunburst"], fn)
    for shape in ("dot", "ring", "diamond", "star"):
        for spacing in (8, 9):
            a, b = pair(n); n += 1
            def fn(g, spacing=spacing, shape=shape, a=a, b=b):
                g.fill(b)
                r = spacing * 0.34
                for cy in range(spacing // 2, g.h, spacing):
                    for cx in range(spacing // 2, g.w, spacing):
                        if shape == "dot":
                            g.disc(cx, cy, r, a)
                        elif shape == "ring":
                            g.ring(cx, cy, r, a, 1)
                        elif shape == "diamond":
                            g.poly(reg_polygon(cx, cy, r + 0.5, 4, rot=0), a)
                        else:
                            g.poly(star_points(cx, cy, r + 1, (r + 1) * 0.45, 5), a)
            add(f"{shape.title()} Field s{spacing}", ["grid"], fn)
    for block in (8, 9, 10):
        a, b = pair(n); n += 1
        add(f"Big Checker {block}", ["checker"],
            lambda g, block=block, a=a, b=b: [g.set(x, y, a if ((x // block) + (y // block)) % 2 == 0 else b)
                                              for y in range(g.h) for x in range(g.w)])
    return gens


def geometric():
    return _emit("geometric", _geo_configs(), 200)


# ── MANDALAS ─────────────────────────────────────────────────────────────────

MPAL = [["red", "orange", "yellow", "green", "blue", "purple"],
        ["navy", "sky_blue", "white", "hot_pink"], ["purple", "magenta", "lemon", "aqua"],
        ["teal", "orange", "hot_pink", "yellow"], ["forest", "light_green", "banana", "red"],
        ["dark_purple", "lavender", "aqua", "white"], ["dark_red", "orange", "banana", "cream"],
        ["blue", "aqua", "white", "hot_pink"], ["magenta", "purple", "sky_blue", "lemon"]]
RING_SHAPES = ["dot", "petal", "spoke", "ring", "tri", "square", "star", "scallop"]


def _mandala(sym, seq, s, pal):
    g = Grid(s, s)
    c = (s - 1) / 2.0
    maxr = s / 2.0 - 1
    rings = len(seq)
    for ri, shape in enumerate(seq):
        rr = maxr * (ri + 1) / (rings + 0.4)
        col = pal[ri % len(pal)]
        count = sym * (2 if ri % 2 else 1)
        if shape == "ring":
            g.ring(c, c, rr, col, max(1.0, s * 0.045))
        elif shape == "spoke":
            for k in range(sym):
                a = 2 * math.pi * k / sym
                g.line(c, c, c + rr * math.cos(a), c + rr * math.sin(a), col)
        else:
            for k in range(count):
                a = 2 * math.pi * k / count + (0 if ri % 2 else math.pi / count)
                px, py = c + rr * math.cos(a), c + rr * math.sin(a)
                rad = max(1.0, maxr * 0.13)
                if shape == "dot":
                    g.disc(px, py, rad, col)
                elif shape == "petal":
                    g.ellipse(px, py, rad * 1.2, rad * 0.6, col)
                elif shape == "tri":
                    g.poly(reg_polygon(px, py, rad + 0.5, 3, rot=a - math.pi / 2), col)
                elif shape == "square":
                    g.poly(reg_polygon(px, py, rad + 0.3, 4, rot=a), col)
                elif shape == "star":
                    g.poly(star_points(px, py, rad + 1, (rad + 1) * 0.45, 5, rot=a), col)
                elif shape == "scallop":
                    g.disc(px, py, rad * 0.9, col)
    g.disc(c, c, max(1.6, s * 0.08), pal[1 % len(pal)])
    g.disc(c, c, max(1.0, s * 0.04), pal[2 % len(pal)])
    g.ring(c, c, maxr, pal[-1], 1.1)
    return g


def mandalas():
    gens = []
    base = len(RING_SHAPES)
    syms = (6, 8, 10, 12, 5, 16)
    # interleave symmetry; a rising `code` gives a fresh ring-shape sequence
    for i in range(2400):
        sym = syms[i % len(syms)]
        nrings = 3 + (i // len(syms)) % 3
        code = i // (len(syms) * 3)                      # new sequence every 18
        seq = [RING_SHAPES[(code // (base ** k)) % base] for k in range(nrings)]
        s = (24, 28, 30)[i % 3]
        pal = MPAL[i % len(MPAL)]
        gens.append((f"Mandala {sym}-fold {i+1}", _mandala(sym, seq, s, pal),
                     ["mandala", f"{sym}fold"]))
    return _emit("mandalas", gens, 200)


# ── SNOWFLAKES ───────────────────────────────────────────────────────────────

SPAL = ["white", "sky_blue", "toothpaste", "aqua", "light_blue", "periwinkle", "turquoise"]
SBG = ["navy", "dark_blue", "blue", "dark_purple", "teal"]


def _hexplate(g, cx, cy, r, col):
    g.poly(reg_polygon(cx, cy, r, 6, rot=0), col)


def _snowflake(spec, s, col, bg):
    """One ornate 6-fold ice crystal. All six arms are the same motif rotated,
    so symmetry is exact; richness comes from dendritic side-branches (that
    themselves fork), hexagonal plates, and varied tips."""
    g = Grid(s, s)
    g.fill(bg)
    c = (s - 1) / 2.0
    maxr = s / 2.0 - 1.5
    positions, blen, bang, sub, plates, tip, center = spec
    for k in range(6):
        a = -math.pi / 2 + k * math.pi / 3
        dx, dy = math.cos(a), math.sin(a)
        ex, ey = c + maxr * dx, c + maxr * dy
        g.line(c, c, ex, ey, col)                       # main spine
        for frac in positions:
            bx, by = c + maxr * frac * dx, c + maxr * frac * dy
            bl = maxr * blen * (1.0 - 0.35 * frac)      # branches shrink outward
            for sgn in (-1, 1):
                ba = a + sgn * bang
                bex, bey = bx + bl * math.cos(ba), by + bl * math.sin(ba)
                g.line(bx, by, bex, bey, col)           # side branch
                if sub:                                  # fork it → fern look
                    mx, my = bx + 0.6 * (bex - bx), by + 0.6 * (bey - by)
                    for sgn2 in (-1, 1):
                        sba = ba + sgn2 * bang * 0.85
                        g.line(mx, my, mx + bl * 0.5 * math.cos(sba),
                               my + bl * 0.5 * math.sin(sba), col)
        for frac in plates:
            _hexplate(g, c + maxr * frac * dx, c + maxr * frac * dy, max(1.4, s * 0.05), col)
        if tip == "dot":
            g.disc(ex, ey, max(1.3, s * 0.055), col)
        elif tip == "plate":
            _hexplate(g, ex, ey, max(1.7, s * 0.07), col)
        elif tip == "fern":
            for sgn in (-1, 1):
                ba = a + sgn * math.pi / 4
                g.line(ex, ey, ex + maxr * 0.16 * math.cos(ba), ey + maxr * 0.16 * math.sin(ba), col)
        elif tip == "split":
            bx, by = c + maxr * 0.86 * dx, c + maxr * 0.86 * dy
            for sgn in (-1, 1):
                ba = a + sgn * math.pi / 7
                g.line(bx, by, bx + maxr * 0.16 * math.cos(ba), by + maxr * 0.16 * math.sin(ba), col)
    if center == "hex":
        _hexplate(g, c, c, max(2.2, s * 0.11), col)
        _hexplate(g, c, c, max(1.2, s * 0.055), bg)
    elif center == "star":
        g.poly(star_points(c, c, s * 0.13, s * 0.06, 6), col)
    else:
        g.disc(c, c, max(1.8, s * 0.09), col)
    return g


def snowflakes():
    gens = []
    # richer, denser branch position sets first so the set skews ornate
    posn = [[0.3, 0.45, 0.6, 0.75, 0.9], [0.35, 0.55, 0.72, 0.88],
            [0.3, 0.5, 0.7, 0.85], [0.4, 0.6, 0.78, 0.92], [0.32, 0.52, 0.72, 0.9],
            [0.45, 0.65, 0.85], [0.35, 0.6, 0.82], [0.3, 0.55, 0.75, 0.9]]
    angs = [math.pi / 3, math.pi / 4, math.pi / 2.5, math.pi / 5]
    lens = [0.28, 0.34, 0.22, 0.4]
    plate_sets = [[], [0.55], [0.5, 0.85], [0.4, 0.7], [0.6, 0.9]]
    tips = ["fern", "plate", "split", "dot"]
    centers = ["hex", "star", "dot"]
    i = 0
    for sub in (True, False):
        for pos in posn:
            for tip in tips:
                for center in centers:
                    for pl in plate_sets:
                        for ang in angs:
                            for ln in lens:
                                s = (27, 29, 32)[i % 3]
                                col = SPAL[i % len(SPAL)]
                                bg = SBG[i % len(SBG)]
                                spec = (pos, ln, ang, sub, pl, tip, center)
                                gens.append((f"Snowflake {i+1}", _snowflake(spec, s, col, bg),
                                             ["snowflake", "crystal", "6fold"]))
                                i += 1
    return _emit("snowflakes", gens, 200)


# ── HEARTS ───────────────────────────────────────────────────────────────────

def _heart_cells(s, size, cx=None, cy=None):
    cx = (s - 1) / 2 if cx is None else cx
    cy = (s - 1) / 2 - 1 if cy is None else cy
    m = Grid(s, s)
    m.poly(heart_points(cx, cy, size), "X")
    return {(x, y) for x, y, _ in m.cells()}


def hearts():
    S = 27
    mask = _heart_cells(S, S * 0.94)
    xs = [x for x, _ in mask]; ys = [y for _, y in mask]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W = x1 - x0 + 1; H = y1 - y0 + 1
    gens = []

    def build(title, fn, tags):
        g = Grid(S, S)
        for (x, y) in mask:
            c = fn(x - x0, y - y0)
            if c:
                g.set(x, y, c)
        gens.append((title, g, ["heart"] + tags))

    def col2(a=("red", "white")):
        return a
    A, B = "red", "white"
    # solid
    build("Solid Heart", lambda x, y: A, ["solid"])
    # stripes h/v/diag/anti x widths
    for w in range(1, 7):
        build(f"H-Stripe Heart w{w}", lambda x, y, w=w: (A, B)[(y // w) % 2], ["stripe"])
        build(f"V-Stripe Heart w{w}", lambda x, y, w=w: (A, B)[(x // w) % 2], ["stripe"])
        build(f"Diag Heart w{w}", lambda x, y, w=w: (A, B)[((x + y) // w) % 2], ["stripe"])
        build(f"Anti Heart w{w}", lambda x, y, w=w: (A, B)[((x - y + H) // w) % 2], ["stripe"])
    # checker / diag-checker
    for b in range(1, 7):
        build(f"Checker Heart b{b}", lambda x, y, b=b: (A, B)[((x // b) + (y // b)) % 2], ["checker"])
    for b in range(2, 6):
        build(f"Diag Checker Heart b{b}", lambda x, y, b=b: (A, B)[(((x + y) // b) + ((x - y + H) // b)) % 2], ["checker"])
    # dot grids inside
    for sp in range(2, 6):
        build(f"Dot Heart s{sp}", lambda x, y, sp=sp: B if (x % sp == sp // 2 and y % sp == sp // 2) else A, ["dots"])
    # concentric heart rings
    for n in range(2, 8):
        rings = [_heart_cells(S, S * 0.94 * (1 - i / (n + 0.5))) for i in range(n)]

        def fn(x, y, rings=rings):
            ax, ay = x + x0, y + y0
            for i, r in enumerate(rings):
                if (ax, ay) in r:
                    return ("red", "hot_pink", "white")[i % 3]
            return "red"
        build(f"Concentric Heart n{n}", fn, ["concentric"])
    # outline thickness
    for t in range(1, 5):
        inner = _heart_cells(S, S * 0.94 * (1 - 0.14 * t))
        build(f"Outline Heart t{t}", lambda x, y, inner=inner: B if (x + x0, y + y0) in inner else A, ["outline"])
    # bordered (2-color frame + solid)
    for t in range(1, 4):
        inner = _heart_cells(S, S * 0.94 * (1 - 0.16 * t))
        build(f"Bordered Heart t{t}", lambda x, y, inner=inner: A if (x + x0, y + y0) in inner else B, ["border"])
    # half splits
    for d in ("v", "h", "d", "a"):
        build(f"Split Heart {d}", lambda x, y, d=d: A if {"v": x < W / 2, "h": y < H / 2, "d": x + y < (W + H) / 2, "a": x - y < 0}[d] else B, ["split"])
    # chevron / zigzag / waves fills
    for p in range(2, 7):
        build(f"Chevron Heart p{p}", lambda x, y, p=p: (A, B)[(abs(((x + y) % (2 * p)) - p)) % 2], ["chevron"])
    for p in range(3, 7):
        build(f"Wave Heart p{p}", lambda x, y, p=p: (A, B)[int((y + 2 * math.sin(x * 2 * math.pi / p)) // 2) % 2], ["wave"])
    # cross / plus inside
    for w in range(1, 4):
        build(f"Cross Heart w{w}", lambda x, y, w=w: B if abs(x - W / 2) <= w or abs(y - H / 2) <= w else A, ["cross"])
        build(f"X Heart w{w}", lambda x, y, w=w: B if abs(x - y) <= w or abs(x + y - H) <= w else A, ["cross"])
    # inner icon
    def inner_icon(shape):
        cx, cy = (S - 1) / 2, (S - 1) / 2
        ig = Grid(S, S)
        if shape == "heart":
            ig.poly(heart_points(cx, cy - 1, S * 0.45), "I")
        elif shape == "star":
            ig.poly(star_points(cx, cy, S * 0.22, S * 0.1, 5), "I")
        elif shape == "circle":
            ig.disc(cx, cy, S * 0.2, "I")
        elif shape == "diamond":
            ig.poly(reg_polygon(cx, cy, S * 0.24, 4, rot=0), "I")
        elif shape == "ring":
            ig.ring(cx, cy, S * 0.22, "I", 2)
        elif shape == "plus":
            ig.rect(cx - 2, cy - S * 0.22, cx + 2, cy + S * 0.22, "I"); ig.rect(cx - S * 0.22, cy - 2, cx + S * 0.22, cy + 2, "I")
        return {(x, y) for x, y, _ in ig.cells()}
    for shape in ("heart", "star", "circle", "diamond", "ring", "plus"):
        ic = inner_icon(shape)
        build(f"Heart with {shape}", lambda x, y, ic=ic: B if (x + x0, y + y0) in ic else A, ["inner", shape])
    # gradient bands (multi-band by width) - structural via band count
    ramp = ["dark_red", "red", "hot_pink", "magenta", "pink", "light_pink"]
    for nb in range(2, 7):
        build(f"Ombre Heart n{nb}", lambda x, y, nb=nb: ramp[min(int(y / (H / nb)), len(ramp) - 1)], ["ombre"])
        build(f"Ombre V Heart n{nb}", lambda x, y, nb=nb: ramp[min(int(x / (W / nb)), len(ramp) - 1)], ["ombre"])
    # mini-heart tessellation inside (density)
    for step in (5, 6, 7, 8):
        minis = set()
        for hy in range(y0 + 2, y1, step):
            for hx in range(x0 + 2, x1, step):
                minis |= _heart_cells(S, step * 0.9, hx, hy)
        build(f"Mini-Heart Heart s{step}", lambda x, y, minis=minis: B if (x + x0, y + y0) in minis else A, ["tessellation"])
    # lattice / diagonal grid inside
    for sp in range(3, 7):
        build(f"Lattice Heart s{sp}", lambda x, y, sp=sp: B if (x % sp == 0 or (x + y) % sp == 0) else A, ["lattice"])
    # crosshatch inside
    for sp in range(2, 6):
        build(f"Crosshatch Heart s{sp}", lambda x, y, sp=sp: B if ((x + y) % sp == 0 or (x - y + H) % sp == 0) else A, ["crosshatch"])
    # polka on two-tone
    for sp in (3, 4, 5):
        build(f"Polka Heart s{sp}", lambda x, y, sp=sp: A if ((x % sp) - sp // 2) ** 2 + ((y % sp) - sp // 2) ** 2 <= 1 else B, ["polka"])
    # concentric shape inside (square/diamond/circle rings from center)
    cxr, cyr = W / 2, H / 2
    for shape in ("square", "diamond", "circle"):
        for t in (2, 3):
            def fn(x, y, shape=shape, t=t):
                if shape == "square":
                    d = max(abs(x - cxr), abs(y - cyr))
                elif shape == "diamond":
                    d = abs(x - cxr) + abs(y - cyr)
                else:
                    d = math.hypot(x - cxr, y - cyr)
                return (A, B)[int(d // t) % 2]
            build(f"{shape.title()}-Ring Heart t{t}", fn, ["concentric"])
    # monogram hearts: a letter or digit inside (from the 5x7 font)
    from gen_icons import FONT
    cxg, cyg = (S - 1) / 2, (S - 1) / 2 - 2

    def glyph_cells(rows, scale=2):
        gw, gh = 5 * scale, 7 * scale
        ox, oy = int(cxg - gw / 2), int(cyg - gh / 2)
        cells = set()
        for r, row in enumerate(rows):
            for cc, ch in enumerate(row):
                if ch == "#":
                    for dy in range(scale):
                        for dx in range(scale):
                            cells.add((ox + cc * scale + dx, oy + r * scale + dy))
        return cells
    for ch, rows in FONT.items():
        gc = glyph_cells(rows)
        build(f"Monogram Heart {ch}", lambda x, y, gc=gc: B if (x + x0, y + y0) in gc else A, ["monogram", ch.lower()])
    # arrangements: use whole board, not the mask
    def build_full(title, drawer, tags):
        g = Grid(S, S)
        drawer(g)
        gens.append((title, g, ["heart"] + tags))
    for i, (px, py, sz) in enumerate([(0.32, 0.44, 0.5), (0.5, 0.5, 0.55)]):
        pass
    # double / triple / row / winged / arrow
    build_full("Two Hearts", lambda g: (g.poly(heart_points(S * 0.34, S * 0.42, S * 0.5), "red"),
                                        g.poly(heart_points(S * 0.66, S * 0.56, S * 0.5), "hot_pink")), ["pair"])
    build_full("Three Hearts", lambda g: [g.poly(heart_points(S * fx, S * fy, S * 0.4), c)
                                          for fx, fy, c in [(0.3, 0.4, "red"), (0.7, 0.4, "hot_pink"), (0.5, 0.66, "magenta")]], ["triple"])
    build_full("Heart Trio Row", lambda g: [g.poly(heart_points(S * fx, S * 0.5, S * 0.34), "red") for fx in (0.25, 0.5, 0.75)], ["row"])
    def winged(g):
        g.poly(heart_points(S * 0.5, S * 0.48, S * 0.5), "red")
        for sgn in (-1, 1):
            for k in range(3):
                g.ellipse(S * 0.5 + sgn * S * (0.22 + k * 0.07), S * 0.45, S * 0.05, S * 0.09, "white")
    build_full("Winged Heart", winged, ["winged"])
    def arrowed(g):
        g.poly(heart_points(S * 0.5, S * 0.48, S * 0.56), "red")
        g.line(S * 0.1, S * 0.62, S * 0.9, S * 0.36, "dark_brown")
        g.poly([(S * 0.9, S * 0.36), (S * 0.78, S * 0.34), (S * 0.8, S * 0.44)], "dark_gray")
        g.poly([(S * 0.12, S * 0.6), (S * 0.2, S * 0.55), (S * 0.2, S * 0.66)], "dark_gray")
    build_full("Cupid Heart", arrowed, ["arrow"])
    def banner(g):
        g.poly(heart_points(S * 0.5, S * 0.42, S * 0.6), "red")
        g.rect(S * 0.15, S * 0.6, S * 0.85, S * 0.72, "cream")
        g.poly([(S * 0.15, S * 0.6), (S * 0.05, S * 0.66), (S * 0.15, S * 0.72)], "cream")
        g.poly([(S * 0.85, S * 0.6), (S * 0.95, S * 0.66), (S * 0.85, S * 0.72)], "cream")
    build_full("Banner Heart", banner, ["banner"])
    return _emit("hearts", gens, 200)


# ── STARS ────────────────────────────────────────────────────────────────────

SHUES = ["yellow", "orange", "cheddar", "hot_pink", "aqua", "red", "sky_blue",
         "lavender", "neon_green", "magenta", "banana", "turquoise", "purple", "blue"]


def stars():
    S = 27
    c = (S - 1) / 2
    gens = []

    def add(title, g, tags):
        gens.append((title, g, ["star"] + tags))

    hi = 0

    def hue():
        nonlocal hi
        hi += 1
        return SHUES[hi % len(SHUES)]

    # solid n-point stars: point count x inner-ratio x size
    for n in (4, 5, 6, 7, 8, 9, 10, 12):
        for ratio in (0.38, 0.46, 0.55):
            for size in (0.4, 0.47):
                g = Grid(S, S)
                g.poly(star_points(c, c, S * size, S * size * ratio, n), hue())
                add(f"{n}-Point r{ratio} z{size}", g, [f"{n}point"])
    # nested two-tone
    for n in (5, 6, 8):
        for ratio in (0.4, 0.5):
            g = Grid(S, S)
            g.poly(star_points(c, c, S * 0.46, S * 0.46 * ratio, n), hue())
            g.poly(star_points(c, c, S * 0.28, S * 0.28 * ratio, n), hue())
            add(f"Nested {n}pt r{ratio}", g, ["nested"])
    # concentric star rings (3 nested outlines)
    for n in (5, 6, 8):
        g = Grid(S, S)
        for rr in (0.46, 0.34, 0.22):
            g.poly_outline(star_points(c, c, S * rr, S * rr * 0.45, n), hue(), t=0)
        add(f"Ring Star {n}pt", g, ["rings"])
    # star polygons / n-grams (connect every k-th vertex)
    for n, k in [(5, 2), (6, 2), (7, 2), (7, 3), (8, 3), (9, 2), (9, 4), (10, 3), (12, 5), (8, 2), (10, 4), (11, 3), (11, 4)]:
        g = Grid(S, S)
        verts = reg_polygon(c, c, S * 0.46, n, rot=-math.pi / 2)
        col = hue()
        for i in range(n):
            a = verts[i]; b = verts[(i + k) % n]
            g.line(a[0], a[1], b[0], b[1], col)
        add(f"{n}/{k} Star Polygon", g, ["polygon", "ngram"])
    # starbursts
    for rays in (8, 10, 12, 14, 16, 18, 20, 24, 28, 32):
        g = Grid(S, S)
        col = hue()
        for kk in range(rays):
            a = 2 * math.pi * kk / rays
            rr = S * 0.46 if kk % 2 == 0 else S * 0.28
            g.line(c, c, c + rr * math.cos(a), c + rr * math.sin(a), col)
        g.disc(c, c, S * 0.09, col)
        add(f"Starburst {rays}", g, ["burst"])
    # sparkles (4-point) varied
    for w in (0.14, 0.2, 0.28):
        for r in (0.4, 0.48):
            g = Grid(S, S)
            col = hue()
            for kk in range(4):
                a = math.pi / 2 * kk
                g.poly([(c + S * w * math.cos(a + math.pi / 4), c + S * w * math.sin(a + math.pi / 4)),
                        (c + S * r * math.cos(a), c + S * r * math.sin(a)),
                        (c + S * w * math.cos(a - math.pi / 4), c + S * w * math.sin(a - math.pi / 4)),
                        (c, c)], col)
            add(f"Sparkle w{w} r{r}", g, ["sparkle"])
    # ring of stars around a center star
    for m in (5, 6, 7, 8, 10, 12):
        g = Grid(S, S)
        rc, cc2 = hue(), hue()
        for kk in range(m):
            a = 2 * math.pi * kk / m - math.pi / 2
            g.poly(star_points(c + S * 0.34 * math.cos(a), c + S * 0.34 * math.sin(a), S * 0.09, S * 0.04, 5), rc)
        g.poly(star_points(c, c, S * 0.18, S * 0.08, 5), cc2)
        add(f"Star Wreath {m}", g, ["wreath"])
    # star grids / tessellation
    for sp in (5, 6, 7, 8):
        g = Grid(S, S)
        col = hue()
        for cy in range(sp // 2, S, sp):
            for cx in range(sp // 2, S, sp):
                g.poly(star_points(cx, cy, sp * 0.42, sp * 0.42 * 0.45, 5), col)
        add(f"Star Grid s{sp}", g, ["grid"])
    # internal-pattern stars: fill a big 5/6-point star mask with a pattern
    for n in (5, 6):
        smask = {(x, y) for x, y, _ in
                 [(cx, cy, "M") for cx in range(S) for cy in range(S)]
                 if False}
        mg = Grid(S, S)
        mg.poly(star_points(c, c, S * 0.48, S * 0.48 * 0.45, n), "M")
        smask = {(x, y) for x, y, _ in mg.cells()}
        xs = [x for x, _ in smask]; ys = [y for _, y in smask]
        mx0, my0 = min(xs), min(ys)
        A, Bc = hue(), "white"
        fills = [("H", lambda x, y, w: (A, Bc)[(y // w) % 2]),
                 ("V", lambda x, y, w: (A, Bc)[(x // w) % 2]),
                 ("Diag", lambda x, y, w: (A, Bc)[((x + y) // w) % 2]),
                 ("Check", lambda x, y, w: (A, Bc)[((x // w) + (y // w)) % 2]),
                 ("Ring", lambda x, y, w: (A, Bc)[int(math.hypot(x - (c - mx0), y - (c - my0)) // w) % 2]),
                 ("Dot", lambda x, y, w: Bc if (x % w == w // 2 and y % w == w // 2) else A)]
        for fname, ffn in fills:
            for w in (2, 3):
                g = Grid(S, S)
                for (x, y) in smask:
                    g.set(x, y, ffn(x - mx0, y - my0, w))
                add(f"{n}pt {fname} Star w{w}", g, ["pattern"])
    return _emit("stars", gens, 200)


# ── GEMS ─────────────────────────────────────────────────────────────────────

GHUES = ["red", "hot_pink", "magenta", "purple", "dark_blue", "blue", "aqua",
         "teal", "green", "orange", "yellow", "turquoise", "sky_blue"]
GLIGHT = {"red": "blush", "hot_pink": "light_pink", "magenta": "light_pink",
          "purple": "light_lavender", "dark_blue": "sky_blue", "blue": "light_blue",
          "aqua": "toothpaste", "teal": "light_teal", "green": "light_green",
          "orange": "peach", "yellow": "lemon", "turquoise": "toothpaste",
          "sky_blue": "white"}


def _cut_points(cut, cx, cy, s):
    if cut == "round":
        return reg_polygon(cx, cy, s * 0.42, 12, rot=0)
    if cut == "oval":
        return [(cx + s * 0.26 * math.cos(a), cy + s * 0.42 * math.sin(a)) for a in
                [2 * math.pi * k / 16 for k in range(16)]]
    if cut == "marquise":
        return [(cx, cy - s * 0.44), (cx + s * 0.2, cy), (cx, cy + s * 0.44), (cx - s * 0.2, cy)]
    if cut == "pear":
        return [(cx, cy - s * 0.42), (cx + s * 0.26, cy + s * 0.1), (cx, cy + s * 0.42), (cx - s * 0.26, cy + s * 0.1)]
    if cut == "emerald":
        return [(cx - s * 0.26, cy - s * 0.34), (cx + s * 0.26, cy - s * 0.34),
                (cx + s * 0.32, cy - s * 0.24), (cx + s * 0.32, cy + s * 0.24),
                (cx + s * 0.26, cy + s * 0.34), (cx - s * 0.26, cy + s * 0.34),
                (cx - s * 0.32, cy + s * 0.24), (cx - s * 0.32, cy - s * 0.24)]
    if cut == "princess":
        return reg_polygon(cx, cy, s * 0.44, 4, rot=0)
    if cut == "heart":
        return heart_points(cx, cy - 1, s * 0.9)
    if cut == "trillion":
        return reg_polygon(cx, cy + s * 0.05, s * 0.44, 3, rot=-math.pi / 2)
    if cut == "cushion":
        return reg_polygon(cx, cy, s * 0.4, 8, rot=math.pi / 8)
    if cut == "kite":
        return [(cx, cy - s * 0.44), (cx + s * 0.28, cy), (cx, cy + s * 0.3), (cx - s * 0.28, cy)]
    if cut == "hexagon":
        return reg_polygon(cx, cy, s * 0.42, 6, rot=0)
    if cut == "baguette":
        return [(cx - s * 0.16, cy - s * 0.44), (cx + s * 0.16, cy - s * 0.44),
                (cx + s * 0.16, cy + s * 0.44), (cx - s * 0.16, cy + s * 0.44)]
    return reg_polygon(cx, cy, s * 0.42, 6, rot=0)


def gems():
    S = 24
    c = (S - 1) / 2
    cuts = ["round", "oval", "marquise", "pear", "emerald", "princess", "heart",
            "trillion", "cushion", "kite", "hexagon", "baguette"]
    gens = []
    hi = 0

    def hue():
        nonlocal hi
        hi += 1
        return GHUES[hi % len(GHUES)]

    def spark(g, x, y):
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
            g.set(int(x + dx), int(y + dy), "white")

    # each cut with several facet styles
    for cut in cuts:
        for facet in ("crown", "star", "cross", "radial", "table", "plain"):
            col = hue(); lt = GLIGHT.get(col, "white")
            g = Grid(S, S)
            pts = _cut_points(cut, c, c, S)
            g.poly(pts, col)
            if facet == "crown":
                g.poly(_cut_points(cut, c, c - S * 0.06, S * 0.55), lt)
            elif facet == "star":
                for k in range(8):
                    a = 2 * math.pi * k / 8
                    g.line(c, c, c + S * 0.4 * math.cos(a), c + S * 0.42 * math.sin(a), "white" if k % 2 else lt)
            elif facet == "cross":
                g.line(c - S * 0.4, c, c + S * 0.4, c, "white"); g.line(c, c - S * 0.42, c, c + S * 0.42, "white")
            elif facet == "radial":
                for k in range(6):
                    a = 2 * math.pi * k / 6
                    g.line(c, c, c + S * 0.38 * math.cos(a), c + S * 0.4 * math.sin(a), lt)
            elif facet == "table":
                g.poly(reg_polygon(c, c, S * 0.18, 6, rot=0), lt)
            spark(g, c - S * 0.14, c - S * 0.16)
            gens.append((f"{cut.title()} {facet}", g, ["gem", cut, facet]))
    # gem clusters (3, 5, 7 small gems)
    for m in (3, 5, 7):
        for cut in ("round", "princess", "marquise", "pear"):
            g = Grid(S, S)
            g.poly(_cut_points(cut, c, c, S * 0.5), hue())
            for k in range(m):
                a = 2 * math.pi * k / m - math.pi / 2
                col = hue()
                g.poly(_cut_points(cut, c + S * 0.3 * math.cos(a), c + S * 0.3 * math.sin(a), S * 0.34), col)
            gens.append((f"{cut.title()} Cluster {m}", g, ["gem", "cluster"]))
    # gem ring (gem on a band)
    for cut in ("round", "princess", "heart", "marquise", "oval", "pear"):
        g = Grid(S, S)
        g.ring(c, c + S * 0.12, S * 0.34, "cheddar", 2)
        g.poly(_cut_points(cut, c, c - S * 0.12, S * 0.55), hue())
        spark(g, c - 2, c - S * 0.2)
        gens.append((f"{cut.title()} Ring", g, ["gem", "ring"]))
    # pendant (gem + bail + chain)
    for cut in ("round", "heart", "pear", "oval", "marquise", "emerald"):
        g = Grid(S, S)
        for x in range(int(c - 6), int(c + 6)):
            g.set(x, int(c - S * 0.42 + abs(x - c) * 0.2), "cheddar")
        g.ring(c, c - S * 0.32, S * 0.06, "cheddar", 1)
        g.poly(_cut_points(cut, c, c + S * 0.06, S * 0.75), hue())
        gens.append((f"{cut.title()} Pendant", g, ["gem", "pendant"]))
    # gem grid
    for sp in (6, 8):
        for cut in ("round", "princess", "marquise"):
            g = Grid(S, S)
            col = hue()
            for cy in range(sp // 2, S, sp):
                for cx in range(sp // 2, S, sp):
                    g.poly(_cut_points(cut, cx, cy, sp * 0.9), col)
            gens.append((f"{cut.title()} Grid s{sp}", g, ["gem", "grid"]))
    # patterned-fill gems (fill a big round/princess with a pattern)
    for cut in ("round", "princess", "cushion", "hexagon"):
        mg = Grid(S, S); mg.poly(_cut_points(cut, c, c, S), "M")
        gm = {(x, y) for x, y, _ in mg.cells()}
        xs = [x for x, _ in gm]; ys = [y for _, y in gm]
        mx0, my0 = min(xs), min(ys)
        A = hue(); Bc = "white"
        for fname, ffn in [("Stripe", lambda x, y, w: (A, Bc)[(y // w) % 2]),
                           ("Check", lambda x, y, w: (A, Bc)[((x // w) + (y // w)) % 2]),
                           ("Ring", lambda x, y, w: (A, Bc)[int(math.hypot(x - (c - mx0), y - (c - my0)) // w) % 2])]:
            for w in (2, 3):
                g = Grid(S, S)
                for (x, y) in gm:
                    g.set(x, y, ffn(x - mx0, y - my0, w))
                gens.append((f"{cut.title()} {fname} w{w}", g, ["gem", "pattern"]))
    return _emit("gems", gens, 200)


GENERATORS = {
    "geometric": geometric,
    "mandalas": mandalas,
    "snowflakes": snowflakes,
    "hearts": hearts,
    "stars": stars,
    "gems": gems,
}
