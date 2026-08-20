"""Structurally-unique generators for the silhouette categories.

The categories these replace were the library's worst: birds shipped 100
patterns built from SIX distinct shapes, fish from eight. Everything else was
the same silhouette in another colour, so a category read as one picture
repeated down the screen.

The fix is not more hand-drawn icons; it is drawing each subject from parts
whose PROPORTIONS carry the identity. A heron and a wren are the same handful
of primitives with a long neck and long legs versus a round body and a cocked
tail, so a spec of a dozen numbers spans real species rather than palette
swaps. Colour is chosen per design too, but it is never what makes two designs
different - uniqueness.signature is colour-blind and _emit drops collisions.
"""
import math

from beadlib import PALETTE, make_pattern, rgb_to_lab, hex_to_rgb, stable_id
from canvas import Grid
from uniqueness import cell_map, signature

NEAR_DUP = 0.95   # two boards sharing more than this are indistinguishable

S = 28          # board side for every design here


# ── helpers ──────────────────────────────────────────────────────────────────

def _emit(cat, specs, build, target=100, near=NEAR_DUP):
    """Build each spec, drop structural duplicates, keep `target`.

    Callers must generate specs POSE-major (every species at pose 0, then
    every species at pose 1, ...). Species-major order plus this cap silently
    drops the tail of the species list: vehicles lost every boat, plane and
    rocket that way, and the category still reported 100 unique patterns.

    [near] is the lookalike threshold. Raise it for categories defined by
    COMPLETENESS rather than novelty - an alphabet missing N, R and T because
    they resemble M, P and I is worse than one that contains all three.
    """
    import numpy as np
    out, seen = [], set()
    kept_by_size = {}
    for i, spec in enumerate(specs):
        g = build(spec)
        pat = make_pattern(stable_id(cat, f"{spec['name']}-{i}"), spec["name"], cat,
                           g.w, g.h, g.cells(), spec.get("tags", []) + [cat])
        sig = signature(pat)
        if sig in seen:
            continue
        # Visual distinctness, not just an exact match: a variant the drawing
        # ignores produces a board differing by a couple of beads, which
        # signature() happily calls unique.
        v = cell_map(pat)
        stack = kept_by_size.get((g.w, g.h))
        if stack and (np.stack(stack) == v).mean(axis=1).max() >= near:
            continue
        kept_by_size.setdefault((g.w, g.h), []).append(v)
        seen.add(sig)
        out.append(pat)
        if len(out) >= target:
            break
    return out


BIG = 60          # working canvas; the subject is auto-framed down onto S x S


def _frame(draw, spec, bg, size=S, margin=1, fill=None):
    """Draw on a roomy canvas, then centre the ink on the real board.

    Composing a subject from parts makes its extent hard to predict - a heron
    with a long neck and long legs is twice the height of a wren - so the first
    version of this clipped tails and beaks off the edge and left the subject
    sitting wherever the maths happened to put it. Drawing big and framing
    afterwards means every design is centred and whole, and a subject too large
    for the board is redrawn smaller rather than cropped.

    [fill] is the fraction of the board the subject should occupy, and it is
    NOT optional decoration. Auto-fitting to the board silently cancels any
    scale a caller applies to its own spec: "Grapes" and "Grapes Large" both
    ended up filling the board and came out 99.9% identical, and the same went
    for every Small/Large variant in every category - about two of every five
    patterns were a lookalike of another. Scale has to be expressed here, where
    the fitting happens, or not at all.
    """
    # Search DOWN from oversized, and take the largest scale that still fits.
    # Only shrinking left small subjects (a mouse, a sapling) marooned in the
    # middle of a big board at a size where nothing is identifiable; filling the
    # board is most of what makes a 28x28 icon readable.
    want = (size - 2 * margin) * (fill if fill else spec.get("fill", 1.0))
    for attempt in range(20):
        scale = 1.7 - attempt * 0.08
        g = Grid(BIG, BIG)
        g.fill(None)
        draw(g, spec, BIG / 2.0, BIG / 2.0, scale)
        xs = [x for y in range(BIG) for x in range(BIG) if g.g[y][x] is not None]
        ys = [y for y in range(BIG) for x in range(BIG) if g.g[y][x] is not None]
        if not xs:
            break
        w = max(xs) - min(xs) + 1
        h = max(ys) - min(ys) + 1
        if max(w, h) <= want and w <= size - 2 * margin and h <= size - 2 * margin:
            out = Grid(size, size)
            out.fill(bg)
            ox = (size - w) // 2 - min(xs)
            oy = (size - h) // 2 - min(ys)
            for y in range(BIG):
                for x in range(BIG):
                    if g.g[y][x] is not None:
                        out.set(x + ox, y + oy, g.g[y][x])
            return out
    out = Grid(size, size)
    out.fill(bg)
    return out


_LAB = {c["id"]: rgb_to_lab(*(v / 255.0 for v in hex_to_rgb(c["hex"]))) for c in PALETTE}


def _contrast(a, b):
    """Plain CIE76 distance - good enough to rank backgrounds by separation."""
    la, lb = _LAB[a], _LAB[b]
    return sum((la[i] - lb[i]) ** 2 for i in range(3)) ** 0.5


def _pick_bg(main, options, nth=0):
    """The background that stands furthest from the subject's body colour.

    Rotating backgrounds blindly produced silver fish on light grey water and
    tan fish on ivory: structurally distinct patterns that are invisible are
    not quality. Ranking by separation and taking the nth-best keeps variety
    without ever landing on camouflage.
    """
    ranked = sorted(options, key=lambda o: -_contrast(main, o))
    return ranked[nth % max(1, min(len(ranked), 4))]


