"""Steamboat Willie, drawn bead by bead.

COPYRIGHT NOTE - read before adding anything here.

The 1928 short *Steamboat Willie* entered the United States public domain on
1 January 2024, and with it that specific 1928 depiction: black and white,
pie-cut eyes, no gloves, oversized shoes, the boat with its twin funnels.
Everything here is held to that version. What is NOT public domain, and must
never be drawn here, is the modern character - colour clothes, white gloves,
jointed limbs, expressive pupils - and the name "Mickey Mouse" remains a live
trademark, so these are titled after the short and never after him.

Three patterns, not thirty. An earlier attempt built a whole cast of poses out
of parametric parts run through an auto-fit, and every one of them came out
unreadable: the boat was a wedding cake, the wheel an asterisk, the standing
figure a black blob with a face. The lesson is in the numbers. The head needs a
radius of 8 beads before its face has room for two eyes, a nose and a grin -
that is a 21-bead-tall subject, most of a 28x28 board - so a full-length figure
on the same board gets a 6-bead head, and a 6-bead head has no face. There is
exactly one good Willie at this size, so that is what ships, alongside the boat
and the wheel he stands at.

Everything is drawn on explicit coordinates and then mirrored, rather than
scaled to fit. A subject like this is read from its proportions, and float
coordinates through an auto-fit do not land where a 28-bead board needs them.
"""
import math

from beadlib import make_pattern, stable_id
from canvas import Grid

S = 28
MID = (S - 1) / 2.0        # 13.5, the board's own centre line

INK = "black"
HULL = "dark_gray"
PALE = "cream"
WATER = "blue"

# Cream, not white: on a board with no backdrop a white bead is the same pale
# grey as an empty peg, so white steam would read as no steam at all.
STEAM = PALE


def _blank():
    return [[None] * S for _ in range(S)]


def _disc(g, cx, cy, r, cid):
    for y in range(S):
        for x in range(S):
            if math.hypot(x - cx, y - cy) <= r:
                g[y][x] = cid


def _ell(g, cx, cy, rx, ry, cid, only=False):
    """Filled ellipse. With `only`, paints solely over beads of that colour -
    which is how the pale face patch stays inside the black head instead of
    bulging out of it."""
    for y in range(S):
        for x in range(S):
            if only is not False and g[y][x] != only:
                continue
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                g[y][x] = cid


def _rect(g, x0, y0, x1, y1, cid):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if 0 <= x < S and 0 <= y < S:
                g[y][x] = cid


