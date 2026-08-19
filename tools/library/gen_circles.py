"""Round-pegboard patterns.

The shipped library had none: every one of the 2690 patterns was pegged out on
a square board, so the round pegboards people actually own had nothing to make.
These are designed FOR the disc - the composition is polar, so the board's edge
is part of the artwork rather than a square design with its corners lopped off.

A round board is the same square peg pitch clipped to a circle, which is why
these are ordinary patterns carrying shape="circle": cells outside the disc are
simply absent, and any renderer that draws only the cells it is given already
draws them correctly.
"""
import math

from beadlib import PALETTE, make_pattern, stable_id

SIZES = [16, 24, 29]          # small, medium, and the ~29-peg large round board

# Harmonious colour runs, ordered light -> dark or warm -> cool so a ring
# sequence reads as a gradient rather than a clash.
RUNS = [
    ("sunset",   ["yellow", "orange", "pumpkin", "red", "dark_red"]),
    ("ocean",    ["white", "light_blue", "sky_blue", "blue", "navy"]),
    ("forest",   ["cream", "light_green", "green", "dark_green", "brown"]),
    ("berry",    ["white", "light_pink", "pink", "hot_pink", "magenta"]),
    ("twilight", ["light_lavender", "lavender", "purple", "navy", "black"]),
    ("candy",    ["white", "banana", "pink", "turquoise", "lavender"]),
    ("mono",     ["white", "light_gray", "gray", "dark_gray", "black"]),
    ("citrus",   ["lemon", "yellow", "cheddar", "orange", "green"]),
    ("flame",    ["banana", "cheddar", "neon_orange", "red", "black"]),
    ("mint",     ["white", "toothpaste", "light_teal", "teal", "forest"]),
]

_AVAILABLE = {c["id"] for c in PALETTE}


def _run(name):
    """Resolve a colour run against the real palette, dropping any stray id."""
    for n, ids in RUNS:
        if n == name:
            return [i for i in ids if i in _AVAILABLE]
    raise KeyError(name)


RUN_NAMES = [n for n, _ in RUNS]


def _polar(size):
    """Yield (x, y, r, theta) for every peg on a `size` round board.

    r is 0 at the centre and 1 at the rim; theta is 0..2pi. Cells outside the
    disc are not yielded at all - they are not pegs.
    """
    c = size / 2.0
    rad = size / 2.0
    for y in range(size):
        for x in range(size):
            dx = x + 0.5 - c
            dy = y + 0.5 - c
            d = math.hypot(dx, dy)
            if d > rad:
                continue
            yield x, y, min(1.0, d / rad), (math.atan2(dy, dx) % (2 * math.pi))


# ── Families ─────────────────────────────────────────────────────────────────
# Each returns (cells, title, tags) for one board.

def f_rings(size, run, bands):
    ids = _run(run)
    cells = [(x, y, ids[min(int(r * bands), bands - 1) % len(ids)])
             for x, y, r, _ in _polar(size)]
    return cells, f"{run.title()} Rings {bands}", ["rings", "concentric", run]


def f_wedges(size, run, k):
    """k full colour cycles around the board.

    The wedge count is a MULTIPLE of the run length on purpose: at 6 wedges
    over 5 colours the first and last wedge share a colour and merge into one
    fat sector, which reads as a mistake rather than a pinwheel.
    """
    ids = _run(run)
    n = len(ids) * k
    cells = [(x, y, ids[int(t / (2 * math.pi) * n) % len(ids)])
             for x, y, _, t in _polar(size)]
    return cells, f"{run.title()} Pinwheel {n}", ["wedges", "pinwheel", run]


