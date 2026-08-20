"""Assemble the published pattern library and bump its version.

Collects:
  - generated icons (gen_icons.py): 100+ recognizable letters/digits/shapes
  - developer photo patterns (library/incoming.json, from photo_to_pattern.py)

Writes:
  - library/patterns.json : every pattern (the big file the app downloads)
  - library/manifest.json : tiny {version, count, patternsUrl, updatedAt}

The app checks manifest.json (cheap), and only downloads patterns.json when the
version is newer than what it already has.

Usage:
  python build_manifest.py                 # rebuild, auto-increment version
  python build_manifest.py --version 7     # set an explicit version
  python build_manifest.py --raw-base https://raw.githubusercontent.com/<you>/<repo>/<branch>
"""
import argparse
import json
import os
import shutil

import gen_icons
import gen_3d
import gen_circles
import gen_creatures
import gen_objects
import gen_faces
import gen_library
import gen_library2
import compact
import uniqueness
from beadlib import REPO, CATEGORIES

LIB = os.path.join(REPO, "library")
PATTERNS = os.path.join(LIB, "patterns.json")
MANIFEST = os.path.join(LIB, "manifest.json")
INCOMING = os.path.join(LIB, "incoming.json")

# The full library ships bundled in each app so it shows on first run offline.
# These copies are kept identical to PATTERNS by this script.
BUNDLE_COPIES = [
    os.path.join(REPO, "BeadSnapAndroid", "app", "src", "main", "assets", "library.json"),
    os.path.join(REPO, "BeadSnap", "BeadSnap", "Resources", "library.json"),
]

DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/claude/fuse-bead-converter-app-706h2s"

def collect():
    patterns = []
    patterns += gen_library.generate()   # 9 categories x 100 procedural patterns
    patterns += gen_library2.generate()  # 12 more categories x 100 procedural patterns
    patterns += gen_icons.generate()     # icons: letters, digits, symbols
    patterns += gen_3d.generate()        # threeD builds with guides
    patterns += gen_circles.generate()   # round-pegboard designs (shape=circle)
    # Silhouette categories rebuilt from parametric parts REPLACE the
    # recolour-heavy originals outright. Filtering by category rather than by
    # id matters: stable_id gives old and new the same "<category>-" prefix, so
    # an id-based filter shipped both and doubled the category.
    rebuilt = dict(gen_creatures.GENERATORS)
    rebuilt.update(gen_objects.GENERATORS)
    rebuilt.update(gen_faces.GENERATORS)
    # space is TOPPED UP rather than replaced: the planets and suns are fine,
    # there just are not a hundred distinct ways to draw a disc.
    topped_up = {"space"}
    patterns = [p for p in patterns
                if p["category"] not in rebuilt or p["category"] in topped_up]
    for fn in rebuilt.values():
        patterns += fn()
    if os.path.exists(INCOMING):
        patterns += json.load(open(INCOMING))
    # de-dup by id (later wins)
    by_id = {p["id"]: p for p in patterns}
    return _interleave(_distinct_per_category(list(by_id.values())))


def _is_blank(p):
    from collections import Counter
    cells = p.get("cells") or compact.from_rows(p.get("rows", []), p["palette"])
    w, h = p["grid"]["width"], p["grid"]["height"]
    ids = [c.get("colorId") for c in cells if c.get("colorId")]
    if not ids:
        return True
    return Counter(ids).most_common(1)[0][1] / (w * h) >= 0.995