def _outline(g, cid, bg):
    """One-bead dark edge around SOLID masses only.

    Outlining every edge bead worked when appendages were one bead wide and
    got skipped as hopeless. Now that legs, antennae and stems are two beads
    wide (canvas.Grid.limb), every bead in them is an edge bead - so the
    outline ate the whole limb and the bugs came out as black scribbles with a
    coloured body.

    A bead is outlined only if it neighbours a bead that survives one erosion,
    i.e. one that has all four neighbours filled. A two-wide strand erodes to
    nothing and keeps its own colour; a body has an interior and gets its edge.
    """
    solid = [[False] * g.w for _ in range(g.h)]
    for y in range(g.h):
        for x in range(g.w):
            if g.g[y][x] in (None, bg):
                continue
            if all(g.inb(x + dx, y + dy) and g.g[y + dy][x + dx] not in (None, bg)
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                solid[y][x] = True
    edge = []
    for y in range(g.h):
        for x in range(g.w):
            if g.g[y][x] in (None, bg):
                continue
            outside = any(not g.inb(x + dx, y + dy) or
                          g.g[y + dy][x + dx] in (None, bg)
                          for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if not outside:
                continue
            near_solid = solid[y][x] or any(
                g.inb(x + dx, y + dy) and solid[y + dy][x + dx]
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if near_solid:
                edge.append((x, y))
    for x, y in edge:
        g.set(x, y, cid)


# ── BIRDS ────────────────────────────────────────────────────────────────────
# Species are proportions: neck and leg length separate a heron from a wren,
# beak shape separates a duck from a finch, tail shape a swallow from an owl.

BIRD_SPECIES = [
    # name        body      neck  head beak      tail        legs crest wing
    ("Wren",      (5.0, 4.2), 0.0, 3.0, "cone",   "cocked",   2,  0,   "folded"),
    ("Finch",     (5.2, 4.4), 0.4, 3.2, "cone",   "notch",    2,  0,   "folded"),
    ("Robin",     (5.6, 4.8), 0.6, 3.4, "cone",   "fan",      3,  0,   "folded"),
    ("Cardinal",  (5.6, 4.8), 0.6, 3.4, "cone",   "long",     3,  4,   "folded"),
    ("Owl",       (6.6, 6.0), 0.0, 5.0, "hook",   "short",    2,  2,   "tucked"),
    ("Parrot",    (5.4, 5.0), 0.8, 3.8, "hook",   "long",     2,  3,   "folded"),
    ("Toucan",    (5.6, 5.0), 0.8, 3.6, "huge",   "fan",      2,  0,   "folded"),
    ("Duck",      (7.0, 4.4), 1.2, 3.2, "spoon",  "short",    0,  0,   "folded"),
    ("Swan",      (7.2, 4.2), 6.0, 3.0, "spoon",  "short",    0,  0,   "folded"),
    ("Heron",     (5.0, 3.6), 6.5, 2.8, "dagger", "short",    9,  2,   "folded"),
    ("Flamingo",  (5.2, 3.8), 7.0, 2.6, "hook",   "short",   10,  0,   "folded"),
    ("Penguin",   (5.2, 7.0), 0.0, 3.4, "cone",   "none",     2,  0,   "flipper"),
    ("Swallow",   (4.6, 3.2), 0.4, 2.8, "cone",   "forked",   0,  0,   "spread"),
    ("Eagle",     (6.0, 5.0), 0.6, 4.0, "hook",   "fan",      3,  0,   "spread"),
    ("Hummingbird", (3.6, 2.8), 0.6, 2.4, "needle", "notch",  0,  0,   "spread"),
    ("Peacock",   (5.6, 4.6), 1.4, 3.0, "cone",   "train",    3,  3,   "folded"),
    ("Rooster",   (6.0, 5.2), 1.2, 3.4, "cone",   "plume",    3,  5,   "folded"),
    ("Pelican",   (6.6, 4.6), 1.6, 3.6, "pouch",  "short",    2,  0,   "folded"),
    ("Kingfisher",(5.0, 4.2), 0.4, 3.6, "dagger", "short",    2,  3,   "folded"),
    ("Ostrich",   (6.0, 5.0), 7.5, 2.6, "cone",   "plume",   11,  0,   "tucked"),
]

# (body, belly, beak/legs, wing) - the wing is a shade of the body so it reads
# as plumage rather than as a patch of something else.
BIRD_COLOURS = [
    ("brown", "cream", "orange", "dark_brown"),
    ("navy", "sky_blue", "cheddar", "dark_blue"),
    ("red", "blush", "orange", "dark_red"),
    ("dark_green", "light_green", "yellow", "forest"),
    ("purple", "lavender", "orange", "dark_purple"),
    ("black", "white", "cheddar", "dark_gray"),
    ("teal", "toothpaste", "banana", "light_teal"),
    ("hot_pink", "light_pink", "black", "magenta"),
    ("olive", "cream", "orange", "army_green"),
    ("blue", "aqua", "cheddar", "dark_blue"),
]
# Backgrounds stay pale. A saturated ground competes with the subject and, at
# 100% fill, is also most of the beads you have to buy.
BIRD_SKY = ["light_gray", "cream", "light_lavender", "toothpaste",
            "ivory", "light_pink", "silver", "peach"]


def _draw_bird(g, spec, cx, cy, scale):
    body, neck, head, beak, tail, legs, crest, wing = spec["parts"]
    main, belly, bill, wingc = spec["cols"]
    rx, ry = body[0] * scale, body[1] * scale
    neck *= scale; head *= scale; legs *= scale

    if legs:
        for off in (-1.4, 1.4):
            g.limb(cx + off, cy + ry - 1, cx + off * 0.6, cy + ry + legs, bill)
            g.limb(cx + off * 0.6, cy + ry + legs, cx + off * 0.6 + 1.8,
                   cy + ry + legs, bill)
    g.ellipse(cx, cy, rx, ry, main)
    g.ellipse(cx + 0.6, cy + ry * 0.35, rx * 0.66, ry * 0.5, belly)

    hx, hy = cx + rx * 0.55, cy - ry - neck * 0.55
    if neck > 0.5:
        g.line(cx + rx * 0.2, cy - ry * 0.4, hx, hy + head * 0.4, main,
               t=max(1, head * 0.32))
    g.disc(hx, hy, head, main)

    bx = cx - rx
    if tail == "cocked":
        g.poly([(bx, cy), (bx - 3 * scale, cy - 7 * scale),
                (bx - 1, cy - 7 * scale), (bx + 1, cy + 2)], main)
    elif tail == "long":
        g.poly([(bx + 1, cy - 1), (bx - 9 * scale, cy + 5 * scale),
                (bx - 8 * scale, cy + 7 * scale), (bx + 1, cy + 3)], main)
    elif tail == "forked":
        g.poly([(bx + 1, cy - 1), (bx - 8 * scale, cy - 4 * scale),
                (bx - 3 * scale, cy + 1), (bx - 8 * scale, cy + 6 * scale)], main)
    elif tail == "fan":
        g.poly([(bx + 1, cy - 2), (bx - 6 * scale, cy - 4 * scale),
                (bx - 7 * scale, cy + 4 * scale), (bx + 1, cy + 3)], main)
    elif tail == "notch":
        g.poly([(bx + 1, cy - 1), (bx - 4 * scale, cy),
                (bx - 4 * scale, cy + 4 * scale), (bx + 1, cy + 2)], main)
    elif tail == "short":
        g.poly([(bx + 1, cy), (bx - 3 * scale, cy + 1),
                (bx - 3 * scale, cy + 3), (bx + 1, cy + 3)], main)
    elif tail == "train":
        for k in range(-2, 3):
            ty = cy + 1 + k * 3.0 * scale
            g.limb(bx, cy + 1, bx - 10 * scale, ty, belly)
            g.disc(bx - 10 * scale, ty, 1.6 * scale, main)
    elif tail == "plume":
        for k in range(3):
            g.limb(bx + 1, cy - 1, bx - (5 + k) * scale,
                   cy - 6 * scale + k * 2.4 * scale, main)

    if wing == "folded":
        # The wing reads as a wing because of its EDGE, so it is drawn as a
        # shade of the body rather than in the beak colour - an orange wing
        # patch on a purple bird just looked like a mistake.
        g.ellipse(cx - rx * 0.15, cy + 0.4, rx * 0.72, ry * 0.46, wingc)
    elif wing == "spread":
        g.poly([(cx - 1, cy - 2), (cx - rx - 7 * scale, cy - ry - 5 * scale),
                (cx - rx - 3 * scale, cy + 1)], wingc)
        g.poly([(cx + 1, cy - 2), (cx + rx + 7 * scale, cy - ry - 5 * scale),
                (cx + rx + 3 * scale, cy + 1)], wingc)
    elif wing == "flipper":
        g.ellipse(cx - rx * 0.55, cy + 1, rx * 0.34, ry * 0.62, wingc)

    tipx = hx + head
    if beak == "cone":
        g.poly([(tipx - 1, hy - 1), (tipx + 3 * scale, hy), (tipx - 1, hy + 1.4)], bill)
    elif beak == "dagger":
        g.poly([(tipx - 1, hy - 1), (tipx + 7 * scale, hy + 0.4), (tipx - 1, hy + 1.2)], bill)
    elif beak == "needle":
        g.limb(tipx - 1, hy, tipx + 7 * scale, hy - 1, bill)
    elif beak == "hook":
        g.poly([(tipx - 1, hy - 1.6), (tipx + 3.4 * scale, hy - 0.6),
                (tipx + 2.4 * scale, hy + 2.2), (tipx - 1, hy + 1)], bill)
    elif beak == "huge":
        g.poly([(tipx - 1.5, hy - 2.4), (tipx + 5 * scale, hy - 2.0),
                (tipx + 8.5 * scale, hy + 0.6), (tipx + 4 * scale, hy + 2.4),
                (tipx - 1.5, hy + 2.0)], bill)
    elif beak == "spoon":
        g.poly([(tipx - 1, hy - 1), (tipx + 4.5 * scale, hy - 0.6),
                (tipx + 4.9 * scale, hy + 1.8), (tipx - 1, hy + 1.8)], bill)
    elif beak == "pouch":
        g.poly([(tipx - 1, hy - 1), (tipx + 5.5 * scale, hy),
                (tipx + 4.5 * scale, hy + 4.5 * scale), (tipx - 1, hy + 2)], bill)

    # A crest is a filled plume swept back over the skull. Drawn as radiating
    # lines it read as antennae, and at one bead wide it read as wire.
    if crest:
        ln = head * (0.7 + 0.22 * crest)
        g.poly([(hx + head * 0.45, hy - head * 0.72),
                (hx - head * 0.15 - ln * 0.5, hy - head * 0.85 - ln),
                (hx - head * 0.55 - ln * 0.9, hy - head * 0.35 - ln * 0.55),
                (hx - head * 0.75, hy - head * 0.15)], main)

    dark = "black" if main not in ("black", "dark_blue", "navy") else "dark_gray"
    _outline(g, dark, None)
    g.set(hx + head * 0.35, hy - head * 0.25, "white")
    g.set(hx + head * 0.35 + 1, hy - head * 0.25, dark)


def birds():
    specs = []
    # Every variant changes the DRAWING or the share of the board it takes.
    # A pure scale factor is cancelled by _frame's auto-fit.
    poses = [("", {"fill": 0.96}), (" Perched", {"legs": +2, "fill": 0.96}),
             (" Calling", {"head": +0.9, "fill": 0.86}),
             (" Wings Out", {"wing": "spread", "fill": 0.96}),
             (" Alert", {"neck": +3.0, "fill": 0.80})]
    for pi, (suffix, tweak) in enumerate(poses):
        for si, (name, body, neck, head, beak, tail, legs, crest, wing) in enumerate(BIRD_SPECIES):
            parts = (body,
                     max(0.0, neck + tweak.get("neck", 0)),
                     head + tweak.get("head", 0),
                     beak, tail,
                     max(0, legs + tweak.get("legs", 0)), crest,
                     tweak.get("wing", wing))
            specs.append(dict(
                name=f"{name}{suffix}", parts=parts, fill=tweak["fill"],
                cols=BIRD_COLOURS[(si + pi) % len(BIRD_COLOURS)],
                bg=_pick_bg(BIRD_COLOURS[(si + pi) % len(BIRD_COLOURS)][0], BIRD_SKY, si + pi),
                tags=["bird", name.lower()]))
    return _emit("birds", specs, lambda sp: _frame(_draw_bird, sp, sp["bg"]), 100)


GENERATORS = {"birds": birds}


# ── FISH ─────────────────────────────────────────────────────────────────────
# Body proportion plus tail and fin shape is what tells a puffer from an eel.

FISH_SPECIES = [
    # name        body        tail      dorsal ventral snout stripe
    ("Goldfish",  (6.0, 4.4), "veil",   0.9, 0.7, "round",  "none"),
    ("Koi",       (7.0, 4.0), "fan",    0.7, 0.6, "round",  "blotch"),
    ("Clownfish", (5.6, 4.0), "fan",    0.8, 0.6, "round",  "bands"),
    ("Angelfish", (4.6, 5.6), "point",  1.9, 1.8, "round",  "bands"),
    ("Betta",     (5.0, 4.0), "veil",   1.6, 1.5, "round",  "none"),
    ("Puffer",    (5.4, 5.2), "round",  0.5, 0.5, "blunt",  "spots"),
    ("Shark",     (8.4, 3.4), "lunate", 1.3, 0.7, "point",  "none"),
    ("Tuna",      (8.0, 3.4), "lunate", 0.9, 0.6, "point",  "none"),
    ("Swordfish", (8.0, 3.0), "lunate", 1.2, 0.6, "sword",  "none"),
    ("Eel",       (10.0, 1.9), "point", 0.5, 0.4, "point",  "none"),
    ("Guppy",     (4.2, 2.8), "veil",   0.7, 0.6, "round",  "spots"),
    ("Catfish",   (7.4, 3.6), "fork",   0.8, 0.6, "blunt",  "none"),
    ("Trout",     (7.6, 3.4), "fork",   0.8, 0.6, "point",  "spots"),
    ("Flounder",  (6.4, 5.0), "round",  0.6, 0.6, "blunt",  "spots"),
    ("Piranha",   (5.4, 4.6), "fork",   0.9, 0.8, "blunt",  "none"),
    ("Sunfish",   (5.0, 5.4), "round",  1.7, 1.6, "blunt",  "none"),
    ("Barb",      (5.0, 3.6), "fork",   0.8, 0.7, "round",  "bands"),
    ("Tetra",     (4.4, 3.2), "fork",   0.7, 0.6, "round",  "bands"),
    ("Marlin",    (8.6, 3.2), "lunate", 2.0, 0.6, "sword",  "none"),
    ("Grouper",   (7.0, 4.6), "fan",    0.9, 0.7, "blunt",  "blotch"),
    ("Seahorse",  (3.0, 6.4), "point",  1.4, 0.4, "point",  "bands"),
    ("Ray",       (9.0, 2.2), "point",  0.4, 0.4, "blunt",  "spots"),
    ("Carp",      (8.0, 4.4), "fan",    0.8, 0.6, "blunt",  "bands"),
    ("Perch",     (6.4, 4.2), "fork",   1.1, 0.8, "point",  "bands"),
    ("Snapper",   (7.2, 4.8), "fork",   0.9, 0.7, "point",  "blotch"),
    ("Bass",      (7.8, 4.2), "fan",    1.0, 0.7, "blunt",  "spots"),
    ("Minnow",    (3.8, 2.4), "fork",   0.6, 0.5, "point",  "none"),
    ("Discus",    (5.2, 6.0), "point",  1.5, 1.4, "blunt",  "bands"),
]

FISH_COLOURS = [
    ("orange", "dark_red", "banana"), ("red", "dark_red", "blush"),
    ("yellow", "orange", "cream"), ("blue", "navy", "aqua"),
    ("teal", "dark_green", "toothpaste"), ("purple", "dark_purple", "lavender"),
    ("navy", "black", "silver"), ("green", "forest", "light_green"),
    ("magenta", "purple", "light_pink"), ("dark_brown", "black", "tan"),
]
WATER = ["toothpaste", "aqua", "light_gray", "ivory", "sky_blue",
         "cream", "light_lavender", "silver"]


def _draw_fish(g, spec, cx, cy, scale):
    (rx, ry), tail, dorsal, ventral, snout, stripe = spec["parts"]
    main, accent, belly = spec["cols"]
    rx *= scale * 1.3; ry *= scale * 1.3
    ts = max(0.55, min(1.15, ry / 5.0))   # tail scales with the body, not the board

    if dorsal > 0.3:
        g.poly([(cx - rx * 0.4, cy - ry * 0.8), (cx + rx * 0.1, cy - ry - 4.4 * dorsal * scale),
                (cx + rx * 0.6, cy - ry * 0.7)], accent)
    if ventral > 0.3:
        g.poly([(cx - rx * 0.3, cy + ry * 0.8), (cx, cy + ry + 4.0 * ventral * scale),
                (cx + rx * 0.5, cy + ry * 0.7)], accent)

    g.ellipse(cx, cy, rx, ry, main)
    g.ellipse(cx + rx * 0.15, cy + ry * 0.55, rx * 0.55, ry * 0.30, belly)

    if snout == "point":
        g.poly([(cx + rx * 0.5, cy - ry * 0.7), (cx + rx + 3.2 * scale, cy),
                (cx + rx * 0.5, cy + ry * 0.7)], main)
    elif snout == "sword":
        g.poly([(cx + rx * 0.6, cy - 1), (cx + rx + 9 * scale, cy),
                (cx + rx * 0.6, cy + 1)], main)

    bx = cx - rx
    if tail == "fan":
        g.poly([(bx + 1, cy), (bx - 4.6 * scale * ts, cy - 4.4 * scale * ts),
                (bx - 4.6 * scale * ts, cy + 4.4 * scale * ts)], accent)
    elif tail == "fork":
        g.poly([(bx + 1, cy), (bx - 5.2 * scale * ts, cy - 5 * scale * ts), (bx - 3.0 * scale * ts, cy),
                (bx - 5.2 * scale * ts, cy + 5 * scale * ts)], accent)
    elif tail == "lunate":
        g.poly([(bx + 1, cy), (bx - 5.8 * scale * ts, cy - 6 * scale * ts), (bx - 3.8 * scale * ts, cy),
                (bx - 5.8 * scale * ts, cy + 6 * scale * ts)], accent)
        g.poly([(bx - 3.8 * scale * ts, cy), (bx - 5.8 * scale * ts, cy - 6 * scale * ts),
                (bx - 5.2 * scale * ts, cy - 6 * scale * ts)], None)
    elif tail == "veil":
        g.poly([(bx + 1, cy - 1), (bx - 6.4 * scale * ts, cy - 6 * scale * ts),
                (bx - 5.2 * scale * ts, cy), (bx - 6.4 * scale * ts, cy + 6 * scale * ts), (bx + 1, cy + 1)], accent)
    elif tail == "round":
        g.ellipse(bx - 2.2 * scale * ts, cy, 3.4 * scale, 3.6 * scale, accent)
    elif tail == "point":
        g.poly([(bx + 1, cy - 1.6), (bx - 5.2 * scale * ts, cy), (bx + 1, cy + 1.6)], accent)

    if stripe == "bands":
        for k in (-0.35, 0.1, 0.55):
            g.rect(cx + rx * k - 1, cy - ry, cx + rx * k + 0.6, cy + ry, accent)
    elif stripe == "spots":
        for k, (ux, uy) in enumerate(((-0.4, -0.3), (0.05, 0.25), (0.4, -0.25), (-0.1, -0.55))):
            g.disc(cx + rx * ux, cy + ry * uy, 1.1 * scale, accent)
    elif stripe == "blotch":
        g.ellipse(cx - rx * 0.3, cy - ry * 0.25, rx * 0.32, ry * 0.4, accent)
        g.ellipse(cx + rx * 0.4, cy + ry * 0.2, rx * 0.24, ry * 0.3, accent)

    g.ellipse(cx - rx * 0.02, cy + ry * 0.22, rx * 0.26, ry * 0.24, accent)  # pectoral
    _outline(g, "black" if main != "black" else "dark_gray", None)
    ex, ey = cx + rx * 0.62, cy - ry * 0.28
    g.disc(ex, ey, 1.3 * scale, "white")
    g.disc(ex + 0.4, ey, 0.8 * scale, "black")


def fish():
    specs = []
    poses = [("", 0.96, {}), (" Small", 0.72, {}),
             (" Finned", 0.96, {"dorsal": 1.2, "ventral": 1.0}),
             (" Sleek", 0.78, {"dorsal": -0.4, "ventral": -0.35}),
             (" Spotted", 0.96, {"stripe": "spots"})]
    for pi, (suffix, sc, tw) in enumerate(poses):
        for si, (name, body, tail, dor, ven, snout, stripe) in enumerate(FISH_SPECIES):
            specs.append(dict(
                name=f"{name}{suffix}", fill=sc,
                parts=((body[0], body[1]),
                       tail,
                       max(0.0, dor + tw.get("dorsal", 0)),
                       max(0.0, ven + tw.get("ventral", 0)),
                       snout, tw.get("stripe", stripe)),
                cols=FISH_COLOURS[(si * 3 + pi) % len(FISH_COLOURS)],
                bg=_pick_bg(FISH_COLOURS[(si * 3 + pi) % len(FISH_COLOURS)][0], WATER, si + pi),
                tags=["fish", name.lower()], scale=1.0))
    return _emit("fish", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_fish(g, s, x, y, k * s["scale"]),
                                   sp, sp["bg"]), 100)


# ── BUGS ─────────────────────────────────────────────────────────────────────

BUG_SPECIES = [
    # name          plan       wings legs segs ants extra      body (len, width)
    ("Ladybug",     "beetle",   0,   6,  1,  2, "spots",    (6.2, 5.2)),
    ("Beetle",      "beetle",   0,   6,  1,  2, "split",    (7.4, 4.4)),
    ("Stag Beetle", "beetle",   0,   6,  1,  2, "horns",    (8.2, 4.0)),
    ("Weevil",      "beetle",   0,   6,  1,  2, "snout",    (5.6, 3.4)),
    ("Chafer",      "beetle",   0,   6,  1,  2, "bands",    (6.8, 5.6)),
    ("Butterfly",   "flier",    2,   6,  3,  2, "wingdot",  (6.4, 2.6)),
    ("Moth",        "flier",    2,   6,  3,  2, "furry",    (5.6, 3.4)),
    ("Dragonfly",   "flier",    4,   6,  5,  2, "long",     (10.4, 1.8)),
    ("Damselfly",   "flier",    4,   6,  6,  2, "long",     (9.0, 1.4)),
    ("Bee",         "flier",    2,   6,  3,  2, "bands",    (5.4, 3.8)),
    ("Wasp",        "flier",    2,   6,  4,  2, "waist",    (7.0, 2.4)),
    ("Hornet",      "flier",    2,   6,  4,  2, "bands",    (8.0, 3.0)),
    ("Firefly",     "flier",    2,   6,  3,  2, "glow",     (6.0, 2.8)),
    ("Cicada",      "flier",    2,   6,  2,  2, "none",     (6.6, 4.2)),
    ("Ant",         "walker",   0,   6,  3,  2, "none",     (6.0, 2.2)),
    ("Termite",     "walker",   0,   6,  3,  2, "bands",    (6.6, 2.8)),
    ("Grasshopper", "walker",   0,   6,  2,  2, "jump",     (8.4, 2.6)),
    ("Cricket",     "walker",   0,   6,  2,  2, "jump",     (7.0, 3.2)),
    ("Mantis",      "walker",   0,   6,  3,  2, "claws",    (9.0, 2.0)),
    ("Stick Insect","walker",   0,   6,  5,  2, "none",     (11.5, 1.2)),
    ("Caterpillar", "crawler",  0,   8,  7,  2, "none",     (0, 0)),
    ("Centipede",   "crawler",  0,  14, 10,  2, "none",     (0, 0)),
    ("Millipede",   "crawler",  0,  18, 13,  2, "none",     (0, 0)),
    ("Grub",        "crawler",  0,   6,  5,  2, "none",     (0, 0)),
    ("Spider",      "spider",   0,   8,  2,  0, "none",     (4.0, 4.6)),
    ("Tarantula",   "spider",   0,   8,  2,  0, "furry",    (5.4, 5.6)),
    ("Scorpion",    "spider",   0,   8,  4,  0, "sting",    (4.4, 5.0)),
    ("Snail",       "snail",    0,   0,  1,  2, "shell",    (0, 0)),
    ("Slug",        "snail",    0,   0,  1,  2, "none",     (0, 0)),
]

BUG_COLOURS = [
    ("red", "black", "white"), ("dark_green", "light_green", "yellow"),
    ("navy", "sky_blue", "white"), ("purple", "lavender", "banana"),
    ("orange", "dark_brown", "cream"), ("black", "yellow", "white"),
    ("teal", "aqua", "cream"), ("magenta", "light_pink", "white"),
    ("brown", "tan", "cream"), ("olive", "army_green", "banana"),
]
LEAF = ["light_green", "cream", "ivory", "toothpaste", "light_gray",
        "banana", "peach", "light_lavender"]


def _draw_bug(g, spec, cx, cy, scale):
    plan, wings, legs, segs, ants, extra, body = spec["parts"]
    main, accent, hi = spec["cols"]
    u = scale

    if plan in ("beetle", "flier", "walker"):
        # Proportions per species: a stick insect and a chafer share the walker
        # and beetle plans but must not share a silhouette. One hard-coded body
        # per plan is what collapsed twenty species into six shapes.
        bl = body[0] * u
        bw = body[1] * u
        for i in range(legs // 2):
            ly = cy - bl * 0.4 + i * bl * 0.55
            for sgn in (-1, 1):
                g.limb(cx + sgn * bw * 0.6, ly, cx + sgn * (bw + 4 * u),
                       ly + (2.4 * u if plan != "walker" else 3.6 * u), accent)
        if wings:
            if extra in ("wingdot", "furry"):
                # A butterfly is mostly wing. Drawn at the same scale as a
                # bee's, it just read as a fly.
                for sgn in (-1, 1):
                    g.ellipse(cx + sgn * bw * 2.3, cy - bl * 0.45, bw * 2.3, bl * 0.75, hi)
                    g.ellipse(cx + sgn * bw * 1.8, cy + bl * 0.55, bw * 1.8, bl * 0.55, hi)
            else:
                for sgn in (-1, 1):
                    g.ellipse(cx + sgn * bw * 1.5, cy - bl * 0.15, bw * 1.5, bl * 0.62, hi)
                    if wings == 4:
                        g.ellipse(cx + sgn * bw * 1.35, cy + bl * 0.45, bw * 1.15, bl * 0.4, hi)
        g.ellipse(cx, cy, bw, bl, main)
        g.disc(cx, cy - bl - 1.2 * u, 2.4 * u, accent)
        if extra == "spots":
            for ux, uy in ((-0.45, -0.35), (0.45, -0.35), (-0.4, 0.3), (0.4, 0.3), (0, 0)):
                g.disc(cx + bw * ux, cy + bl * uy, 1.2 * u, accent)
        elif extra == "split":
            g.rect(cx - 0.4, cy - bl, cx + 0.4, cy + bl, accent)
        elif extra == "bands":
            for k in (-0.5, 0.0, 0.5):
                g.rect(cx - bw, cy + bl * k - 0.8 * u, cx + bw, cy + bl * k + 0.8 * u, accent)
        elif extra == "horns":
            for sgn in (-1, 1):
                g.limb(cx + sgn * 1.4 * u, cy - bl - 2 * u,
                       cx + sgn * 4 * u, cy - bl - 6 * u, accent)
        elif extra == "wingdot":
            for sgn in (-1, 1):
                g.disc(cx + sgn * bw * 2.4, cy - bl * 0.55, 2.0 * u, accent)
                g.disc(cx + sgn * bw * 1.7, cy + bl * 0.6, 1.4 * u, accent)
        elif extra == "glow":
            g.ellipse(cx, cy + bl * 0.7, bw * 0.8, bl * 0.3, hi)
        elif extra == "waist":
            g.ellipse(cx, cy + bl * 0.15, bw * 0.35, bl * 0.12, None)
        elif extra == "snout":
            g.limb(cx, cy - bl - 3 * u, cx, cy - bl - 6 * u, accent)
        elif extra == "claws":
            for sgn in (-1, 1):
                g.limb(cx + sgn * bw, cy - bl * 0.6, cx + sgn * (bw + 4 * u), cy - bl * 1.2, accent)
        elif extra == "jump":
            for sgn in (-1, 1):
                g.limb(cx + sgn * bw * 0.7, cy + bl * 0.2, cx + sgn * (bw + 3 * u), cy - bl * 0.4, accent)
                g.limb(cx + sgn * (bw + 3 * u), cy - bl * 0.4, cx + sgn * (bw + 5 * u), cy + bl * 0.6, accent)
        hy = cy - bl - 1.2 * u
    elif plan == "crawler":
        for i in range(segs):
            sx = cx - (segs - 1) * 1.9 * u / 2 + i * 1.9 * u
            g.disc(sx, cy + math.sin(i * 0.9) * 1.4 * u, 2.2 * u, main if i else accent)
            if i % 2 == 0:
                g.limb(sx, cy + 2 * u, sx, cy + 5 * u, accent)
        hy = cy - 2 * u
    elif plan == "spider":
        g.ellipse(cx, cy + 2 * u, body[0] * u, body[1] * u, main)
        g.disc(cx, cy - body[1] * 0.6 * u, 2.6 * u, accent)
        if extra == "furry":
            for k in range(10):
                a = k * math.pi / 5
                g.limb(cx + math.cos(a) * body[0] * 0.9 * u,
                       cy + 2 * u + math.sin(a) * body[1] * 0.9 * u,
                       cx + math.cos(a) * (body[0] + 1.6) * u,
                       cy + 2 * u + math.sin(a) * (body[1] + 1.6) * u, main)
        for i in range(4):
            for sgn in (-1, 1):
                a = -0.9 + i * 0.55
                g.limb(cx + sgn * 2 * u, cy + 1 * u,
                       cx + sgn * (4 + 6 * math.cos(a)) * u, cy + 1 * u + 7 * math.sin(a) * u, accent)
        if extra == "sting":
            g.limb(cx, cy + 6 * u, cx + 7 * u, cy + 1 * u, accent)
            g.disc(cx + 7.6 * u, cy + 0.4 * u, 1.4 * u, hi)
        hy = cy - 2.6 * u
    else:   # snail / slug
        g.ellipse(cx - 1.5 * u, cy + 3.4 * u, 6.5 * u, 2.2 * u, accent)
        if extra == "shell":
            for k in range(4):
                g.ring(cx + 1.5 * u, cy, (6.2 - k * 1.5) * u,
                       main if k % 2 == 0 else hi, t=1.4 * u)
        else:
            g.ellipse(cx + 0.5 * u, cy + 1.4 * u, 5.6 * u, 2.4 * u, main)
        hy = cy + 1.5 * u
        cx = cx - 6 * u

    for k in range(ants):
        sgn = -1 if k == 0 else 1
        g.limb(cx + sgn * 1.2 * u, hy - 1.4 * u, cx + sgn * 4.4 * u, hy - 6 * u, accent)
    _outline(g, "black" if main != "black" else "dark_gray", None)
    for sgn in (-1, 1):
        g.set(cx + sgn * 1.1 * u, hy - 0.4 * u, hi)


def bugs():
    specs = []
    # Variants have to change the DRAWING, not just a field the plan ignores.
    # A "Winged" spider is still a spider, so the first cut lost a third of the
    # category to structural collisions; leg count and segment count move
    # something in every plan.
    poses = [("", 0.96, {}), (" Small", 0.72, {}),
             (" Long", 0.96, {"segs": +3, "legs": +4}),
             (" Slender", 0.78, {"segs": +1, "legs": -2}),
             (" Antennaed", 0.96, {"ants": +2, "segs": +2})]
    for pi, (suffix, sc, tw) in enumerate(poses):
        for si, (name, plan, wings, legs, segs, ants, extra, body) in enumerate(BUG_SPECIES):
            w2 = wings + tw.get("wings", 0) if plan == "flier" else wings
            specs.append(dict(
                name=f"{name}{suffix}",
                parts=(plan, w2, max(4, legs + tw.get("legs", 0)),
                       max(1, segs + tw.get("segs", 0)),
                       ants + tw.get("ants", 0), extra, body),
                cols=BUG_COLOURS[(si * 7 + pi) % len(BUG_COLOURS)],
                bg=_pick_bg(BUG_COLOURS[(si * 7 + pi) % len(BUG_COLOURS)][0], LEAF, si + pi),
                fill=sc, tags=["bug", name.lower()], scale=1.0))
    return _emit("bugs", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_bug(g, s, x, y, k * s["scale"]),
                                   sp, sp["bg"]), 100)


# ── TREES ────────────────────────────────────────────────────────────────────

TREE_SPECIES = [
    # name          crown      tiers trunk  branch  extras
    ("Oak",         "round",   1,   (2.6, 8),  0,  "none"),
    ("Maple",       "round",   1,   (2.2, 8),  0,  "fruit"),
    ("Pine",        "conifer", 4,   (2.0, 5),  0,  "none"),
    ("Fir",         "conifer", 5,   (1.8, 4),  0,  "none"),
    ("Spruce",      "conifer", 3,   (2.2, 5),  0,  "none"),
    ("Birch",       "oval",    1,   (1.8, 10), 0,  "bands"),
    ("Poplar",      "column",  1,   (2.0, 6),  0,  "none"),
    ("Cypress",     "column",  1,   (1.8, 5),  0,  "none"),
    ("Willow",      "weep",    1,   (2.4, 7),  0,  "none"),
    ("Palm",        "palm",    0,   (2.0, 12), 6,  "coco"),
    ("Cactus",      "cactus",  0,   (3.6, 12), 2,  "none"),
    ("Bonsai",      "cloud",   3,   (2.6, 5),  2,  "none"),
    ("Apple Tree",  "round",   1,   (2.6, 7),  0,  "fruit"),
    ("Cherry",      "round",   1,   (2.4, 7),  0,  "blossom"),
    ("Baobab",      "flat",    1,   (5.0, 8),  2,  "none"),
    ("Acacia",      "flat",    1,   (2.2, 9),  2,  "none"),
    ("Bare Tree",   "bare",    0,   (2.6, 9),  4,  "none"),
    ("Bamboo",      "bamboo",  5,   (1.6, 16), 0,  "none"),
    ("Mushroom",    "cap",     0,   (3.0, 7),  0,  "spots"),
    ("Topiary",     "ball",    3,   (1.8, 6),  0,  "none"),
    ("Redwood",     "conifer", 6,   (2.6, 6),  0,  "none"),
    ("Juniper",     "cloud",   4,   (2.0, 4),  3,  "none"),
    ("Olive",       "flat",    1,   (2.4, 7),  3,  "fruit"),
    ("Magnolia",    "round",   1,   (2.4, 6),  2,  "blossom"),
    ("Aspen",       "oval",    1,   (1.6, 11), 0,  "bands"),
    ("Yew",         "column",  1,   (2.4, 4),  0,  "fruit"),
    ("Fern",        "palm",    0,   (1.6, 5),  8,  "none"),
    ("Dead Tree",   "bare",    0,   (2.0, 11), 6,  "none"),
]

TREE_COLOURS = [
    ("dark_green", "green", "brown"), ("forest", "light_green", "dark_brown"),
    ("olive", "army_green", "brown"), ("green", "light_green", "caramel"),
    ("teal", "toothpaste", "dark_brown"), ("dark_green", "olive", "rust"),
]
SKY = ["sky_blue", "cream", "ivory", "light_lavender", "toothpaste",
       "light_gray", "banana", "peach"]


def _draw_tree(g, spec, cx, cy, scale):
    crown, tiers, trunk, branch, extra = spec["parts"]
    leaf, leaf2, bark = spec["cols"]
    u = scale
    tw, th = trunk[0] * u, trunk[1] * u
    base = cy + 11 * u
    g.rect(cx - tw, base - th, cx + tw, base, bark)
    if extra == "bands":
        for k in range(3):
            g.rect(cx - tw, base - th * (0.25 + 0.25 * k), cx + tw,
                   base - th * (0.25 + 0.25 * k) + 0.9 * u, "dark_gray")
    for b in range(branch):
        sgn = -1 if b % 2 == 0 else 1
        by = base - th * (0.45 + 0.16 * b)
        g.line(cx, by, cx + sgn * 5 * u, by - 4 * u, bark, t=0)

    top = base - th
    if crown == "round":
        g.disc(cx, top - 5 * u, 8 * u, leaf)
        g.disc(cx - 2.6 * u, top - 6.6 * u, 4.4 * u, leaf2)
    elif crown == "oval":
        g.ellipse(cx, top - 5 * u, 5.4 * u, 8 * u, leaf)
        g.ellipse(cx - 1.6 * u, top - 6.5 * u, 3.0 * u, 4.4 * u, leaf2)
    elif crown == "column":
        g.ellipse(cx, top - 7 * u, 3.6 * u, 10 * u, leaf)
        g.ellipse(cx - 1.2 * u, top - 8 * u, 1.7 * u, 6 * u, leaf2)
    elif crown == "conifer":
        for k in range(tiers):
            wdt = (9 - k * 1.6) * u
            yy = top - k * 3.4 * u
            g.poly([(cx - wdt, yy), (cx + wdt, yy), (cx, yy - 6.5 * u)],
                   leaf if k % 2 == 0 else leaf2)
    elif crown == "weep":
        g.ellipse(cx, top - 4 * u, 8.5 * u, 5 * u, leaf)
        for k in range(-3, 4):
            g.limb(cx + k * 2.4 * u, top - 2 * u, cx + k * 2.6 * u, top + 5 * u, leaf2)
    elif crown == "palm":
        for k in range(branch):
            a = math.pi + k * math.pi / max(1, branch - 1)
            g.line(cx, top, cx + math.cos(a) * 9 * u, top + math.sin(a) * 6 * u - 2 * u, leaf, t=1)
            g.disc(cx + math.cos(a) * 9 * u, top + math.sin(a) * 6 * u - 2 * u, 1.6 * u, leaf2)
        if extra == "coco":
            for sgn in (-1, 1):
                g.disc(cx + sgn * 1.8 * u, top + 1.4 * u, 1.5 * u, bark)
    elif crown == "cactus":
        g.rect(cx - tw, base - th, cx + tw, base, leaf)
        for b in range(branch):
            sgn = -1 if b % 2 == 0 else 1
            ay = base - th * (0.55 + 0.22 * b)
            g.rect(cx + sgn * tw, ay - 1.4 * u, cx + sgn * 7 * u, ay + 1.4 * u, leaf)
            g.rect(cx + sgn * 7 * u - 1.4 * u, ay - 6 * u, cx + sgn * 7 * u + 1.4 * u, ay, leaf)
    elif crown == "cloud":
        for k in range(tiers):
            sgn = -1 if k % 2 == 0 else 1
            g.ellipse(cx + sgn * 3.4 * u, top - k * 3.6 * u, 5 * u, 2.6 * u,
                      leaf if k % 2 == 0 else leaf2)
    elif crown == "flat":
        g.ellipse(cx, top - 2.4 * u, 10 * u, 3.4 * u, leaf)
        g.ellipse(cx, top - 4.6 * u, 6 * u, 2.2 * u, leaf2)
    elif crown == "bare":
        for k in range(6):
            a = -2.6 + k * 0.42
            g.line(cx, top + 1, cx + math.cos(a) * 8 * u, top + 1 + math.sin(a) * 8 * u, bark, t=0)
    elif crown == "bamboo":
        for k in range(tiers):
            yy = base - th * (k + 1) / tiers
            g.rect(cx - tw, yy, cx + tw, yy + 0.9 * u, leaf2)
            for sgn in (-1, 1):
                if k % 2 == 0:
                    g.limb(cx + sgn * tw, yy, cx + sgn * 6 * u, yy - 3.4 * u, leaf)
    elif crown == "cap":
        g.ellipse(cx, top, 8.5 * u, 5 * u, leaf)
        g.rect(cx - 8.5 * u, top, cx + 8.5 * u, top + 5 * u, None)
        g.ellipse(cx, top, 8.5 * u, 5 * u, leaf)
        if extra == "spots":
            for ux in (-0.55, -0.1, 0.4):
                g.disc(cx + 8.5 * u * ux, top - 2 * u, 1.5 * u, leaf2)
    elif crown == "ball":
        for k in range(tiers):
            g.disc(cx, top - k * 5.2 * u, (5.2 - k * 0.9) * u, leaf if k % 2 == 0 else leaf2)

    if extra == "fruit":
        for ux, uy in ((-0.5, -0.2), (0.45, -0.45), (0.1, 0.25), (-0.2, -0.6)):
            g.disc(cx + 8 * u * ux, top - 5 * u + 8 * u * uy, 1.3 * u, "red")
    elif extra == "blossom":
        for ux, uy in ((-0.55, -0.1), (0.4, -0.5), (0.05, 0.3), (-0.15, -0.65), (0.6, 0.1)):
            g.disc(cx + 8 * u * ux, top - 5 * u + 8 * u * uy, 1.3 * u, "light_pink")
    _outline(g, "dark_brown" if leaf != "dark_brown" else "black", None)


def trees():
    specs = []
    poses = [("", 0.96, {}), (" Sapling", 0.72, {}),
             (" Tall", 0.96, {"trunk": 1.9}), (" Squat", 0.96, {"trunk": 0.45}),
             (" Young", 0.78, {"trunk": 1.2, "tiers": -1})]
    for pi, (suffix, sc, tw) in enumerate(poses):
        for si, (name, crown, tiers, trunk, branch, extra) in enumerate(TREE_SPECIES):
            tr = (trunk[0], trunk[1] * tw.get("trunk", 1.0))
            specs.append(dict(
                name=f"{name}{suffix}", fill=sc,
                parts=(crown, max(1, tiers + tw.get("tiers", 0)), tr, branch, extra),
                cols=TREE_COLOURS[(si * 3 + pi) % len(TREE_COLOURS)],
                bg=_pick_bg(TREE_COLOURS[(si * 3 + pi) % len(TREE_COLOURS)][0], SKY, si + pi),
                tags=["tree", name.lower()], scale=1.0))
    return _emit("trees", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_tree(g, s, x, y, k * s["scale"]),
                                   sp, sp["bg"]), 100)


GENERATORS.update({"fish": fish, "bugs": bugs, "trees": trees})


if __name__ == "__main__":
    for cat, fn in GENERATORS.items():
        ps = fn()
        print(f"{cat:8s} {len(ps):3d} patterns, "
              f"{len({signature(p) for p in ps}):3d} structurally unique")


# ── ANIMALS ──────────────────────────────────────────────────────────────────
# Land animals, side view. Body proportion + neck + ears + snout + tail is
# what separates a giraffe from a hippo; nothing here is a recolour.

ANIMAL_SPECIES = [
    # name        body        neck  head ear      snout  tail      legs mark
    ("Cat",       (6.2, 4.0), 1.2, 3.0, "point",  "flat", "curl",   4.0, "stripe"),
    ("Dog",       (6.6, 4.2), 1.4, 3.2, "flop",   "long", "up",     4.2, "patch"),
    ("Fox",       (6.4, 3.6), 1.2, 3.0, "point",  "long", "bushy",  3.8, "tip"),
    ("Wolf",      (7.0, 4.2), 1.6, 3.4, "point",  "long", "bushy",  4.6, "none"),
    ("Bear",      (7.6, 5.4), 0.8, 3.8, "round",  "flat", "stub",   3.4, "none"),
    ("Panda",     (7.4, 5.4), 0.8, 3.8, "round",  "flat", "stub",   3.4, "panda"),
    ("Rabbit",    (5.0, 4.0), 0.6, 3.0, "long",   "flat", "puff",   2.6, "none"),
    ("Mouse",     (4.2, 3.0), 0.4, 2.4, "round",  "point","thin",   1.8, "none"),
    ("Squirrel",  (4.4, 3.4), 0.8, 2.6, "point",  "point","plume",  2.2, "none"),
    ("Hedgehog",  (5.4, 3.4), 0.4, 2.4, "round",  "point","stub",   1.6, "spines"),
    ("Pig",       (6.4, 4.4), 0.6, 3.0, "point",  "snub", "curl",   2.6, "none"),
    ("Sheep",     (6.4, 4.6), 1.0, 2.8, "flop",   "flat", "stub",   3.2, "wool"),
    ("Cow",       (7.6, 4.8), 1.2, 3.4, "round",  "flat", "tuft",   4.2, "patch"),
    ("Horse",     (7.6, 4.4), 3.0, 3.0, "point",  "long", "plume",  6.0, "none"),
    ("Zebra",     (7.4, 4.4), 3.0, 3.0, "point",  "long", "tuft",   6.0, "stripe"),
    ("Giraffe",   (6.4, 4.0), 8.5, 2.6, "point",  "long", "tuft",   7.5, "patch"),
    ("Deer",      (6.4, 4.0), 3.2, 2.8, "point",  "long", "stub",   6.0, "antler"),
    ("Elephant",  (8.4, 5.6), 0.8, 4.0, "wide",   "trunk","thin",   4.4, "none"),
    ("Hippo",     (8.4, 4.8), 0.6, 4.2, "round",  "snub", "stub",   2.6, "none"),
    ("Rhino",     (8.0, 4.8), 0.8, 3.6, "round",  "horn", "tuft",   3.0, "none"),
    ("Lion",      (7.0, 4.4), 1.2, 3.2, "round",  "flat", "tuft",   4.0, "mane"),
    ("Tiger",     (7.2, 4.2), 1.4, 3.2, "round",  "flat", "thin",   4.0, "stripe"),
    ("Monkey",    (4.8, 4.2), 1.0, 3.0, "round",  "flat", "hook",   3.0, "none"),
    ("Koala",     (5.2, 4.6), 0.4, 3.4, "fluff",  "snub", "stub",   2.4, "none"),
    ("Raccoon",   (5.8, 3.8), 1.0, 3.0, "round",  "point","ringed", 2.8, "mask"),
]

ANIMAL_COLOURS = [
    ("brown", "cream", "dark_brown"), ("dark_gray", "light_gray", "black"),
    ("orange", "cream", "dark_brown"), ("tan", "ivory", "brown"),
    ("black", "white", "dark_gray"), ("white", "light_gray", "dark_gray"),
    ("caramel", "cream", "rust"), ("silver", "white", "dark_gray"),
    ("rust", "peach", "dark_brown"), ("olive", "cream", "army_green"),
]
FIELD = ["light_green", "cream", "ivory", "sky_blue", "light_gray",
         "toothpaste", "banana", "light_lavender"]


def _draw_animal(g, spec, cx, cy, scale):
    (rx, ry), neck, head, ear, snout, tail, legs, mark = spec["parts"]
    main, belly, dark = spec["cols"]
    u = scale
    rx *= u; ry *= u; neck *= u; head *= u; legs *= u

    base = cy + ry + legs
    for i, lx in enumerate((-0.62, -0.34, 0.34, 0.62)):
        g.rect(cx + rx * lx - 1.1 * u, cy + ry * 0.4, cx + rx * lx + 1.1 * u, base,
               main if i % 2 else dark)
    g.ellipse(cx, cy, rx, ry, main)
    g.ellipse(cx, cy + ry * 0.42, rx * 0.72, ry * 0.42, belly)

    # The head has to clear the body. Placing it at the body's edge buried it,
    # and a buried head plus a snout drawn from the head centre produced
    # animals that read as headless lumps.
    hx = cx + rx * 0.9 + head * 0.75 + neck * 0.30
    hy = cy - ry * 0.55 - neck
    if neck > 0.8 * u:
        g.line(cx + rx * 0.55, cy - ry * 0.45, hx, hy + head * 0.6, main,
               t=max(1, head * 0.45))
    else:
        g.line(cx + rx * 0.5, cy - ry * 0.4, hx, hy, main, t=max(1, head * 0.55))
    g.disc(hx, hy, head, main)

    if snout == "long":
        g.ellipse(hx + head * 0.75, hy + head * 0.35, head * 0.62, head * 0.42, main)
        g.disc(hx + head * 1.25, hy + head * 0.35, head * 0.22, dark)
    elif snout == "point":
        g.poly([(hx + head * 0.3, hy - head * 0.3), (hx + head * 1.7, hy + head * 0.4),
                (hx + head * 0.3, hy + head * 0.7)], main)
        g.set(hx + head * 1.5, hy + head * 0.4, dark)
    elif snout == "snub":
        g.disc(hx + head * 0.8, hy + head * 0.35, head * 0.42, belly)
        g.set(hx + head * 0.9, hy + head * 0.3, dark)
    elif snout == "trunk":
        for k in range(9):
            t = k / 8.0
            g.disc(hx + head * (0.85 + 0.55 * t * t), hy + head * (0.1 + 2.3 * t),
                   head * (0.40 - 0.20 * t), main)
    elif snout == "horn":
        g.ellipse(hx + head * 0.7, hy + head * 0.35, head * 0.55, head * 0.4, main)
        g.poly([(hx + head * 1.1, hy + head * 0.1), (hx + head * 1.5, hy - head * 1.1),
                (hx + head * 1.45, hy + head * 0.3)], belly)
    else:   # flat
        g.disc(hx + head * 0.7, hy + head * 0.4, head * 0.34, belly)
        g.set(hx + head * 0.8, hy + head * 0.3, dark)

    # Ears sit ON the skull, one behind the other, at a spacing that scales
    # with the head - the first version put both at almost the same point.
    for sgn in (-1, 1):
        ex = hx + sgn * head * 0.48
        ey = hy - head * 0.72
        if ear == "point":
            g.poly([(ex - head * 0.42, ey + head * 0.42), (ex, ey - head * 0.85),
                    (ex + head * 0.42, ey + head * 0.42)], main)
        elif ear == "long":
            g.ellipse(ex + sgn * head * 0.12, ey - head * 0.85, head * 0.5, head * 1.25, main)
            g.ellipse(ex + sgn * head * 0.12, ey - head * 0.85, head * 0.26, head * 0.85, belly)
        elif ear == "flop":
            g.ellipse(ex, ey + head * 0.65, head * 0.42, head * 0.9, dark)
        elif ear == "round":
            g.disc(ex, ey, head * 0.5, main)
        elif ear == "wide":
            g.ellipse(hx - head * 0.55, hy, head * 0.9, head * 1.15, main)
            break
        elif ear == "fluff":
            g.disc(ex, ey + head * 0.25, head * 0.62, belly)

    bx = cx - rx
    if tail == "curl":
        for k in range(5):
            a = -0.6 - k * 0.7
            g.disc(bx - 1.4 * u + math.cos(a) * 2.6 * u, cy - 1 * u + math.sin(a) * 2.6 * u,
                   1.0 * u, main)
    elif tail == "up":
        g.line(bx, cy - 1 * u, bx - 2.4 * u, cy - 6 * u, main, t=1)
    elif tail == "bushy":
        g.ellipse(bx - 3 * u, cy + 0.6 * u, 3.4 * u, 2.1 * u, main)
        g.ellipse(bx - 4.8 * u, cy + 0.6 * u, 1.6 * u, 1.4 * u, belly)
    elif tail == "plume":
        # A squirrel's tail is a fat comma standing up behind it, not a slab.
        for k in range(6):
            a = 2.5 - k * 0.42
            g.disc(bx - 1.4 * u + math.cos(a) * 3.2 * u,
                   cy - 1.4 * u + math.sin(a) * 3.4 * u, (2.0 - k * 0.15) * u, main)
    elif tail == "puff":
        g.disc(bx - 1.6 * u, cy + 0.6 * u, 2.0 * u, belly)
    elif tail == "thin":
        g.line(bx, cy, bx - 3.4 * u, cy - 2.6 * u, dark, t=0)
    elif tail == "tuft":
        g.limb(bx, cy - 1 * u, bx - 3.4 * u, cy + 3.4 * u, dark)
        g.disc(bx - 3.8 * u, cy + 3.8 * u, 1.3 * u, dark)
    elif tail == "hook":
        for k in range(7):
            a = -1.4 + k * 0.5
            g.set(bx - 1 * u - math.cos(a) * 4 * u, cy - 2 * u + math.sin(a) * 4 * u, main)
    elif tail == "ringed":
        for k in range(4):
            g.disc(bx - (1.4 + k * 1.7) * u, cy - k * 0.9 * u, 1.5 * u,
                   main if k % 2 == 0 else dark)
    elif tail == "stub":
        g.disc(bx - 0.8 * u, cy - 0.4 * u, 1.4 * u, main)

    if mark == "stripe":
        for k in range(-2, 3):
            g.rect(cx + rx * k * 0.28 - 0.7 * u, cy - ry, cx + rx * k * 0.28 + 0.7 * u,
                   cy + ry * 0.2, dark)
    elif mark == "patch":
        g.ellipse(cx - rx * 0.35, cy - ry * 0.25, rx * 0.3, ry * 0.4, dark)
        g.ellipse(cx + rx * 0.3, cy + ry * 0.2, rx * 0.24, ry * 0.3, dark)
    elif mark == "panda":
        g.ellipse(cx - rx * 0.2, cy, rx * 0.55, ry * 0.9, dark)
        g.disc(hx - head * 0.3, hy - head * 0.1, head * 0.32, dark)
    elif mark == "spines":
        # Only over the back. Radiating them all the way round made a sun.
        for k in range(9):
            a = math.pi + k * math.pi / 10
            g.limb(cx + math.cos(a) * rx * 0.75, cy + math.sin(a) * ry * 0.75,
                   cx + math.cos(a) * (rx + 2.4 * u), cy + math.sin(a) * (ry + 2.4 * u),
                   dark)
    elif mark == "wool":
        for k in range(7):
            a = math.pi + k * math.pi / 6
            g.disc(cx + math.cos(a) * rx * 0.85, cy + math.sin(a) * ry * 0.85, 1.6 * u, belly)
    elif mark == "mane":
        g.ring(hx, hy, head + 2.2 * u, dark, t=2.2 * u)
    elif mark == "antler":
        for sgn in (-1, 1):
            g.limb(hx - head * 0.2, hy - head, hx + sgn * head * 0.8, hy - head * 2.6, belly)
            g.limb(hx + sgn * head * 0.8, hy - head * 2.6, hx + sgn * head * 1.5,
                   hy - head * 2.1, belly)
    elif mark == "mask":
        g.rect(hx - head * 0.4, hy - head * 0.35, hx + head * 0.9, hy + head * 0.15, dark)
    elif mark == "tip":
        g.disc(bx - 4.8 * u, cy + 0.6 * u, 1.5 * u, belly)

    _outline(g, "black" if main != "black" else "dark_gray", None)
    g.set(hx + head * 0.25, hy - head * 0.3, "white")
    g.set(hx + head * 0.25 + 1, hy - head * 0.3, "black")


def animals():
    specs = []
    poses = [("", 0.96, {}), (" Cub", 0.72, {}),
             (" Standing", 0.96, {"legs": 2.1}), (" Crouching", 0.96, {"legs": 0.3}),
             (" Grazing", 0.78, {"legs": 1.4, "neck": -0.6})]
    for pi, (suffix, sc, tw) in enumerate(poses):
        for si, (name, body, neck, head, ear, snout, tail, legs, mark) in enumerate(ANIMAL_SPECIES):
            specs.append(dict(
                name=f"{name}{suffix}",
                parts=(body, max(0.0, neck + tw.get("neck", 0)), head, ear, snout,
                       tail, legs * tw.get("legs", 1.0), mark),
                cols=ANIMAL_COLOURS[(si * 3 + pi) % len(ANIMAL_COLOURS)],
                bg=_pick_bg(ANIMAL_COLOURS[(si * 3 + pi) % len(ANIMAL_COLOURS)][0],
                            FIELD, si + pi),
                fill=sc, tags=["animal", name.lower()], scale=1.0))
    return _emit("animals", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_animal(g, s, x, y, k * s["scale"]),
                                   sp, sp["bg"]), 100)


GENERATORS["animals"] = animals
