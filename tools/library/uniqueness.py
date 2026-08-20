"""Structural uniqueness for the library.

A pattern's signature is COLOR-AGNOSTIC: the grid of palette indices in
first-appearance order. Two patterns that differ only by color collapse to the
same signature, so `dedup` drops pure recolors and keeps only distinct designs.
"""
import re

from compact import from_rows


def signature(p):
    cells = p.get("cells")
    if cells is None:
        cells = from_rows(p.get("rows", []), p["palette"])
    w, h = p["grid"]["width"], p["grid"]["height"]
    order = {}
    marks = []
    # sort so signature is order-independent of cell listing
    for c in sorted(cells, key=lambda c: (c["y"], c["x"])):
        cid = c.get("colorId")
        if cid is None:
            continue
        if cid not in order:
            order[cid] = len(order)
        marks.append((c["x"], c["y"], order[cid]))
    return (w, h, tuple(marks))


def dedup(patterns):
    """Keep first occurrence of each distinct color-agnostic design."""
    seen = set()
    out = []
    for p in patterns:
        s = signature(p)
        if s in seen:
            continue
        seen.add(s)
        out.append(p)
    return out


def colored_signature(p):
    """Like signature but keyed on actual colors - for color-defined categories
    (rainbows) where a different color arrangement IS a different design."""
    cells = p.get("cells")
    if cells is None:
        cells = from_rows(p.get("rows", []), p["palette"])
    w, h = p["grid"]["width"], p["grid"]["height"]
    marks = tuple((c["x"], c["y"], c.get("colorId"))
                  for c in sorted(cells, key=lambda c: (c["y"], c["x"])) if c.get("colorId"))
    return (w, h, marks)


def count_unique(patterns):
    return len({signature(p) for p in patterns})


# ── Visual distinctness ──────────────────────────────────────────────────────

def cell_map(p, w=None, h=None):
    """Colour-agnostic index map: which cells share a colour, not which colour.

    A recolour collapses onto its original, exactly as `signature` intends -
    but unlike `signature` this supports comparing two boards that are ALMOST
    the same, which is the failure `signature` cannot see.

    Indices are assigned by FREQUENCY RANK, not by first appearance. First
    appearance makes the map depend on which colour happens to occupy the
    top-left cell: two boards differing by a single bead, where that bead is
    the first cell, came out 5.6% similar instead of 97%, so the lookalike
    check silently missed them. Ranking by cell count is stable under exactly
    the small edits this is meant to detect; ties fall back to first
    appearance so the result stays deterministic.
    """
    import numpy as np
    cells = p.get("cells")
    if cells is None:
        cells = from_rows(p.get("rows", []), p["palette"])
    w = w or p["grid"]["width"]
    h = h or p["grid"]["height"]
    counts, first = {}, {}
    for c in cells:
        cid = c.get("colorId")
        if cid is None:
            continue
        counts[cid] = counts.get(cid, 0) + 1
        first.setdefault(cid, c["y"] * w + c["x"])
    order = sorted(counts, key=lambda cid: (-counts[cid], first[cid]))
    idx = {cid: i + 1 for i, cid in enumerate(order)}
    g = np.zeros(w * h, dtype=np.int16)
    for c in cells:
        cid = c.get("colorId")
        if cid is None:
            continue
        x, y = c["x"], c["y"]
        if 0 <= x < w and 0 <= y < h:
            g[y * w + x] = idx[cid]
    return g


def select_distinct(patterns, limit=None, threshold=0.95):
    """Greedily keep patterns that no earlier kept pattern looks like.

    Generators sweep parameters, and a sweep fine enough to fill a category is
    usually finer than the eye: mandalas 225 and 243 shared 99.8% of their
    cells. Rather than hand-tuning every stride, over-generate and let this
    decide what actually reads as a different design.

    Boards of different sizes are trivially distinct, so they are compared only
    within their own size.
    """
    import numpy as np
    kept, kept_by_size = [], {}
    for p in patterns:
        size = (p["grid"]["width"], p["grid"]["height"])
        v = cell_map(p)
        stack = kept_by_size.get(size)
        if stack is not None and len(stack):
            if (np.stack(stack) == v).mean(axis=1).max() >= threshold:
                continue
        kept_by_size.setdefault(size, []).append(v)
        kept.append(p)
        if limit and len(kept) >= limit:
            break
    return kept


# Suffixes generators append to mark a variant of one design.
VARIANT_WORDS = {
    "Small", "Large", "Wide", "Tall", "Bold", "Fine", "Compact", "Long", "Big",
    "Wheels", "Cub", "Standing", "Crouching", "Grazing", "Young", "Sleek",
    "Finned", "Spotted", "Winged", "Slender", "Antennaed", "Perched", "Calling",
    "Fledgling", "Alert", "Out", "Wings", "Sapling", "Old", "Squat", "Bud",
    "Full", "Double", "Simple", "Sprig", "Tile", "Knockout", "Shadow", "Framed",
    "Silhouette", "Outline", "Grin", "Laughing", "Sad", "Wink", "Love", "Cool",
    "Surprised", "Angry", "Sleepy", "Silly", "Starry",
}


_PARAM_TAG = re.compile(r"^[a-z]{1,2}[-0-9.]+$")


def family_of(title):
    """The design a title belongs to, ignoring variant and sequence suffixes.

    Three kinds of suffix have to go: variant words ("Wren Perched"), bare
    sequence numbers ("Planet 4"), and the parameter tags generators append
    ("Vert Stripes w1", "4-Point r0.46 z0.47"). Treating any of them as part of
    the name makes every sweep member its own family, which both mislabels
    lookalike pairs as cross-family and defeats interleaving a category by
    family - round-robin over 75 one-member families reproduces the original
    order exactly, so geometric still opened with fourteen stripe patterns.
    """
    words = title.split()
    while len(words) > 1 and (words[-1] in VARIANT_WORDS or
                              words[-1].replace(".", "").isdigit() or
                              _PARAM_TAG.match(words[-1])):
        words.pop()
    return " ".join(words)
