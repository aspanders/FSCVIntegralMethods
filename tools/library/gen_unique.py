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


GENERATORS = {
    "geometric": geometric,
}
