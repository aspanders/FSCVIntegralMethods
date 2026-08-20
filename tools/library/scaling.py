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


def reduce_grid(g, w, h, frac, mirror=None, repair=True):
    """A smaller, still-buildable copy of `g`. Returns (grid, nw, nh) or None."""
    nw, nh = max(1, round(w * frac)), max(1, round(h * frac))
    if nw < MIN_SIDE or nh < MIN_SIDE or (nw >= w and nh >= h):
        return None
    small = resample(g, w, h, nw, nh)
    if not any(c is not None for row in small for c in row):
        return None
    if not repair:
        return small, nw, nh
    if mirror:
        symmetrize(small, nw, nh)
    make_buildable(small, nw, nh)
    if mirror:
        symmetrize(small, nw, nh)
        make_buildable(small, nw, nh)
    thicken_necks(small, nw, nh, mirror=bool(mirror))
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
        got = reduce_grid(g, w, h, frac, mirror=mirror, repair=backgroundless)
        if got:
            out[name] = got
    return out
