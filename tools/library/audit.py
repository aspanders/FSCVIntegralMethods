"""Quality control for the shipped pattern library.

Two questions, both answerable without opinion:

  UNIQUENESS  how many of a category's patterns are actually different designs?
              uniqueness.signature is colour-blind, so a recolour of an
              existing design collapses onto it. Exact duplicates - byte-for-
              byte identical boards, colours included - are counted separately
              because they are the indefensible case: the same picture listed
              twice under two names.

  IMAGE       per-pattern measures that correlate with "is this worth making":
              bead count, how much of the board one colour takes, the fraction
              of beads that are isolated (a bead differing from all four of its
              neighbours reads as noise and is miserable to place), and mirror
              symmetry.

Usage:
    python audit.py                  # table + failures
    python audit.py --montage trees  # render a category to /tmp for eyeballing
"""
import argparse
import json
import os
from collections import Counter, defaultdict

from beadlib import REPO
from compact import from_rows
from uniqueness import family_of, signature

PATTERNS = os.path.join(REPO, "library", "patterns.json")

# Thresholds. Deliberately loose - these flag patterns worth LOOKING at, they
# are not a pass mark.
MIN_BEADS = 40          # below this there is barely a pattern to make
MAX_DOMINANT = 0.90     # one colour over this share of the BOARD is near-blank
MAX_SPECKLE = 0.15      # isolated beads as a fraction of all beads
MIN_UNIQUE_FRAC = 0.80  # a category below this is mostly recolours
NEAR_DUP = 0.95         # two boards sharing more than this are indistinguishable

def grid_of(p):
    cells = p.get("cells") or from_rows(p.get("rows", []), p["palette"])
    w, h = p["grid"]["width"], p["grid"]["height"]
    g = [[None] * w for _ in range(h)]
    for c in cells:
        if c.get("colorId") is not None and 0 <= c["x"] < w and 0 <= c["y"] < h:
            g[c["y"]][c["x"]] = c["colorId"]
    return g, w, h


def measure(p):
    g, w, h = grid_of(p)
    filled = [v for row in g for v in row if v]
    n = len(filled)
    counts = Counter(filled)
    # Share of the whole BOARD, not of the placed beads. Measured against the
    # placed beads, a one-colour star silhouette on an empty board scores 100%
    # and gets flagged as near-blank, which it plainly is not - 57 of the 105
    # flags were exactly that.
    dom = counts.most_common(1)[0][1] / (w * h) if n else 1.0
    iso = 0
    for y in range(h):
        for x in range(w):
            v = g[y][x]
            if not v:
                continue
            nb = [g[y + dy][x + dx] for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
                  if 0 <= y + dy < h and 0 <= x + dx < w and g[y + dy][x + dx]]
            if nb and all(u != v for u in nb):
                iso += 1
    sym = sum(1 for y in range(h) for x in range(w) if g[y][x] == g[y][w - 1 - x]) / (w * h)
    return dict(beads=n, colours=len(counts), dom=dom, fill=n / (w * h),
                speckle=iso / max(n, 1), sym=sym)


def near_duplicates(patterns, threshold=NEAR_DUP):
    """Pairs of patterns that share more than `threshold` of their cells.

    uniqueness.signature is an EXACT match, so two boards differing by a single
    bead both count as distinct. That is the gap this closes: a category can
    report 100% unique while being full of pairs nobody could tell apart. The
    comparison is colour-agnostic - it compares which cells share a colour, not
    which colour they share - so a recolour still collapses.
    """
    import numpy as np
    by_size = defaultdict(list)
    for p in patterns:
        by_size[(p["grid"]["width"], p["grid"]["height"])].append(p)
    out = []
    for (w, h), group in by_size.items():
        if len(group) < 2:
            continue
        rows = []
        for p in group:
            cells = p.get("cells") or from_rows(p.get("rows", []), p["palette"])
            g = np.zeros(w * h, dtype=np.int16)
            idx = {}
            for c in cells:
                cid = c.get("colorId")
                if cid is None:
                    continue
                if cid not in idx:
                    idx[cid] = len(idx) + 1
                g[c["y"] * w + c["x"]] = idx[cid]
            rows.append(g)
        M = np.stack(rows)
        for i in range(len(group)):
            same = (M[i + 1:] == M[i]).mean(axis=1)
            for j in np.nonzero(same >= threshold)[0]:
                a, b = group[i]["title"], group[i + 1 + int(j)]["title"]
                out.append((float(same[j]), a, b,
                            family_of(a) == family_of(b)))
    out.sort(reverse=True)
    return out


def exact_key(p):
    cells = p.get("cells") or from_rows(p.get("rows", []), p["palette"])
    return (p["grid"]["width"], p["grid"]["height"],
            tuple(sorted((c["x"], c["y"], c.get("colorId")) for c in cells)))


