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
import gen_library
import compact
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
    patterns += gen_icons.generate()     # icons: letters, digits, symbols
    patterns += gen_3d.generate()        # threeD builds with guides
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
