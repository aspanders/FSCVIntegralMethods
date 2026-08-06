"""Structural uniqueness for the library.

A pattern's signature is COLOR-AGNOSTIC: the grid of palette indices in
first-appearance order. Two patterns that differ only by color collapse to the
same signature, so `dedup` drops pure recolors and keeps only distinct designs.
"""
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


def count_unique(patterns):
    return len({signature(p) for p in patterns})