def audit(patterns):
    by = defaultdict(list)
    for p in patterns:
        by[p["category"]].append(p)

    rows = []
    failures = defaultdict(list)
    for cat, lst in sorted(by.items()):
        sigs = [signature(p) for p in lst]
        uniq = len(set(sigs))
        exact = Counter(exact_key(p) for p in lst)
        dups = sum(v - 1 for v in exact.values() if v > 1)
        ms = [measure(p) for p in lst]
        for p, m in zip(lst, ms):
            if m["beads"] < MIN_BEADS:
                failures["tiny"].append((cat, p["title"], m["beads"]))
            if m["dom"] > MAX_DOMINANT:
                failures["near-blank"].append((cat, p["title"], round(100 * m["dom"])))
            if m["speckle"] > MAX_SPECKLE:
                failures["speckled"].append((cat, p["title"], round(100 * m["speckle"])))
        near = near_duplicates(lst)
        same_fam = [x for x in near if x[3]]
        cross_fam = [x for x in near if not x[3]]
        rows.append(dict(
            cat=cat, n=len(lst), uniq=uniq, frac=uniq / len(lst), dups=dups,
            near=len(near), samefam=len(same_fam), crossfam=len(cross_fam),
            worst=near[0] if near else None,
            beads=sum(m["beads"] for m in ms) / len(ms),
            colours=sum(m["colours"] for m in ms) / len(ms),
            speckle=sum(m["speckle"] for m in ms) / len(ms)))
    return rows, failures


def render_montage(cat, patterns, cell=6, cols=10, limit=40, out=None):
    """Contact sheet for one category. No titles - the picture is the review."""
    from PIL import Image, ImageDraw
    lst = [p for p in patterns if p["category"] == cat][:limit]
    if not lst:
        raise SystemExit(f"no patterns in category {cat!r}")
    tiles = []
    for p in lst:
        g, w, h = grid_of(p)
        hexes = {c["id"]: c["hex"] for c in p["palette"]}
        img = Image.new("RGB", (w * cell, h * cell), (252, 252, 252))
        d = ImageDraw.Draw(img)
        for y in range(h):
            for x in range(w):
                cid = g[y][x]
                if not cid:
                    continue
                hx = hexes.get(cid, "#888888").lstrip("#")
                d.rectangle([x * cell, y * cell, x * cell + cell - 1, y * cell + cell - 1],
                            fill=tuple(int(hx[k:k + 2], 16) for k in (0, 2, 4)))
        tiles.append(img)
    tw = max(t.width for t in tiles)
    th = max(t.height for t in tiles)
    rows = (len(tiles) + cols - 1) // cols
    pad = 4
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + pad) + pad),
                      (226, 226, 230))
    for i, t in enumerate(tiles):
        sheet.paste(t, (pad + (i % cols) * (tw + pad) + (tw - t.width) // 2,
                        pad + (i // cols) * (th + pad) + (th - t.height) // 2))
    out = out or f"/tmp/library_{cat}.png"
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--montage", help="render this category to /tmp and exit")
    ap.add_argument("--file", default=PATTERNS)
    args = ap.parse_args()
    patterns = json.load(open(args.file))["patterns"]

    if args.montage:
        out = render_montage(args.montage, patterns)
        print(f"-> {out}")
        return

    rows, failures = audit(patterns)
    print(f"{'category':<12}{'n':>5}{'unique':>8}{'%':>6}{'exactDup':>9}"
          f"{'sameFam':>9}{'crossFam':>9}{'beads':>7}{'speckle':>9}")
    worst = []
    for r in rows:
        mark = "  <-- mostly recolours" if r["frac"] < MIN_UNIQUE_FRAC else ""
        if mark:
            worst.append(r)
        flag = "  <-- lookalikes" if r["near"] else ""
        print(f"{r['cat']:<12}{r['n']:>5}{r['uniq']:>8}{100*r['frac']:>5.0f}%"
              f"{r['dups']:>9}{r['samefam']:>9}{r['crossfam']:>9}{r['beads']:>7.0f}"
              f"{100*r['speckle']:>8.1f}%{mark or flag}")
    n = sum(r["n"] for r in rows)
    u = sum(r["uniq"] for r in rows)
    d = sum(r["dups"] for r in rows)
    sf = sum(r["samefam"] for r in rows)
    cf = sum(r["crossfam"] for r in rows)
    print(f"\n{n} patterns, {u} distinct designs ({100*u/n:.1f}%), "
          f"{d} exact duplicates")
    print(f"lookalike pairs at >={100*NEAR_DUP:.0f}% identical cells: "
          f"{sf} same-family (pointless variants), {cf} cross-family "
          f"(designs that render the same)")
    for r in rows:
        if r["worst"]:
            sc, a, b, same = r["worst"]
            kind = "same-family" if same else "CROSS-FAMILY"
            print(f"    {r['cat']:<11} worst {100*sc:5.1f}%  {kind:<12} "
                  f"{a}  ==  {b}")
    print(f"{len(worst)} categories below {100*MIN_UNIQUE_FRAC:.0f}% unique: "
          f"{', '.join(r['cat'] for r in worst) or 'none'}")
    for k, v in sorted(failures.items()):
        print(f"\n{k}: {len(v)}")
        for row in v[:5]:
            print("   ", row)
        if len(v) > 5:
            print(f"    ... and {len(v)-5} more")


if __name__ == "__main__":
    main()
