"""Developer tool: convert photos of finished bead creations into library patterns.

Uses the SAME LAB nearest-color quantization the app uses, so a photo you add
here looks the way it would if a user converted it in-app. Intended for the
developer to photograph their own finished pieces and publish them to the
public library.

Requires Pillow:  pip install pillow

Usage:
  # single photo
  python photo_to_pattern.py add photo.jpg --title "Blue Cat" --category animals \
        --tags cat,blue --grid 32 --max-colors 14

  # a whole folder (metadata from a CSV: filename,title,category,tags)
  python photo_to_pattern.py batch ./my_photos --csv meta.csv --grid 32

Adds the resulting pattern(s) to library/incoming.json, which build_manifest.py
folds into the published library.
"""
import argparse
import csv
import json
import os
import sys

from PIL import Image

from beadlib import nearest_color_id, make_pattern, stable_id, CATEGORIES, REPO

INCOMING = os.path.join(REPO, "library", "incoming.json")
GRID_PRESETS = {16: (16, 16), 24: (24, 24), 32: (32, 32), 48: (48, 48)}

def convert_image(path, title, category, tags, grid=32, max_colors=14):
    if category not in CATEGORIES:
        raise SystemExit(f"category must be one of {CATEGORIES}")
    cols, rows = GRID_PRESETS.get(grid, (grid, grid))
    img = Image.open(path).convert("RGBA").resize((cols, rows), Image.LANCZOS)
    px = img.load()

    # 1) nearest bead color for every non-transparent cell
    assign = {}
    counts = {}
    for y in range(rows):
        for x in range(cols):
            r, g, b, a = px[x, y]
            if a < 38:  # ~0.15 alpha: treat as background (matches the app)
                continue
            cid = nearest_color_id(r, g, b)
            assign[(x, y)] = cid
            counts[cid] = counts.get(cid, 0) + 1

    # 2) limit to the maxColors most-used, remap the rest to the nearest kept color
    if len(counts) > max_colors:
        keep = {cid for cid, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:max_colors]}
        kept_rgb = _rgb_for_ids(keep)
        for pos, cid in list(assign.items()):
            if cid not in keep:
                assign[pos] = _nearest_kept(cid, kept_rgb)

    cells = [(x, y, cid) for (x, y), cid in assign.items()]
    return make_pattern(
        stable_id("photo", f"{category}:{title}"),
        title, category, cols, rows, cells,
        tags=tags + ["photo", "handmade"],
        source_prompt=None,
    )

def _rgb_for_ids(ids):
    from beadlib import PALETTE, hex_to_rgb
    return {c["id"]: hex_to_rgb(c["hex"]) for c in PALETTE if c["id"] in ids}

def _nearest_kept(cid, kept_rgb):
    from beadlib import PALETTE, hex_to_rgb, rgb_to_lab
    src = next(hex_to_rgb(c["hex"]) for c in PALETTE if c["id"] == cid)
    slab = rgb_to_lab(*(v / 255.0 for v in src))
    best, bestd = None, 1e18
    for kid, rgb in kept_rgb.items():
        klab = rgb_to_lab(*(v / 255.0 for v in rgb))
        d = sum((a - b) ** 2 for a, b in zip(slab, klab))
        if d < bestd:
            bestd, best = d, kid
    return best

def load_incoming():
    if os.path.exists(INCOMING):
        return json.load(open(INCOMING))
    return []

def save_incoming(patterns):
    json.dump(patterns, open(INCOMING, "w"), indent=2)
    print(f"  wrote {len(patterns)} pattern(s) -> {INCOMING}")

def cmd_add(args):
    p = convert_image(args.photo, args.title, args.category,
                      args.tags.split(",") if args.tags else [],
                      args.grid, args.max_colors)
    existing = [x for x in load_incoming() if x["id"] != p["id"]]
    existing.append(p)
    save_incoming(existing)
    print(f"  added '{p['title']}' ({p['grid']['width']}x{p['grid']['height']}, "
          f"{len(p['cells'])} beads, {len(p['palette'])} colors)")

def cmd_batch(args):
    rows = list(csv.DictReader(open(args.csv)))
    out = {x["id"]: x for x in load_incoming()}
    for r in rows:
        path = os.path.join(args.folder, r["filename"])
        p = convert_image(path, r["title"], r["category"],
                          [t.strip() for t in r.get("tags", "").split(",") if t.strip()],
                          args.grid, args.max_colors)
        out[p["id"]] = p
        print(f"  + {r['title']} ({r['category']})")
    save_incoming(list(out.values()))

def main():
    ap = argparse.ArgumentParser(description="Convert photos to library patterns")
    sub = ap.add_subparsers(required=True)
    a = sub.add_parser("add"); a.set_defaults(fn=cmd_add)
    a.add_argument("photo"); a.add_argument("--title", required=True)
    a.add_argument("--category", required=True); a.add_argument("--tags", default="")
    a.add_argument("--grid", type=int, default=32); a.add_argument("--max-colors", type=int, default=14)
    b = sub.add_parser("batch"); b.set_defaults(fn=cmd_batch)
    b.add_argument("folder"); b.add_argument("--csv", required=True)
    b.add_argument("--grid", type=int, default=32); b.add_argument("--max-colors", type=int, default=14)
    args = ap.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
