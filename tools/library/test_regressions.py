"""One named test per bug found in the QC pass, so none of them can come back.

Each test states the SYMPTOM first: what shipped, and what a user saw. Run with
    python test_regressions.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit import PATTERNS, measure, near_duplicates            # noqa: E402
from compact import from_rows                                    # noqa: E402
from uniqueness import cell_map, family_of, select_distinct      # noqa: E402
from connectivity import (SNAP_SYMMETRIC, best_axis, components,   # noqa: E402
                          grid_of, has_background, mirror_score,
                          weak_necks)

SHIPPED = json.load(open(PATTERNS))["patterns"]
BY_CAT = {}
for _p in SHIPPED:
    BY_CAT.setdefault(_p["category"], []).append(_p)

FAILURES = []


def check(name, ok, detail=""):
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if not ok:
        FAILURES.append((name, detail))
        if detail:
            print(f"        {detail}")


# ── 1. auto-fit cancelled every scale variant ────────────────────────────────
# Symptom: "Grapes" and "Grapes Large" were 99.9% identical. _frame scales a
# subject up to fill the board, so a spec asking for 0.76 and one asking for
# 1.18 both came out full size.
def test_fill_changes_the_board():
    import gen_creatures as gc
    from canvas import Grid

    def draw(g, spec, cx, cy, k):
        g.disc(cx, cy, 6 * k, "red")

    spec = {"fill": 0.72}
    small = gc._frame(draw, spec, "white", fill=0.72)
    large = gc._frame(draw, spec, "white", fill=0.96)
    a = np.array([1 if c == "red" else 0 for row in small.g for c in row])
    b = np.array([1 if c == "red" else 0 for row in large.g for c in row])
    ratio = a.sum() / max(b.sum(), 1)
    check("1. fill= actually changes the drawn size",
          0.35 < ratio < 0.85, f"small/large bead ratio {ratio:.2f}, expected ~0.55")


# ── 2. shrinking makes different subjects converge ───────────────────────────
# Symptom: at 0.54 fill "Wasp Small" and "Firefly Small" were 99.7% identical,
# and 90% of the board was background.
def test_small_variants_do_not_converge():
    """Two different subjects shrunk to the same size must stay different.

    A blanket "fill >= 0.70" rule would be the wrong invariant: the Framed
    variants use 0.62 and are fine, because the border occupies the margin the
    subject gives up (their dominant-colour share runs 0.36-0.70, and none is
    near-blank). What actually matters is the outcome.
    """
    SHRINK = (" Small", " Cub", " Bud", " Sapling", " Compact")
    bad = []
    for cat, lst in BY_CAT.items():
        if cat == "icons":
            continue
        shrunk = [p for p in lst if p["title"].endswith(SHRINK)]
        if len(shrunk) < 2:
            continue
        for score, a, b, _same in near_duplicates(shrunk):
            bad.append(f"{cat}: {100*score:.1f}% {a} == {b}")
    check("2. shrunk variants of different subjects stay distinct",
          not bad, "; ".join(bad[:4]))


# ── 3. _emit only deduped EXACT matches ──────────────────────────────────────
# Symptom: mandalas 225 and 243 shared 99.8% of their cells and both shipped.
def test_emit_rejects_lookalikes():
    import gen_creatures as gc
    from canvas import Grid

    def build(spec):
        g = Grid(28, 28)
        g.fill("white")
        g.disc(14, 14, 9, "red")
        # one bead of difference between successive specs
        g.set(spec["i"], 0, "blue")
        return g

    specs = [{"name": f"x{i}", "i": i, "tags": []} for i in range(10)]
    out = gc._emit("geometric", specs, build, target=10)
    check("3. _emit drops boards that differ by a bead", len(out) == 1,
          f"kept {len(out)} of 10 near-identical boards")


# ── 4. family_of missed sequence and parameter suffixes ──────────────────────
# Symptom: "Planet 4" became its own family, so round-robin over 75 one-member
# families reproduced the original order and space opened with 16 planets.
def test_family_of_strips_suffixes():
    cases = {"Planet 4": "Planet", "Vert Stripes w1": "Vert Stripes",
             "Mandala 10-fold 225": "Mandala 10-fold", "Wren Perched": "Wren",
             "4-Point r0.46 z0.47": "4-Point", "Letter A Tile": "Letter A",
             "Grapes Large": "Grapes"}
    bad = [f"{k}->{family_of(k)}" for k, v in cases.items() if family_of(k) != v]
    check("4a. family_of strips variant, sequence and parameter suffixes",
          not bad, ", ".join(bad))

    worst = []
    for cat, lst in BY_CAT.items():
        if cat == "icons":
            continue          # letters resemble letters; see test 8
        head = lst[:12]
        if len(head) < 4:
            continue
        M = np.stack([cell_map(p) for p in head
                      if (p["grid"]["width"], p["grid"]["height"]) ==
                         (head[0]["grid"]["width"], head[0]["grid"]["height"])])
        if len(M) < 4:
            continue
        sims = [(M[i] == M[j]).mean()
                for i in range(len(M)) for j in range(i + 1, len(M))]
        if max(sims) >= 0.95:
            worst.append(f"{cat}: two of the first 12 are "
                         f"{100*max(sims):.0f}% identical")
    check("4b. the first screen of every category is visibly varied",
          not worst, "; ".join(worst))


# ── 5. the 3D nets erased themselves ─────────────────────────────────────────
# Symptom: _place wrote the overlay's transparent marker through as a colour,
# so the dice net was a scatter of pips with no faces at all.
def test_3d_nets_have_faces_and_folds():
    import gen_3d
    nets = {p["title"]: p for p in gen_3d.generate()}
    dice = nets["Dice (Cube)"]
    w, h = dice["grid"]["width"], dice["grid"]["height"]
    ids = [c["colorId"] for c in dice["cells"]]
    from collections import Counter
    n = Counter(ids)
    # six 5x5 faces = 150 cells; pips and fold lines are drawn within them
    check("5a. dice net draws all six faces, not just the pips",
          len(dice["cells"]) == 150, f"{len(dice['cells'])} beads, expected 150")
    check("5b. dice net has visible fold lines",
          n.get("light_gray", 0) > 40, f"{n.get('light_gray', 0)} edge beads")
    pips = n.get("black", 0)
    check("5c. corner pips survive the fold lines",
          pips == 21, f"{pips} pips, expected 1+2+3+4+5+6 = 21")
    gift = nets["Gift Box"]
    check("5d. gift box net keeps all six faces (nothing erased)",
          len(gift["cells"]) == 6 * 6 * 6,
          f"{len(gift['cells'])} beads, expected 216 for six 6x6 faces")


# ── 6. the near-blank measure compared against PLACED beads ──────────────────
# Symptom: a one-colour star silhouette on an empty board scored 100% dominant
# and was flagged; 57 of 105 flags were exactly that.
def test_near_blank_measures_the_board():
    star = {"grid": {"width": 20, "height": 20},
            "palette": [{"id": "red", "name": "Red", "hex": "#FF0000"}],
            "cells": [{"x": x, "y": y, "colorId": "red"}
                      for y in range(20) for x in range(20)
                      if abs(x - 10) + abs(y - 10) < 6]}
    m = measure(star)
    check("6. a sparse one-colour silhouette is not called near-blank",
          m["dom"] < 0.5, f"dominant share {m['dom']:.2f} of the board")


# ── 7. a genuinely blank board shipped ───────────────────────────────────────
# Symptom: "Square Grid s4" was one colour edge to edge.
def test_no_blank_boards_ship():
    blank = [(p["category"], p["title"]) for p in SHIPPED
             if measure(p)["dom"] >= 0.995]
    check("7. no shipped board is a single flat colour", not blank,
          str(blank[:5]))


# ── the property all seven were symptoms of ──────────────────────────────────
def test_shipped_library_has_no_lookalikes():
    offenders = []
    for cat, lst in BY_CAT.items():
        if cat == "icons":
            continue          # deliberately exempt: an alphabet needs all of it
        near = near_duplicates(lst)
        if near:
            offenders.append(f"{cat}: {len(near)} pairs, worst "
                             f"{100*near[0][0]:.1f}% {near[0][1]} == {near[0][2]}")
    check("8. no category outside icons ships a lookalike pair",
          not offenders, "; ".join(offenders[:3]))

    dropped = [f"{cat} {len(lst)}->{len(select_distinct(lst))}"
               for cat, lst in BY_CAT.items()
               if cat != "icons" and len(select_distinct(lst)) < len(lst)]
    check("9. the distinctness backstop has nothing left to drop",
          not dropped, "; ".join(dropped[:4]))


# ── 10-13. buildability, added after the backdrops came off ─────────────────
# Symptom: with a backdrop every pattern is trivially one connected piece, so
# 218 unbuildable patterns sat in the categories that already had none and
# nobody noticed. Removing backdrops from 1500 more would have shipped
# hundreds of piles of loose beads.
def test_patterns_are_buildable():
    nobg = [p for p in SHIPPED if not has_background(p)]
    frac = len(nobg) / len(SHIPPED)
    check("10. at least 60% of the library has no background",
          frac >= 0.60, f"{100*frac:.1f}%")

    broken = []
    for p in nobg:
        g, w, h = grid_of(p)
        if len(components(g, w, h)) > 1:
            broken.append(f"{p['category']}/{p['title']}")
    check("11. every backgroundless pattern is ONE connected piece",
          not broken, f"{len(broken)} in pieces: {broken[:3]}")

    thin = []
    for p in nobg:
        g, w, h = grid_of(p)
        if weak_necks(g, w, h):
            thin.append(f"{p['category']}/{p['title']}")
    check("12. no part hangs off a pattern by a single bead",
          not thin, f"{len(thin)} thin joins: {thin[:3]}")

    # An empty peg reads as pale grey, so a white bead is indistinguishable
    # from one left out - and on the mandalas those beads are the silhouette.
    pale = [f"{p['category']}/{p['title']}" for p in nobg
            if any(c["id"] in ("white", "ivory", "clear") for c in p["palette"])]
    check("13. no backgroundless pattern uses a board-coloured bead",
          not pale, f"{len(pale)}: {pale[:3]}")

    big = [f"{p['category']}/{p['title']}" for p in SHIPPED
           if max(p["grid"]["width"], p["grid"]["height"]) > 29]
    check("14. every board fits a standard 29x29 pegboard",
          not big, f"{len(big)} too large: {big[:3]}")


def test_size_variants():
    """Small and medium have to be as buildable as the board they came from."""
    import scaling
    from compact import from_rows

    def grid_of_variant(v, palette):
        g = [[None] * v["width"] for _ in range(v["height"])]
        for c in from_rows(v["rows"], palette):
            g[c["y"]][c["x"]] = c["colorId"]
        return g, v["width"], v["height"]

    eligible = [p for p in SHIPPED
                if round(min(p["grid"]["width"], p["grid"]["height"])
                         * scaling.SIZES["small"]) >= scaling.MIN_SIDE]
    missing = [f"{p['category']}/{p['title']}" for p in eligible
               if set(p.get("sizes", {})) != {"small", "medium"}]
    check("15. every board big enough to reduce offers small and medium",
          not missing, f"{len(missing)} without both: {missing[:3]}")

    wrong = []
    for p in SHIPPED:
        for name, v in (p.get("sizes") or {}).items():
            if (v["width"] >= p["grid"]["width"]
                    or min(v["width"], v["height"]) < scaling.MIN_SIDE
                    or len(v["rows"]) != v["height"]
                    or any(len(r) != v["width"] for r in v["rows"])):
                wrong.append(f"{p['category']}/{p['title']}/{name}")
    check("16. every size variant is smaller, square-edged and well formed",
          not wrong, f"{len(wrong)} malformed: {wrong[:3]}")

    broken = []
    for p in SHIPPED:
        if has_background(p):
            continue
        for name, v in (p.get("sizes") or {}).items():
            g, w, h = grid_of_variant(v, p["palette"])
            if len(components(g, w, h)) > 1:
                broken.append(f"{p['category']}/{p['title']}/{name}")
    check("17. every size variant of a backgroundless pattern is one piece",
          not broken, f"{len(broken)} in pieces: {broken[:3]}")

    lost = []
    for p in SHIPPED:
        for name, v in (p.get("sizes") or {}).items():
            beads = sum(1 for r in v["rows"] for ch in r if ch != ".")
            if beads < 12:
                lost.append(f"{p['category']}/{p['title']}/{name}")
    check("18. no size variant reduces to a handful of beads",
          not lost, f"{len(lost)} nearly empty: {lost[:3]}")


# ── 19. subjects drawn symmetric shipped wonky ───────────────────────────────
# Symptom: "many of the bugs should have symmetric patterns, but they are
# wonky". Ellipses rounded differently on each side, limbs grew towards +x/+y
# only, and the weld and thicken passes patched whichever side happened to
# need it. Nothing in the pipeline put it back.
def test_symmetric_subjects_are_symmetric():
    """A category drawn bilaterally symmetric must ship bilaterally symmetric.

    A side-view fish or a letter R is asymmetric on purpose and is not checked;
    the score is measured on INK only, so a small subject on a bare board
    cannot earn credit for the bare board it sits in.
    """
    MIRRORED = ("bugs", "emoji", "gems", "hearts", "circles", "snowflakes",
                "flowers", "stars", "mandalas")
    bad = []
    for cat in MIRRORED:
        for p in BY_CAT.get(cat, []):
            g, w, h = grid_of(p)
            score = mirror_score(g, w, h)
            if score < 0.99:
                bad.append(f"{cat}/{p['title']} {100*score:.0f}%")
    check("19. every subject in a symmetric category is symmetric",
          not bad, f"{len(bad)} wonky: {bad[:4]}")

    # And nothing ANYWHERE should sit in the uncanny band: a subject that is
    # 95% symmetric was drawn symmetric and came out wrong, which reads worse
    # than one that is frankly asymmetric.
    band = []
    for p in SHIPPED:
        g, w, h = grid_of(p)
        score = mirror_score(g, w, h)
        if SNAP_SYMMETRIC <= score < 0.99:
            band.append(f"{p['category']}/{p['title']} {100*score:.0f}%")
    check("19b. almost nothing is left in the almost-symmetric band",
          len(band) <= 20, f"{len(band)} nearly-symmetric: {band[:4]}")


def test_no_franchise_references():
    """Nothing in the library may name or depict someone else's character.

    A "video game" category is an open invitation to draw other people's
    sprites, and it had four: a creeper head, a mushroom with eyes, a magenta
    ghost with a wavy skirt and a green invader. Each belonged to a rights
    holder that enforces - Mojang, Nintendo, Bandai Namco, Taito - and each
    passed every quality check in the suite, because none of them measures
    whose character it is.

    The Steamboat Willie set is deliberately NOT caught here: the 1928 short is
    in the United States public domain, the art is held to that depiction, and
    the patterns are titled after the short rather than after the trademarked
    character. See tools/library/gen_willie.py.
    """
    banned = [
        "creeper", "minecraft", "mario", "luigi", "yoshi", "bowser", "nintendo",
        "pikachu", "pokemon", "sonic", "sega", "zelda", "kirby",
        "tetris", "tetromino", "pac-man", "pacman", "space invader", "invader",
        "hello kitty", "batman", "superman", "spider-man", "marvel", "star wars",
        "lego", "among us", "fortnite", "roblox", "disney", "mickey mouse",
    ]
    bad = []
    for p in SHIPPED:
        hay = (p["title"] + " " + " ".join(p.get("tags", []))).lower()
        for term in banned:
            if term in hay:
                bad.append(f"{p['category']}/{p['title']} matches {term!r}")
    check("20. no pattern names or tags someone else's character", not bad,
          "; ".join(sorted(set(bad))[:5]))


def test_subjects_clear_the_board_edge():
    """No backgroundless board, at any size, puts a bead on the outermost peg.

    Symptom: "ensure that the letters and the hearts do not touch the edges".
    Every heart sat one bead from the edge at full size, and the reduction
    scales the WHOLE board - margin included - so at 0.52 that one bead became
    none: 181 of the 184 reduced hearts ran into all four sides, and 2062 of
    the library's 4674 reduced boards did.

    It matters beyond looks. A bead on the outermost peg has nothing holding it
    on three sides while the design is ironed, the pattern cannot be given a
    border, and pegboards vary by a peg or two between brands, so the edge row
    is the first thing that does not fit.

    A pattern WITH a background is exempt: a full board is what that design is,
    and ringing it with empty pegs would read as a mistake rather than a
    margin.
    """
    from connectivity import has_background
    tight = []
    for p in SHIPPED:
        if has_background(p):
            continue
        boards = [(p["grid"]["width"], p["grid"]["height"],
                   [(c["x"], c["y"]) for c in
                    (p.get("cells") or from_rows(p["rows"], p["palette"]))],
                   "full")]
        for name, v in (p.get("sizes") or {}).items():
            boards.append((v["width"], v["height"],
                           [(x, y) for y, r in enumerate(v["rows"])
                            for x, ch in enumerate(r) if ch != "."], name))
        for w, h, pts, name in boards:
            if not pts:
                continue
            xs = [x for x, _ in pts]; ys = [y for _, y in pts]
            if min(min(xs), min(ys), w - 1 - max(xs), h - 1 - max(ys)) < 1:
                tight.append(f"{p['category']}/{p['title']}/{name}")
    # Full-size boards are allowed to fill their own board - "filling the board
    # is most of what makes a 28x28 icon readable" - so this holds the line
    # where it was asked for and everywhere the REDUCTION would have caused it.
    reduced = [t for t in tight if not t.endswith("/full")]
    named = [t for t in tight if t.split("/")[0] in ("icons", "hearts")]
    check("21. no reduced backgroundless board touches the edge",
          not reduced, f"{len(reduced)} touching: {reduced[:3]}")
    check("21b. no letter or heart touches the edge at any size",
          not named, f"{len(named)} touching: {named[:3]}")


def test_a_border_always_has_colour_inside_it():
    """Two borders may never meet with nothing between them.

    Symptom: "the pretzels look like a slug"; "if there is a border, black or
    otherwise, it should contain color between at all points".

    _outline skips a strand that erodes to nothing, which handles a limb that
    is thin in two dimensions. The failure is one-dimensional. A limb three
    beads ACROSS but only three beads LONG has a solid centre, so all eight
    beads around that centre qualify as edge and the whole limb goes dark bar
    one. Repeat that over a pretzel drawn from three overlapping rings and the
    result is a black amoeba.

    This drives _outline directly on shapes chosen to hit each case, rather
    than scanning the shipped library, because the shipped answer depends on
    every species colour and every framing decision as well - and a test that
    depends on all of those tells you nothing about which one broke.
    """
    from canvas import Grid
    from gen_creatures import _outline, _ink_for, MAX_OUTLINE_SHARE

    def runs_keep_colour(g, ink):
        """Every row and column run of the subject holds a non-ink bead."""
        lines = [[(x, y) for x in range(g.w)] for y in range(g.h)]
        lines += [[(x, y) for y in range(g.h)] for x in range(g.w)]
        for line in lines:
            i = 0
            while i < len(line):
                x, y = line[i]
                if g.g[y][x] is None:
                    i += 1
                    continue
                j = i
                while j < len(line) and g.g[line[j][1]][line[j][0]] is not None:
                    j += 1
                run = line[i:j]
                if len(run) >= 2 and all(g.g[b][a] == ink for a, b in run):
                    return False
                i = j
        return True

    def blob(w, h):
        g = Grid(12, 12)
        for y in range(2, 2 + h):
            for x in range(2, 2 + w):
                g.set(x, y, "red")
        return g

    bad = []
    for w, h in ((3, 3), (3, 5), (4, 4), (5, 5), (3, 9), (9, 3), (6, 7), (8, 8)):
        g = blob(w, h)
        _outline(g, "black", None)
        if not runs_keep_colour(g, "black"):
            bad.append(f"{w}x{h} block")
    check("22. an outline never closes over the shape it outlines",
          not bad, f"pinched: {bad}")

    # However small the subject, the outline never becomes the pattern.
    over = []
    for w, h in ((3, 3), (3, 4), (4, 4), (3, 5), (5, 5), (3, 9), (7, 7)):
        g = blob(w, h)
        _outline(g, "black", None)
        ink = sum(1 for r in g.g for c in r if c == "black")
        if ink > MAX_OUTLINE_SHARE * (w * h):
            over.append(f"{w}x{h}: {ink}/{w*h}")
    check("22b. an outline never grows past its share of the subject",
          not over, f"over {MAX_OUTLINE_SHARE:.0%}: {over}")

    # And it is never drawn in a colour the subject already uses.
    g = blob(6, 6)
    g.set(3, 3, "black")
    check("22c. the outline colour never collides with the drawing",
          _ink_for(g, None, "black") != "black",
          f"picked {_ink_for(g, None, 'black')!r} when the drawing already uses it")


def test_no_subject_is_mostly_its_own_outline():
    """A border that outweighs what it borders has replaced it.

    Angelfish shipped at 99.2% black with one cream bead for an eye, and it
    passed every check in this file, because none of them measured how much of
    a subject its dark had eaten. Twenty-two other fish and thirty-four bugs
    were in the same state: the outline colour was also the species' marking
    colour, so fins, legs and edge were one mass.

    The bar is set where genuinely dark subjects still pass - a bat, a bomb,
    Steamboat Willie, an ant whose legs really are black - and the failure this
    is guarding against, an outline eating four fifths of a fish, cannot.
    """
    from collections import Counter
    from connectivity import has_background
    INK = ("black", "dark_gray")
    OUTLINED = {"animals", "birds", "bugs", "fish", "food", "sweets", "holidays",
                "sports", "trees", "vehicles", "videogame", "emoji", "flowers",
                "space", "threeD"}
    worst = []
    for p in SHIPPED:
        if p["category"] not in OUTLINED or has_background(p):
            continue
        cells = p.get("cells") or from_rows(p["rows"], p["palette"])
        counts = Counter(c["colorId"] for c in cells)
        if len(counts) < 2:
            continue
        ink = next((c for c in INK if c in counts), None)
        if ink and counts[ink] / sum(counts.values()) > 0.70:
            worst.append(f"{p['category']}/{p['title']} "
                         f"{100*counts[ink]/sum(counts.values()):.0f}% {ink}")
    check("23. no outlined subject is mostly its own outline",
          not worst, f"{len(worst)} swallowed: {worst[:3]}")



def main():
    print(f"regressions against {len(SHIPPED)} shipped patterns\n")
    for fn in (test_fill_changes_the_board, test_small_variants_do_not_converge,
               test_emit_rejects_lookalikes, test_family_of_strips_suffixes,
               test_3d_nets_have_faces_and_folds,
               test_near_blank_measures_the_board, test_no_blank_boards_ship,
               test_shipped_library_has_no_lookalikes,
               test_patterns_are_buildable, test_size_variants,
               test_symmetric_subjects_are_symmetric,
               test_no_franchise_references,
               test_subjects_clear_the_board_edge,
               test_a_border_always_has_colour_inside_it,
               test_no_subject_is_mostly_its_own_outline):
        fn()
    print()
    if FAILURES:
        print(f"{len(FAILURES)} FAILED")
        return 1
    print("all regression checks pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
