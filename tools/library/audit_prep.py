"""Prepare an independent audit of one category.

Renders every pattern as a numbered tile (index only, so the reviewer is not
told the answer) into montages of BATCH tiles, and writes a manifest mapping
each index to its intended label. An audit workflow then has a separate agent
view each montage, guess what each tile is, rate how clearly it reads, and
suggest a fix.

Usage: python audit_prep.py <category> [outdir]
"""
import json
import os
import sys

import render
import gen_library
import gen_library2
import gen_icons
import gen_3d

BATCH = 20
COLS = 5


def patterns_for(cat):
    if cat in gen_library.GENERATORS:
        return gen_library.GENERATORS[cat]()
    if cat in gen_library2.GENERATORS:
        return gen_library2.GENERATORS[cat]()
    if cat == "icons":
        return gen_icons.generate()
    if cat == "threeD":
        return gen_3d.generate()
    raise SystemExit(f"unknown category {cat}")


def main():
    cat = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else \
        f"/tmp/claude-0/-home-user-FSCVIntegralMethods/677f742f-722e-571e-8869-71f8aa1b6295/scratchpad/audit/{cat}"
    os.makedirs(outdir, exist_ok=True)
    pats = patterns_for(cat)
    batches = []
    for b, start in enumerate(range(0, len(pats), BATCH)):
        chunk = pats[start:start + BATCH]
        path = os.path.join(outdir, f"{cat}_b{b:02d}.png")
        render.numbered_montage(chunk, start=start + 1, cols=COLS,
                                title=f"{cat} tiles {start+1}-{start+len(chunk)}").save(path)
        labels_path = os.path.join(outdir, f"{cat}_b{b:02d}_labels.txt")
        with open(labels_path, "w") as f:
            for i, p in enumerate(chunk):
                f.write(f"#{start + i + 1} = {p['title']}\n")
        batches.append({
            "montage": path, "labels": labels_path,
            "first": start + 1, "last": start + len(chunk),
        })
    manifest = {"category": cat, "count": len(pats), "batches": batches}
    mpath = os.path.join(outdir, f"{cat}_manifest.json")
    json.dump(manifest, open(mpath, "w"), indent=2)
    print(mpath)
    print(f"{cat}: {len(pats)} tiles in {len(batches)} montages")


if __name__ == "__main__":
    main()
