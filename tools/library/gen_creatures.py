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
from uniqueness import signature

S = 28          # board side for every design here


# ── helpers ──────────────────────────────────────────────────────────────────

def _emit(cat, specs, build, target=100):
    """Build each spec, drop structural duplicates, keep `target`."""
    out, seen = [], set()
    for i, spec in enumerate(specs):
        g = build(spec)
        pat = make_pattern(stable_id(cat, f"{spec['name']}-{i}"), spec["name"], cat,
                           g.w, g.h, g.cells(), spec.get("tags", []) + [cat])
        sig = signature(pat)
        if sig in seen:
            continue
        seen.add(sig)
        out.append(pat)
        if len(out) >= target:
            break
    return out


BIG = 60          # working canvas; the subject is auto-framed down onto S x S


def _frame(draw, spec, bg, size=S, margin=1):
    """Draw on a roomy canvas, then centre the ink on the real board.

    Composing a subject from parts makes its extent hard to predict - a heron
    with a long neck and long legs is twice the height of a wren - so the first
    version of this clipped tails and beaks off the edge and left the subject
    sitting wherever the maths happened to put it. Drawing big and framing
    afterwards means every design is centred and whole, and a subject too large
    for the board is redrawn smaller rather than cropped.
    """
    for attempt in range(6):
        scale = 1.0 - attempt * 0.10
        g = Grid(BIG, BIG)
        g.fill(None)
        draw(g, spec, BIG / 2.0, BIG / 2.0, scale)
        xs = [x for y in range(BIG) for x in range(BIG) if g.g[y][x] is not None]
        ys = [y for y in range(BIG) for x in range(BIG) if g.g[y][x] is not None]
        if not xs:
            break
        w = max(xs) - min(xs) + 1
        h = max(ys) - min(ys) + 1
        if w <= size - 2 * margin and h <= size - 2 * margin:
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
    """One-bead dark edge wherever a filled cell touches background."""
    edge = []
    for y in range(g.h):
        for x in range(g.w):
            if g.g[y][x] in (None, bg):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if not g.inb(x + dx, y + dy) or g.g[y + dy][x + dx] in (None, bg):
                    edge.append((x, y))
                    break
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
            g.line(cx + off, cy + ry - 1, cx + off * 0.6, cy + ry + legs, bill)
            g.line(cx + off * 0.6, cy + ry + legs, cx + off * 0.6 + 1.8,
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
            g.line(bx, cy + 1, bx - 10 * scale, ty, belly)
            g.disc(bx - 10 * scale, ty, 1.6 * scale, main)
    elif tail == "plume":
        for k in range(3):
            g.line(bx + 1, cy - 1, bx - (5 + k) * scale,
                   cy - 6 * scale + k * 2.4 * scale, main, t=1)

    if wing == "folded":
        # The wing reads as a wing because of its EDGE, so it is drawn as a
        # shade of the body rather than in the beak colour - an orange wing
        # patch on a purple bird just looked like a mistake.
        g.ellipse(cx - rx * 0.15, cy + 0.4, rx * 0.58, ry * 0.46, wingc)
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
        g.line(tipx - 1, hy, tipx + 7 * scale, hy - 1, bill)
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
    poses = [("", {}), (" Perched", {"legs": +1}), (" Calling", {"head": +0.6}),
             (" Fledgling", {"scale": 0.78}), (" Alert", {"neck": +2.0})]
    for si, (name, body, neck, head, beak, tail, legs, crest, wing) in enumerate(BIRD_SPECIES):
        for pi, (suffix, tweak) in enumerate(poses):
            sc = tweak.get("scale", 1.0)
            parts = ((body[0] * sc, body[1] * sc),
                     max(0.0, neck * sc + tweak.get("neck", 0)),
                     head * sc + tweak.get("head", 0),
                     beak, tail,
                     max(0, int(legs * sc) + tweak.get("legs", 0)), crest, wing)
            specs.append(dict(
                name=f"{name}{suffix}", parts=parts,
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
    poses = [("", 1.0, {}), (" Young", 0.76, {}), (" Large", 1.14, {}),
             (" Finned", 1.0, {"dorsal": 0.9, "ventral": 0.8}),
             (" Sleek", 1.0, {"dorsal": -0.35, "ventral": -0.3})]
    for si, (name, body, tail, dor, ven, snout, stripe) in enumerate(FISH_SPECIES):
        for pi, (suffix, sc, tw) in enumerate(poses):
            specs.append(dict(
                name=f"{name}{suffix}",
                parts=((body[0], body[1]),
                       tail,
                       max(0.0, dor + tw.get("dorsal", 0)),
                       max(0.0, ven + tw.get("ventral", 0)),
                       snout, stripe),
                cols=FISH_COLOURS[(si * 3 + pi) % len(FISH_COLOURS)],
                bg=_pick_bg(FISH_COLOURS[(si * 3 + pi) % len(FISH_COLOURS)][0], WATER, si + pi),
                tags=["fish", name.lower()], scale=sc))
    return _emit("fish", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_fish(g, s, x, y, k * s["scale"]),
                                   sp, sp["bg"]), 100)


# ── BUGS ─────────────────────────────────────────────────────────────────────

BUG_SPECIES = [
    # name          plan        wings   legs segs antennae extras
    ("Ladybug",     "beetle",   0,      6,  1,  2, "spots"),
    ("Beetle",      "beetle",   0,      6,  1,  2, "split"),
    ("Stag Beetle", "beetle",   0,      6,  1,  2, "horns"),
    ("Butterfly",   "flier",    2,      6,  3,  2, "wingdot"),
    ("Moth",        "flier",    2,      6,  3,  2, "furry"),
    ("Dragonfly",   "flier",    4,      6,  5,  2, "long"),
    ("Bee",         "flier",    2,      6,  3,  2, "bands"),
    ("Wasp",        "flier",    2,      6,  4,  2, "waist"),
    ("Ant",         "walker",   0,      6,  3,  2, "none"),
    ("Grasshopper", "walker",   0,      6,  2,  2, "jump"),
    ("Cricket",     "walker",   0,      6,  2,  2, "jump"),
    ("Mantis",      "walker",   0,      6,  3,  2, "claws"),
    ("Caterpillar", "crawler",  0,      8,  7,  2, "none"),
    ("Centipede",   "crawler",  0,     14, 10,  2, "none"),
    ("Spider",      "spider",   0,      8,  2,  0, "none"),
    ("Scorpion",    "spider",   0,      8,  4,  0, "sting"),
    ("Snail",       "snail",    0,      0,  1,  2, "shell"),
    ("Firefly",     "flier",    2,      6,  3,  2, "glow"),
    ("Cicada",      "flier",    2,      6,  2,  2, "none"),
    ("Weevil",      "beetle",   0,      6,  1,  2, "snout"),
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
    plan, wings, legs, segs, ants, extra = spec["parts"]
    main, accent, hi = spec["cols"]
    u = scale

    if plan in ("beetle", "flier", "walker"):
        bl = 7 * u if plan != "walker" else 8 * u
        bw = 4.6 * u if plan == "beetle" else 3.2 * u
        for i in range(legs // 2):
            ly = cy - bl * 0.4 + i * bl * 0.55
            for sgn in (-1, 1):
                g.line(cx + sgn * bw * 0.6, ly, cx + sgn * (bw + 4 * u),
                       ly + (2.4 * u if plan != "walker" else 3.6 * u), accent)
        if wings:
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
                g.line(cx + sgn * 1.4 * u, cy - bl - 2 * u,
                       cx + sgn * 4 * u, cy - bl - 6 * u, accent)
        elif extra == "wingdot":
            for sgn in (-1, 1):
                g.disc(cx + sgn * bw * 1.8, cy - bl * 0.35, 1.5 * u, accent)
                g.disc(cx + sgn * bw * 1.3, cy + bl * 0.2, 1.1 * u, main)
        elif extra == "glow":
            g.ellipse(cx, cy + bl * 0.7, bw * 0.8, bl * 0.3, hi)
        elif extra == "waist":
            g.ellipse(cx, cy + bl * 0.15, bw * 0.35, bl * 0.12, None)
        elif extra == "snout":
            g.line(cx, cy - bl - 3 * u, cx, cy - bl - 6 * u, accent)
        elif extra == "claws":
            for sgn in (-1, 1):
                g.line(cx + sgn * bw, cy - bl * 0.6, cx + sgn * (bw + 4 * u), cy - bl * 1.2, accent)
        elif extra == "jump":
            for sgn in (-1, 1):
                g.line(cx + sgn * bw * 0.7, cy + bl * 0.2, cx + sgn * (bw + 3 * u), cy - bl * 0.4, accent)
                g.line(cx + sgn * (bw + 3 * u), cy - bl * 0.4, cx + sgn * (bw + 5 * u), cy + bl * 0.6, accent)
        hy = cy - bl - 1.2 * u
    elif plan == "crawler":
        for i in range(segs):
            sx = cx - (segs - 1) * 1.9 * u / 2 + i * 1.9 * u
            g.disc(sx, cy + math.sin(i * 0.9) * 1.4 * u, 2.2 * u, main if i else accent)
            if i % 2 == 0:
                g.line(sx, cy + 2 * u, sx, cy + 5 * u, accent)
        hy = cy - 2 * u
    elif plan == "spider":
        g.ellipse(cx, cy + 2 * u, 4.0 * u, 4.6 * u, main)
        g.disc(cx, cy - 2.6 * u, 2.6 * u, accent)
        for i in range(4):
            for sgn in (-1, 1):
                a = -0.9 + i * 0.55
                g.line(cx + sgn * 2 * u, cy + 1 * u,
                       cx + sgn * (4 + 6 * math.cos(a)) * u, cy + 1 * u + 7 * math.sin(a) * u, accent)
        if extra == "sting":
            g.line(cx, cy + 6 * u, cx + 7 * u, cy + 1 * u, accent)
            g.disc(cx + 7.6 * u, cy + 0.4 * u, 1.4 * u, hi)
        hy = cy - 2.6 * u
    else:   # snail
        g.ellipse(cx - 1.5 * u, cy + 3.4 * u, 6.5 * u, 2.2 * u, accent)
        for k in range(4):
            g.ring(cx + 1.5 * u, cy, (6.2 - k * 1.5) * u, main if k % 2 == 0 else hi, t=1.4 * u)
        hy = cy + 1.5 * u
        cx = cx - 6 * u

    for k in range(ants):
        sgn = -1 if k == 0 else 1
        g.line(cx + sgn * 1.2 * u, hy - 1.4 * u, cx + sgn * 4.4 * u, hy - 6 * u, accent)
    _outline(g, "black" if main != "black" else "dark_gray", None)
    for sgn in (-1, 1):
        g.set(cx + sgn * 1.1 * u, hy - 0.4 * u, hi)


def bugs():
    specs = []
    # Variants have to change the DRAWING, not just a field the plan ignores.
    # A "Winged" spider is still a spider, so the first cut lost a third of the
    # category to structural collisions; leg count and segment count move
    # something in every plan.
    poses = [("", 1.0, {}), (" Small", 0.74, {}), (" Large", 1.18, {}),
             (" Long", 1.0, {"segs": +2, "legs": +2}),
             (" Slender", 0.9, {"segs": +1, "legs": -2})]
    for si, (name, plan, wings, legs, segs, ants, extra) in enumerate(BUG_SPECIES):
        for pi, (suffix, sc, tw) in enumerate(poses):
            w2 = wings + tw.get("wings", 0) if plan == "flier" else wings
            specs.append(dict(
                name=f"{name}{suffix}",
                parts=(plan, w2, max(4, legs + tw.get("legs", 0)),
                       max(1, segs + tw.get("segs", 0)), ants, extra),
                cols=BUG_COLOURS[(si * 7 + pi) % len(BUG_COLOURS)],
                bg=_pick_bg(BUG_COLOURS[(si * 7 + pi) % len(BUG_COLOURS)][0], LEAF, si + pi),
                tags=["bug", name.lower()], scale=sc))
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
            g.line(cx + k * 2.4 * u, top - 2 * u, cx + k * 2.6 * u, top + 5 * u, leaf2)
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
                    g.line(cx + sgn * tw, yy, cx + sgn * 6 * u, yy - 3.4 * u, leaf)
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
    poses = [("", 1.0, {}), (" Sapling", 0.7, {}), (" Old", 1.16, {}),
             (" Tall", 1.0, {"trunk": 1.5}), (" Squat", 1.0, {"trunk": 0.6})]
    for si, (name, crown, tiers, trunk, branch, extra) in enumerate(TREE_SPECIES):
        for pi, (suffix, sc, tw) in enumerate(poses):
            tr = (trunk[0], trunk[1] * tw.get("trunk", 1.0))
            specs.append(dict(
                name=f"{name}{suffix}", parts=(crown, tiers, tr, branch, extra),
                cols=TREE_COLOURS[(si * 3 + pi) % len(TREE_COLOURS)],
                bg=_pick_bg(TREE_COLOURS[(si * 3 + pi) % len(TREE_COLOURS)][0], SKY, si + pi),
                tags=["tree", name.lower()], scale=sc))
    return _emit("trees", specs,
                 lambda sp: _frame(lambda g, s, x, y, k: _draw_tree(g, s, x, y, k * s["scale"]),
                                   sp, sp["bg"]), 100)


GENERATORS.update({"fish": fish, "bugs": bugs, "trees": trees})


if __name__ == "__main__":
    for cat, fn in GENERATORS.items():
        ps = fn()
        print(f"{cat:8s} {len(ps):3d} patterns, "
              f"{len({signature(p) for p in ps}):3d} structurally unique")