def _distinct_per_category(patterns):
    """Drop patterns that look like one already in the same category.

    Structural uniqueness is an EXACT match and so passes at 100% while a
    category is still full of pairs nobody could tell apart - 4384 of them at
    one point, mostly consecutive steps of a parameter sweep. This is the
    backstop: no shipped pattern shares 95% of its cells with another in the
    same category, whatever the generator did.
    """
    from collections import OrderedDict
    by_cat = OrderedDict()
    for p in patterns:
        by_cat.setdefault(p["category"], []).append(p)
    # Some categories are defined by completeness, not by novelty. An alphabet
    # missing D, F and N because they resemble O, E and M is worse than one
    # containing all three: the letters ARE similar, and a user looking for a D
    # is not consoled by its absence being principled.
    LENIENT = {"icons": 1.0}
    out = []
    for cat, lst in by_cat.items():
        # A board covered by a single colour is a blank, not a pattern. One
        # slipped through as "Square Grid s4", where the grid spacing happened
        # to make the squares meet.
        lst = [p for p in lst if not _is_blank(p)]
        keep = uniqueness.select_distinct(lst, threshold=LENIENT.get(cat, 0.95))
        if len(keep) < len(lst):
            print(f"  {cat}: dropped {len(lst) - len(keep)} lookalikes "
                  f"({len(lst)} -> {len(keep)})")
        out += keep
    return out


def _interleave(patterns):
    """Round-robin each category across its design families.

    Generators emit family by family, so a category opened at the top showed a
    dozen variations of one idea before reaching the second - geometric led
    with twelve stripe patterns. Every one of those is a distinct design, so
    the uniqueness numbers looked fine while the category still read as
    repetitive. Dealing every family in turn puts twelve DIFFERENT ideas on the
    first screen.
    """
    from collections import OrderedDict, defaultdict
    out = []
    by_cat = OrderedDict()
    for p in patterns:
        by_cat.setdefault(p["category"], []).append(p)
    for cat, lst in by_cat.items():
        fams = OrderedDict()
        for p in lst:
            # uniqueness.family_of strips both variant words and sequence
            # numbers, so "Wren Perched" and "Wren Calling" are one family and
            # "Planet 4" and "Planet 19" are too.
            fams.setdefault(uniqueness.family_of(p["title"]), []).append(p)
        order = list(fams.values())
        i = 0
        while any(order):
            for f in order:
                if i < len(f):
                    out.append(f[i])
            order = [f for f in order if len(f) > i + 1]
            i += 1
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", type=int, default=None)
    ap.add_argument("--raw-base", default=DEFAULT_RAW_BASE)
    ap.add_argument("--updated-at", default="", help="ISO timestamp; blank = leave prior/none")
    args = ap.parse_args()

    patterns = collect()

    prev_version = 0
    if os.path.exists(MANIFEST):
        try:
            prev_version = json.load(open(MANIFEST)).get("version", 0)
        except Exception:
            prev_version = 0
    version = args.version if args.version is not None else prev_version + 1

    # This file is machine-read (bundled asset + network download), not
    # hand-edited. The compact 'rows' encoding + minified JSON take it from
    # ~15 MB to ~1 MB; both apps expand rows back to cells on load.
    shipped = [compact.compact_pattern(p) for p in patterns]
    json.dump({"version": version, "patterns": shipped},
              open(PATTERNS, "w"), separators=(",", ":"))

    per_cat = {c: 0 for c in CATEGORIES}
    for p in patterns:
        per_cat[p["category"]] = per_cat.get(p["category"], 0) + 1

    manifest = {
        "version": version,
        "count": len(patterns),
        "perCategory": per_cat,
        "patternsUrl": f"{args.raw_base}/library/patterns.json",
        "updatedAt": args.updated_at,
    }
    json.dump(manifest, open(MANIFEST, "w"), indent=2)

    # Keep the bundled app copies identical to the source library.
    for dst in BUNDLE_COPIES:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(PATTERNS, dst)

    print(f"Library v{version}: {len(patterns)} patterns")
    for c in CATEGORIES:
        print(f"  {c:10s} {per_cat.get(c, 0)}")
    print(f"  -> {PATTERNS}")
    print(f"  -> {MANIFEST}")
    for dst in BUNDLE_COPIES:
        print(f"  -> {dst}")
    print(f"NOTE: set BUNDLED_LIBRARY_VERSION / bundledLibraryVersion to {version} in both apps.")

if __name__ == "__main__":
    main()
