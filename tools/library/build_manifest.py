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

import gen_icons
import gen_3d
from beadlib import REPO, CATEGORIES

LIB = os.path.join(REPO, "library")
PATTERNS = os.path.join(LIB, "patterns.json")
MANIFEST = os.path.join(LIB, "manifest.json")
INCOMING = os.path.join(LIB, "incoming.json")

DEFAULT_RAW_BASE = "https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/claude/fuse-bead-converter-app-706h2s"

def collect():
    patterns = []
    patterns += gen_icons.generate()
    patterns += gen_3d.generate()
    if os.path.exists(INCOMING):
        patterns += json.load(open(INCOMING))
    # de-dup by id (later wins)
    by_id = {p["id"]: p for p in patterns}
    return list(by_id.values())

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

    json.dump({"version": version, "patterns": patterns},
              open(PATTERNS, "w"), indent=2)

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

    print(f"Library v{version}: {len(patterns)} patterns")
    for c in CATEGORIES:
        print(f"  {c:10s} {per_cat.get(c, 0)}")
    print(f"  -> {PATTERNS}")
    print(f"  -> {MANIFEST}")

if __name__ == "__main__":
    main()
