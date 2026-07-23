"""Shared helpers for building BeadSnap's downloadable pattern library.

The LAB color math here mirrors the app (BeadColor.rgbToLab / ImageConverter),
so patterns produced by these tools quantize to exactly the same bead colors
the app would pick.
"""
import json
import os
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PALETTE_PATH = os.path.join(REPO, "library", "palette.json")

# The 10 content categories are procedurally generated (100 each). threeD is a
# retained specialty (build/assembly guides); custom is the user's own designs.
CATEGORIES = ["geometric", "mandalas", "hearts", "stars", "flowers",
              "rainbows", "space", "emoji", "gems", "icons", "threeD"]

# ── Palette ────────────────────────────────────────────────────────────────

def load_palette():
    return json.load(open(PALETTE_PATH))["colors"]

PALETTE = load_palette()
_BY_ID = {c["id"]: c for c in PALETTE}

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

# ── CIE Lab (same constants as BeadColor.rgbToLab) ───────────────────────────

def _linearize(c):
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92

def rgb_to_lab(r, g, b):
    """r,g,b in 0..1 → (L, a, b), identical to the app's conversion."""
    rl, gl, bl = _linearize(r), _linearize(g), _linearize(b)
    x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047
    y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000
    z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883
    def f(t):
        return t ** (1.0 / 3.0) if t > 0.008856 else 7.787 * t + 16.0 / 116.0
    return (116.0 * f(y) - 16.0, 500.0 * (f(x) - f(y)), 200.0 * (f(y) - f(z)))

_PALETTE_LAB = [
    (c["id"], rgb_to_lab(*(v / 255.0 for v in hex_to_rgb(c["hex"])))) for c in PALETTE
]

def nearest_color_id(r, g, b):
    """r,g,b in 0..255 → the id of the perceptually-nearest bead color."""
    lab = rgb_to_lab(r / 255.0, g / 255.0, b / 255.0)
    best_id, best_d = None, float("inf")
    for cid, (cl, ca, cb) in _PALETTE_LAB:
        d = (lab[0] - cl) ** 2 + (lab[1] - ca) ** 2 + (lab[2] - cb) ** 2
        if d < best_d:
            best_d, best_id = d, cid
    return best_id

# ── Pattern construction ─────────────────────────────────────────────────────

def make_pattern(pattern_id, title, category, width, height, cells, tags,
                 difficulty=None, source_prompt=None,
                 build_guide=None, assembly_guide=None):
    """Build a FusePattern dict matching the app's model.

    `cells` is a list of (x, y, color_id). Palette is derived from the colors
    actually used, in the app's canonical order. `build_guide`/`assembly_guide`
    are used by 3D constructions and stay null for flat patterns.
    """
    assert category in CATEGORIES, f"bad category {category}"
    used = []
    seen = set()
    # keep palette in canonical order for stable, app-matching output
    used_ids = {cid for _, _, cid in cells}
    for c in PALETTE:
        if c["id"] in used_ids and c["id"] not in seen:
            used.append({"id": c["id"], "name": c["name"], "hex": c["hex"]})
            seen.add(c["id"])
    # dedup cells (last writer wins), drop out-of-bounds
    cellmap = {}
    for x, y, cid in cells:
        if 0 <= x < width and 0 <= y < height and cid is not None:
            cellmap[(x, y)] = cid
    cell_list = [{"x": x, "y": y, "colorId": cid} for (x, y), cid in sorted(cellmap.items(), key=lambda kv: (kv[0][1], kv[0][0]))]
    if difficulty is None:
        n = len(cell_list)
        difficulty = "easy" if n < 80 else "medium" if n < 350 else "hard"
    return {
        "id": pattern_id,
        "title": title,
        "category": category,
        "createdBy": "system",
        "grid": {"width": width, "height": height},
        "palette": used,
        "cells": cell_list,
        "difficulty": difficulty,
        "tags": tags,
        "sourcePrompt": source_prompt,
        "buildGuide": build_guide,
        "assemblyGuide": assembly_guide,
        "version": 1,
    }

def cells_from_ascii(rows, char_map):
    """rows: list[str], char_map: {char: color_id}. Returns [(x,y,color_id)]."""
    out = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            cid = char_map.get(ch)
            if cid is not None:
                out.append((x, y, cid))
    return out

def stable_id(prefix, key):
    """Deterministic id so re-runs don't churn ids (uuid5 over a fixed namespace)."""
    ns = uuid.UUID("b3ad5na9-0000-4000-8000-000000000001".replace("-", "")[:32].rjust(32, "0")[:32]) \
        if False else uuid.NAMESPACE_URL
    return f"{prefix}-" + str(uuid.uuid5(ns, f"beadsnap:{prefix}:{key}"))