def _mirror(g):
    """Left half wins. Every shape here is placed symmetrically already; this
    is the guarantee, so no rounding difference can leave one ear a bead wider
    than the other."""
    for y in range(S):
        for x in range(S // 2):
            g[y][S - 1 - x] = g[y][x]


def _grid(cells):
    g = Grid(S, S)
    for y in range(S):
        for x in range(S):
            if cells[y][x] is not None:
                g.set(x, y, cells[y][x])
    return g


# ── the head ────────────────────────────────────────────────────────────────

def head():
    """The three-circle silhouette, with room for an actual face inside it.

    The radii are not arbitrary. Ears at 4.3 and a head at 8.0, centred 7.5
    apart, is the largest arrangement that still leaves a valley between each
    ear and the skull - push the ears out and it reads as a bat, pull them in
    and the whole top of the head is one flat black bar.
    """
    g = _blank()
    _disc(g, MID - 7.5, 7.0, 4.3, INK)
    _disc(g, MID + 7.5, 7.0, 4.3, INK)
    _disc(g, MID, 16.0, 8.0, INK)
    _ell(g, MID, 17.8, 7.2, 6.5, PALE, only=INK)      # the face mask
    for s in (-1, 1):
        _ell(g, MID + s * 3.0, 15.2, 1.4, 1.7, INK)   # eyes
    _ell(g, MID, 18.8, 1.7, 1.2, INK)                 # nose
    _rect(g, 10, 21, 17, 21, INK)                     # grin
    for x in (9, 18):
        g[20][x] = INK                                # corners, turned up
    _mirror(g)
    return _grid(g)


# ── the boat ────────────────────────────────────────────────────────────────
#
#   K black   D hull   C deck   B water   . empty
# Rows 0-7 are left to build(): the funnels are placed there, and their number
# is the only thing that makes one boat structurally different from another.
BOAT_ART = [
    "......KKKKKKKKKKKKKKKK......",
    "......KCCCCCCCCCCCCCCK......",
    "......KCKKCCCKKCCCKKCK......",
    "......KCKKCCCKKCCCKKCK......",
    "......KCCCCCCCCCCCCCCK......",
    "...KKKKKKKKKKKKKKKKKKKKKK...",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "..KDCCCCCCCCCCCCCCCCCCCCDK..",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "..KDDDDDDDDDDDDDDDDDDDDDDK..",
    "...KDDDDDDDDDDDDDDDDDDDDK...",
    "....KKDDDDDDDDDDDDDDDDKK....",
    "......KKKKKKKKKKKKKKKK......",
    "..BBBBBBBBBBBBBBBBBBBBBBBB..",
    "..BBBBBBBBBBBBBBBBBBBBBBBB..",
]
ART_TOP = 8


def boat():
    g = _blank()
    paint = {"K": INK, "D": HULL, "C": PALE, "B": WATER}
    for y, row in enumerate(BOAT_ART):
        for x, ch in enumerate(row):
            if ch != ".":
                g[ART_TOP + y][x] = paint[ch]
    for x0, x1 in ((9, 11), (16, 18)):
        for x in range(x0, x1 + 1):
            for y in range(3, ART_TOP):
                g[y][x] = INK
            g[5][x] = PALE                            # the funnel's band
        for x in range(x0 - 1, x1 + 2):               # steam, resting on the rim
            g[1][x] = STEAM
            g[2][x] = STEAM
    _mirror(g)
    return _grid(g)


# ── the wheel ───────────────────────────────────────────────────────────────

def wheel():
    """The pilot's wheel, on doubled coordinates.

    Working in dx = 2x - 27 instead of x - 13.5 is the whole trick: a bead's
    doubled coordinate is always an odd integer, so a shape defined by |dx| is
    symmetric bead-for-bead with no rounding to disagree about. The float
    version came out lopsided and read as an asterisk.
    """
    g = _blank()
    for y in range(S):
        for x in range(S):
            dx, dy = 2 * x - (S - 1), 2 * y - (S - 1)
            d = math.hypot(dx, dy) / 2.0
            arm = abs(dx) <= 1 or abs(dy) <= 1 or abs(abs(dx) - abs(dy)) <= 1
            if d <= 3.0 or 8.0 <= d <= 10.2:
                g[y][x] = HULL
            elif arm and (d < 8.0 or d <= 12.4):
                g[y][x] = HULL
    return _grid(g)


# ── the small board, drawn rather than reduced ──────────────────────────────
#
# The box-majority reduction is right for 2,600 patterns and wrong for this
# one. At 15x15 the grin is three beads long: the resampler kept the two turned
# up corners, lost the bar between them, and what was left read as a frown. A
# face has no margin for a bead going missing, so the hero board is drawn at
# the small size too.
#
#   K black   C cream (the face)   . empty
HEAD_SMALL = [
    "...............",
    ".KKK.......KKK.",
    ".KKKKK...KKKKK.",
    ".KKKKK...KKKKK.",
    "..KKKKKKKKKKK..",
    "..KKCCCCCCCKK..",
    "..KCCKCCCKCCK..",
    "..KCCKCCCKCCK..",
    "..KCCCCCCCCCK..",
    "..KCCCKKKCCCK..",
    "...CCCCCCCCC...",
    "...CKCCCCCKC...",
    "...CCKKKKKCC...",
    "....CCCCCCC....",
    "...............",
]


def _art_grid(art):
    paint = {"K": INK, "C": PALE}
    return [[paint.get(ch) for ch in row] for row in art]


DESIGNS = [
    ("Steamboat Willie", head, ["mouse", "cartoon", "retro"]),
    ("Willie's Steamboat", boat, ["boat", "cartoon", "retro"]),
    ("Willie's Wheel", wheel, ["wheel", "cartoon", "retro"]),
]


# Hand-drawn boards for sizes the reducer cannot do justice to. build_manifest
# uses these verbatim and reduces everything else as usual.
HAND_SIZES = {"Steamboat Willie": {"small": HEAD_SMALL}}


def generate(category="videogame"):
    out = []
    for name, build, tags in DESIGNS:
        g = build()
        p = make_pattern(stable_id(category, name), name, category,
                         g.w, g.h, g.cells(), tags + [category])
        art = HAND_SIZES.get(name)
        if art:
            p["sizeArt"] = {k: _art_grid(v) for k, v in art.items()}
        out.append(p)
    return out
