"""Compact 'rows' encoding for the shipped library.

Each pattern's cells become one string per grid row, where each character is an
index into the pattern's palette ('.' = empty). A 29x29 board shrinks from
~25 KB of {x,y,colorId} objects to ~0.9 KB. Both apps expand rows back to cells
on load using the exact same charset, so nothing else changes.
"""
# Keep in sync with FusePattern.CHARS (Kotlin) and FusePattern.rowChars (Swift).
CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
EMPTY = "."


def to_rows(pattern):
    w, h = pattern["grid"]["width"], pattern["grid"]["height"]
    idx = {c["id"]: i for i, c in enumerate(pattern["palette"])}
    grid = [[EMPTY] * w for _ in range(h)]
    for cell in pattern["cells"]:
        cid = cell.get("colorId")
        if cid is None or cid not in idx:
            continue
        x, y = cell["x"], cell["y"]
        if 0 <= x < w and 0 <= y < h:
            grid[y][x] = CHARS[idx[cid]]
    return ["".join(r) for r in grid]


def from_rows(rows, palette):
    cells = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == EMPTY:
                continue
            i = CHARS.find(ch)
            if 0 <= i < len(palette):
                cells.append({"x": x, "y": y, "colorId": palette[i]["id"]})
    return cells


def compact_pattern(p):
    """Return a copy with cells replaced by rows (for the shipped file)."""
    q = dict(p)
    q["rows"] = to_rows(p)
    q.pop("cells", None)
    # drop null optionals to trim a little more; decoders default them
    for k in ("sourcePrompt", "buildGuide", "assemblyGuide"):
        if q.get(k) is None:
            q.pop(k, None)
    return q
