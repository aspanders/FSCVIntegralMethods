"""Render BeadSnap patterns to PNGs the same way the app does, for QC.

Beads are full-size circles (diameter == cell pitch) so they touch like fused
beads, with a faint center hole and a thin rim. This mirrors ImageConverter on
both platforms, so what we inspect here is what ships.
"""
import json
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PALETTE = {c["id"]: c["hex"] for c in json.load(
    open(os.path.join(REPO, "library", "palette.json")))["colors"]}


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _cells_of(pat):
    """Cells, expanding the compact 'rows' encoding if that is what's present."""
    if pat.get("cells"):
        return pat["cells"]
    if pat.get("rows"):
        from compact import from_rows
        return from_rows(pat["rows"], pat["palette"])
    return []


def render_pattern(pat, cell=18, bg=(255, 255, 255)):
    """Render one pattern dict to a PIL RGB image with touching, fused beads."""
    w, h = pat["grid"]["width"], pat["grid"]["height"]
    # supersample for crisp anti-aliased circles, then downscale
    ss = 3
    c = cell * ss
    img = Image.new("RGB", (w * c, h * c), bg)
    d = ImageDraw.Draw(img, "RGBA")
    colors = {p["id"]: _rgb(p["hex"]) for p in pat["palette"]}
    r = c / 2.0
    hole = c * 0.17
    rim = max(1, int(c * 0.05))
    for cell_data in _cells_of(pat):
        cid = cell_data.get("colorId")
        if cid is None:
            continue
        rgb = colors.get(cid) or _rgb(PALETTE.get(cid, "#000000"))
        cx = cell_data["x"] * c + r
        cy = cell_data["y"] * c + r
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=rgb)
        d.ellipse([cx - hole, cy - hole, cx + hole, cy + hole],
                  fill=(255, 255, 255, 28))
        d.ellipse([cx - r + rim, cy - r + rim, cx + r - rim, cy + r - rim],
                  outline=(0, 0, 0, 30), width=rim)
    return img.resize((w * cell, h * cell), Image.LANCZOS)


def montage(patterns, cols=10, thumb=132, pad=10, label=True, title=None):
    """Grid of pattern thumbnails for eyeballing a whole category at once."""
    n = len(patterns)
    rows = (n + cols - 1) // cols
    labelh = 16 if label else 0
    titleh = 30 if title else 0
    cellw = thumb + pad
    cellh = thumb + labelh + pad
    W = cols * cellw + pad
    H = rows * cellh + pad + titleh
    canvas = Image.new("RGB", (W, H), (238, 240, 243))
    dd = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        tfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
        tfont = font
    if title:
        dd.text((pad, 6), title, fill=(20, 20, 20), font=tfont)
    for i, pat in enumerate(patterns):
        rr, cc = divmod(i, cols)
        x = pad + cc * cellw
        y = pad + titleh + rr * cellh
        maxdim = max(pat["grid"]["width"], pat["grid"]["height"])
        im = render_pattern(pat, cell=max(4, (thumb * 3) // maxdim))
        im.thumbnail((thumb, thumb), Image.LANCZOS)
        ox = x + (thumb - im.width) // 2
        oy = y + (thumb - im.height) // 2
        canvas.paste(im, (ox, oy))
        if label:
            t = pat["title"][:20]
            dd.text((x, y + thumb + 2), t, fill=(60, 60, 60), font=font)
    return canvas


if __name__ == "__main__":
    import sys
    data = json.load(open(sys.argv[1]))
    pats = data["patterns"] if "patterns" in data else data
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/montage.png"
    montage(pats, title=f"{len(pats)} patterns").save(out)
    print("wrote", out)