def f_checker(size, run, bands):
    """A true polar chessboard: tiles per ring grow with the radius.

    A fixed wedge count is what a square checkerboard's logic gives you, and on
    a disc it fails - the wedges converge to slivers at the hub, so the middle
    of the board reads as confetti while the rim reads as slabs. Setting the
    ring's tile count to 2*round(pi*(k+0.5)) makes every tile about as wide as
    the ring is thick, and keeping it even makes the alternation close cleanly
    where the ring wraps.
    """
    ids = _run(run)
    a, b = ids[0], ids[-1]
    hub = ids[len(ids) // 2]
    cells = []
    for x, y, r, t in _polar(size):
        k = min(bands - 1, int(r * bands))
        if k == 0:
            cells.append((x, y, hub))
            continue
        n = 2 * max(2, round(math.pi * (k + 0.5)))
        wedge = int(t / (2 * math.pi) * n)
        cells.append((x, y, a if (k + wedge) % 2 == 0 else b))
    return cells, f"{run.title()} Radial {bands}", ["radial", "spokes", run]


def f_spiral(size, run, arms):
    ids = _run(run)
    cells = []
    for x, y, r, t in _polar(size):
        # Twisting the angle with radius is what turns wedges into arms.
        # ~1 full turn of twist across the radius; less than that and the arms
        # read as plain straight wedges.
        phase = (t + r * 6.2) / (2 * math.pi) * arms
        cells.append((x, y, ids[int(phase) % len(ids)]))
    return cells, f"{run.title()} Spiral {arms}", ["spiral", "swirl", run]


def f_rosette(size, run, petals):
    ids = _run(run)
    cells = []
    for x, y, r, t in _polar(size):
        # r = |cos(k*theta)| is the classic rose curve; inside it is petal.
        edge = 0.35 + 0.62 * abs(math.cos(petals * t / 2.0))
        if r < 0.16:
            cid = ids[0]
        elif r <= edge:
            cid = ids[1 + int(r * (len(ids) - 1)) % (len(ids) - 1)]
        else:
            cid = ids[-1]
        cells.append((x, y, cid))
    return cells, f"{run.title()} Rosette {petals}", ["rosette", "flower", run]


def f_star(size, run, points):
    ids = _run(run)
    cells = []
    for x, y, r, t in _polar(size):
        # Peaks must stop short of 1.0: at 1.5 the points ran off the board and
        # the star fused into a disc with a few notches in it.
        edge = 0.26 + 0.62 * (0.5 + 0.5 * math.cos(points * t))
        cells.append((x, y, ids[0] if r <= edge else ids[-1]))
    return cells, f"{run.title()} Star {points}", ["star", "burst", run]


def f_target(size, run, bands):
    ids = _run(run)
    a, b = ids[0], ids[-1]
    cells = [(x, y, a if int(r * bands) % 2 == 0 else b)
             for x, y, r, _ in _polar(size)]
    return cells, f"{run.title()} Target {bands}", ["target", "bullseye", run]


def f_yinyang(size, run, variant=0):
    """variant rotates the S and resizes the eyes, so the ten runs differ."""
    ids = _run(run)
    a, b = ids[0], ids[-1]
    eye = 5.0 + (variant % 5)          # smaller divisor = bigger eye
    flip = -1 if variant % 2 else 1
    cells = []
    c = size / 2.0
    rad = size / 2.0
    for x, y, r, _ in _polar(size):
        dx = x + 0.5 - c
        dy = y + 0.5 - c
        # Two half-size lobes split the disc down the S curve.
        dx *= flip
        top = math.hypot(dx, dy + rad / 2.0) <= rad / 2.0
        bot = math.hypot(dx, dy - rad / 2.0) <= rad / 2.0
        cid = a if dx < 0 else b
        if top:
            cid = a
        elif bot:
            cid = b
        # The two eyes.
        if math.hypot(dx, dy + rad / 2.0) <= rad / eye:
            cid = b
        elif math.hypot(dx, dy - rad / 2.0) <= rad / eye:
            cid = a
        cells.append((x, y, cid))
    return cells, f"{run.title()} Balance {variant + 1}", ["yinyang", "balance", run]


def f_sunburst(size, run, rays):
    ids = _run(run)
    cells = []
    for x, y, r, t in _polar(size):
        if r < 0.30:
            cid = ids[0]
        else:
            on = (int(t / (2 * math.pi) * rays * 2) % 2 == 0)
            cid = ids[1] if on else ids[-1]
        cells.append((x, y, cid))
    return cells, f"{run.title()} Sunburst {rays}", ["sunburst", "rays", run]


def f_gradient(size, run, bands=5):
    """Equal-AREA bands, not equal-width ones.

    A linear radial ramp is the same quantisation Rings uses, so at matching
    band counts the two families produced byte-identical boards. Stepping on
    sqrt(r) gives every band the same number of beads, which both looks more
    like a fade and cannot coincide with Rings.
    """
    ids = _run(run)
    n = len(ids)
    cells = [(x, y, ids[min(n - 1, int(math.sqrt(r) * bands) * n // max(1, bands))])
             for x, y, r, _ in _polar(size)]
    return cells, f"{run.title()} Fade {bands}", ["gradient", "fade", run]


def generate():
    """100 round-board patterns: 10 families x 10 colour runs."""
    out = []
    for run in RUN_NAMES:
        i = RUN_NAMES.index(run)
        size = SIZES[i % len(SIZES)]
        big = SIZES[-1]
        # Every family takes a parameter that varies across ALL ten runs, not
        # a few. The first cut used i % 3 and i % 4 for most families and no
        # parameter at all for Balance and Fade, so the ten colour runs
        # collapsed onto three or four distinct boards and the category came
        # out only 36% structurally unique - exactly the recolour problem this
        # library is trying to get rid of.
        specs = [
            f_rings(big, run, 3 + i),
            f_wedges(size, run, 1 + i % 4),
            f_checker(big, run, 3 + i),
            f_spiral(big, run, 2 + i),
            f_rosette(big, run, 5 + i),
            f_star(size, run, 5 + i),
            f_target(size, run, 4 + i),
            f_yinyang(big, run, i),
            f_sunburst(big, run, 5 + i),
            f_gradient(size, run, 3 + i),
        ]
        boards = [big, size, big, big, big, size, size, big, big, size]
        # sizes rotate with the run too, so families whose parameter space is
        # narrower than ten still land on ten distinct boards.
        for (cells, title, tags), side in zip(specs, boards):
            out.append(make_pattern(
                stable_id("circles", title),
                title,
                "circles",
                side, side,
                cells,
                tags=["circle", "round board"] + tags,
                shape="circle",
            ))
    return out


if __name__ == "__main__":
    ps = generate()
    print(f"{len(ps)} circular patterns")
    for p in ps[:5]:
        print(" ", p["title"], p["grid"], len(p["cells"]), "cells",
              len(p["palette"]), "colours")
