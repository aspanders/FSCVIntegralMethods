"""Small and medium versions of every pattern.

A 29x29 design is a real afternoon's work and a whole large pegboard. Plenty of
makers want the same subject at a size they can finish in twenty minutes, or on
the small square board they actually own, so every shipped pattern carries two
reduced versions alongside its full-size one.

The reduction is a box-majority resample, not a nearest-neighbour pick: each
output bead looks at the block of input beads it covers and takes the colour
that occupies most of it, and comes out empty only when the block is more than
half empty. Nearest-neighbour at 0.55x drops every second row, which deletes
one-bead outlines, antennae and pupils - exactly the features that make a small
pattern readable.

Reducing then breaks things that the full-size pattern got right, so each
reduced grid goes back through the same repair the full-size one did: weld the
loose parts, widen the load-bearing necks, and re-impose symmetry on anything
that was symmetric before. A small version that cannot be built is worse than
no small version.
"""
from connectivity import (best_axis, components, make_buildable, symmetrize,
                          thicken_necks)

# Fractions of the pattern's own board, not absolute sizes: a 16x16 icon and a
# 29x29 mandala should both come out meaningfully smaller, and pinning small to
# a fixed 14 would make the icon LARGER.
SIZES = {"small": 0.52, "medium": 0.76}

# Below this the subject stops being a subject. A 9-bead-wide board holds a
# heart or a letter and nothing else, so a pattern that would reduce past it is
# simply not offered at that size.
MIN_SIDE = 11

# Empty pegs kept between the subject and the edge of the reduced board.
#
# The reduction scales the WHOLE board, margin included, so a full-size design
# sitting one bead in from the edge came out at 0.52 with 0.52 of a bead of
# margin - which rounds to none. Every small and medium letter and heart in the
# library ran into all four edges. That is not a cosmetic complaint: a bead on
# the outermost peg has nothing to hold it on three sides while you iron it,
# the design cannot be given a border, and on a board whose exact peg count
# varies by brand it is the first thing to not fit.
MARGIN = 1

# Below this a reduced board is not the subject any more, it is a few beads.
# The inset costs a ring of pegs, and for the very thinnest subjects - a "1" at
# the Small style is a one-bead stem - that ring is the difference between a
# readable glyph and eight beads. Those fall back to the full board rather than
# lose the variant.
MIN_BEADS = 12


def resample(g, w, h, nw, nh):
    """Box-majority reduction of a bead grid onto an nw x nh board."""
    out = [[None] * nw for _ in range(nh)]
    for ny in range(nh):
        y0 = ny * h // nh
        y1 = max(y0 + 1, (ny + 1) * h // nh)
        for nx in range(nw):
            x0 = nx * w // nw
            x1 = max(x0 + 1, (nx + 1) * w // nw)
            counts = {}
            total = 0
            for y in range(y0, y1):
                for x in range(x0, x1):
                    total += 1
                    c = g[y][x]
                    if c is not None:
                        counts[c] = counts.get(c, 0) + 1
            filled = sum(counts.values())
            # A block that is half beads keeps its bead. Requiring a strict
            # majority erodes every silhouette by one bead per reduction, and
            # at 0.52 that is most of a thin subject.
            if filled * 2 >= total and counts:
                out[ny][nx] = max(counts.items(), key=lambda kv: kv[1])[0]
    return out


def _pad(inner, iw, ih, nw, nh):
    """Centre an iw x ih grid on an empty nw x nh board."""
    ox, oy = (nw - iw) // 2, (nh - ih) // 2
    out = [[None] * nw for _ in range(nh)]
    for y in range(ih):
        for x in range(iw):
            out[y + oy][x + ox] = inner[y][x]
    return out


def reduce_grid(g, w, h, frac, mirror=None, repair=True, margin=MARGIN):
    """A smaller, still-buildable copy of `g`. Returns (grid, nw, nh) or None.

    The subject is resampled onto a board `margin` pegs smaller on every side
    and then centred on the real one, so the reduction cannot push it into the
    edge. The inner size is derived from ONE scale factor rather than by
    shrinking each axis independently: doing it per-axis stretches anything
    that is not square, and a squashed heart is worse than a cramped one.

    `margin` is 0 for a board that is meant to be full - a design with a
    background is not a subject sitting on a board, it IS the board, and
    ringing it with empty pegs would just look like a mistake.
    """
    nw, nh = max(1, round(w * frac)), max(1, round(h * frac))
    if nw < MIN_SIDE or nh < MIN_SIDE or (nw >= w and nh >= h):
        return None
    if margin:
        inner = min((nw - 2 * margin) / float(w), (nh - 2 * margin) / float(h))
        iw, ih = max(1, round(w * inner)), max(1, round(h * inner))
    else:
        iw, ih = nw, nh
    small = resample(g, w, h, iw, ih)
    if not any(c is not None for row in small for c in row):
        return None
    if repair:
        if mirror:
            symmetrize(small, iw, ih)
        make_buildable(small, iw, ih)
        if mirror:
            symmetrize(small, iw, ih)
            make_buildable(small, iw, ih)
        thicken_necks(small, iw, ih, mirror=bool(mirror))
    if (iw, ih) != (nw, nh):
        small = _pad(small, iw, ih, nw, nh)
    return small, nw, nh


def was_symmetric(g, w, h, threshold=0.999):
    """Did the full-size pattern obey a mirror line? Then the small one must."""
    score, _ = best_axis(g, w, h)
    return score >= threshold


def variants(g, w, h, backgroundless=True):
    """{'small': (grid, w, h), ...} for every size that survives the reduction.

    `backgroundless` says whether the pattern's connectivity actually matters.
    A full-board design is trivially connected at any size and the repair pass
    would only fatten it.
    """
    mirror = was_symmetric(g, w, h)
    out = {}
    for name, frac in SIZES.items():
        want = MARGIN if backgroundless else 0
        for margin in range(want, -1, -1):
            got = reduce_grid(g, w, h, frac, mirror=mirror,
                              repair=backgroundless, margin=margin)
            if not got:
                break
            beads = sum(1 for row in got[0] for c in row if c is not None)
            if beads >= MIN_BEADS or margin == 0:
                out[name] = got
                break
    return out
