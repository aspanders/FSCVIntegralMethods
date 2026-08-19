"""Exact Python port of the shipped Android photo->bead pipeline, so the
conversion can be exercised end to end on a real photo without a device.

Mirrors, line for line:
  services/BitmapLoader.kt   (EXIF orientation + bounded decode)
  services/ColorMath.kt      (sRGB->linear, CIELAB, CIEDE2000, beadDistance)
  services/ImageConverter.kt (box-average sampling in linear light, greedy
                              error-minimizing palette selection)

Also implements the OLD pipeline so the two can be compared directly.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PALETTE = json.load(open(os.path.join(REPO, "library", "palette.json")))["colors"]
CONVERT_MAX_DIM = 1024          # BitmapLoader.CONVERT_MAX_DIM


# ── ColorMath ────────────────────────────────────────────────────────────────

def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)


def linear_rgb_to_lab(rl, gl, bl):
    x = (rl * 0.4124564 + gl * 0.3575761 + bl * 0.1804375) / 0.95047
    y = (rl * 0.2126729 + gl * 0.7151522 + bl * 0.0721750) / 1.00000
    z = (rl * 0.0193339 + gl * 0.1191920 + bl * 0.9503041) / 1.08883
    def f(t):
        return np.where(t > 0.008856, np.cbrt(t), 7.787 * t + 16.0 / 116.0)
    fx, fy, fz = f(x), f(y), f(z)
    return np.stack([116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)], axis=-1)


def srgb_to_lab(rgb01):
    lin = srgb_to_linear(rgb01)
    return linear_rgb_to_lab(lin[..., 0], lin[..., 1], lin[..., 2])


def delta_e2000(lab1, lab2):
    """Vectorised CIEDE2000. lab1 (N,3) vs lab2 (M,3) -> (N,M)."""
    L1 = lab1[:, None, 0]; a1 = lab1[:, None, 1]; b1 = lab1[:, None, 2]
    L2 = lab2[None, :, 0]; a2 = lab2[None, :, 1]; b2 = lab2[None, :, 2]
    c1 = np.hypot(a1, b1); c2 = np.hypot(a2, b2)
    cBar = (c1 + c2) / 2.0
    cBar7 = cBar ** 7
    g = 0.5 * (1.0 - np.sqrt(cBar7 / (cBar7 + 6103515625.0)))
    a1p = (1.0 + g) * a1; a2p = (1.0 + g) * a2
    c1p = np.hypot(a1p, b1); c2p = np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360.0
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360.0
    h1p = np.where((a1p == 0) & (b1 == 0), 0.0, h1p)
    h2p = np.where((a2p == 0) & (b2 == 0), 0.0, h2p)
    dLp = L2 - L1
    dCp = c2p - c1p
    cProd = c1p * c2p
    dh = h2p - h1p
    dh = np.where(dh > 180.0, dh - 360.0, dh)
    dh = np.where(dh < -180.0, dh + 360.0, dh)
    dhp = np.where(cProd == 0.0, 0.0, dh)
    dHp = 2.0 * np.sqrt(cProd) * np.sin(np.radians(dhp / 2.0))
    lBarP = (L1 + L2) / 2.0
    cBarP = (c1p + c2p) / 2.0
    hsum = h1p + h2p
    hBarP = np.where(cProd == 0.0, hsum,
             np.where(np.abs(h1p - h2p) <= 180.0, hsum / 2.0,
              np.where(hsum < 360.0, (hsum + 360.0) / 2.0, (hsum - 360.0) / 2.0)))
    t = (1.0 - 0.17 * np.cos(np.radians(hBarP - 30.0))
             + 0.24 * np.cos(np.radians(2.0 * hBarP))
             + 0.32 * np.cos(np.radians(3.0 * hBarP + 6.0))
             - 0.20 * np.cos(np.radians(4.0 * hBarP - 63.0)))
    dTheta = 30.0 * np.exp(-(((hBarP - 275.0) / 25.0) ** 2))
    cBarP7 = cBarP ** 7
    rc = 2.0 * np.sqrt(cBarP7 / (cBarP7 + 6103515625.0))
    sl = 1.0 + (0.015 * (lBarP - 50.0) ** 2) / np.sqrt(20.0 + (lBarP - 50.0) ** 2)
    sc = 1.0 + 0.045 * cBarP
    sh = 1.0 + 0.015 * cBarP * t
    rt = -np.sin(np.radians(2.0 * dTheta)) * rc
    tl = dLp / sl; tc = dCp / sc; th = dHp / sh
    return np.sqrt(tl * tl + tc * tc + th * th + rt * tc * th)


def bead_distance(src_lab, pal_lab, chroma_weight=0.45):
    """deltaE2000 plus the penalty for draining chroma out of a colourful pixel."""
    base = delta_e2000(src_lab, pal_lab)
    cs = np.hypot(src_lab[:, None, 1], src_lab[:, None, 2])
    cc = np.hypot(pal_lab[None, :, 1], pal_lab[None, :, 2])
    lost = np.clip(cs - cc, 0.0, None)
    return base + chroma_weight * lost * (cs / (cs + 12.0))


# ── BitmapLoader ─────────────────────────────────────────────────────────────

def decode_upright(path, max_dim=CONVERT_MAX_DIM):
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)          # BitmapLoader.applyOrientation
    im = im.convert("RGBA")
    w, h = im.size
    scale = min(1.0, max_dim / max(w, h))     # BitmapLoader.decodeSampled
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return im


# ── ImageConverter (new pipeline) ────────────────────────────────────────────

def chroma_lift(lab, amount=1.0, k=16.0):
    """ImageConverter.applyChromaLift: scale chroma by 1+amount*(k/(C+k))^2."""
    if amount <= 0:
        return lab
    a = lab[..., 1]; b = lab[..., 2]
    c = np.hypot(a, b)
    s = 1.0 + amount * (k / (c + k)) ** 2
    out = lab.copy()
    out[..., 1] = a * s
    out[..., 2] = b * s
    return out


def sample_cells_lab(im, cols, rows, crop=None, lift=1.0):
    """Box-average every source pixel under each bead, in LINEAR light."""
    arr = np.asarray(im, dtype=np.float64) / 255.0
    if crop is not None:
        x0, y0, x1, y1 = crop
        arr = arr[y0:y1, x0:x1]
    h, w = arr.shape[:2]
    lin = srgb_to_linear(arr[..., :3])
    alpha = arr[..., 3]
    out = np.full((rows, cols, 3), np.nan)
    for cy in range(rows):
        sy0 = cy * h // rows
        sy1 = max(sy0 + 1, min((cy + 1) * h // rows, h))
        for cx in range(cols):
            sx0 = cx * w // cols
            sx1 = max(sx0 + 1, min((cx + 1) * w // cols, w))
            a = alpha[sy0:sy1, sx0:sx1]
            block = lin[sy0:sy1, sx0:sx1]
            n = a.size
            aAcc = a.sum()
            # Matches the Kotlin: mostly-transparent cells stay empty.
            if n == 0 or aAcc / n < 0.35:
                continue
            wgt = a[..., None]
            acc = (block * wgt).reshape(-1, 3).sum(axis=0) / aAcc
            out[cy, cx] = linear_rgb_to_lab(acc[0], acc[1], acc[2])
    out = np.where(np.isnan(out), out, chroma_lift(out, lift))
    return out


def quantize_bead_safe(cell_lab, max_colors, pal_lab):
    """Greedy error-minimizing palette selection, then final assignment."""
    rows, cols = cell_lab.shape[:2]
    mask = ~np.isnan(cell_lab[..., 0])
    labs = cell_lab[mask]
    if labs.size == 0:
        return [], np.full((rows, cols), -1, dtype=int)
    dist = bead_distance(labs, pal_lab)               # (nCells, nPal)
    chosen = []
    best = np.full(len(labs), np.inf)
    for _ in range(max(1, max_colors)):
        cand = np.minimum(best[:, None], dist).sum(axis=0)
        cand[chosen] = np.inf
        p = int(np.argmin(cand))
        if not np.isfinite(cand[p]):
            break
        chosen.append(p)
        best = np.minimum(best, dist[:, p])
    sub = dist[:, chosen]
    picked = np.array(chosen)[np.argmin(sub, axis=1)]
    assign = np.full((rows, cols), -1, dtype=int)
    assign[mask] = picked
    return chosen, assign


# ── OLD pipeline, for comparison ─────────────────────────────────────────────

def old_pipeline(im, cols, rows, max_colors, pal_lab):
    """Single bilinear createScaledBitmap, sRGB averaging, dE76, top-N by count."""
    small = im.convert("RGB").resize((cols, rows), Image.BILINEAR)
    px = np.asarray(small, dtype=np.float64) / 255.0
    lab = srgb_to_lab(px).reshape(-1, 3)
    d76 = ((lab[:, None, :] - pal_lab[None, :, :]) ** 2).sum(axis=2)
    nearest = np.argmin(d76, axis=1)
    counts = np.bincount(nearest, minlength=len(pal_lab))
    top = np.argsort(counts)[::-1][:max_colors]
    top = [t for t in top if counts[t] > 0]
    sub = d76[:, top]
    picked = np.array(top)[np.argmin(sub, axis=1)]
    return top, picked.reshape(rows, cols)


# ── Pattern assembly ─────────────────────────────────────────────────────────

def build_pattern(assign, title):
    used = sorted({int(v) for v in assign.flatten() if v >= 0})
    pal = [{"id": PALETTE[i]["id"], "name": PALETTE[i]["name"], "hex": PALETTE[i]["hex"]}
           for i in used]
    rows, cols = assign.shape
    cells = []
    for y in range(rows):
        for x in range(cols):
            v = int(assign[y, x])
            if v >= 0:
                cells.append({"x": x, "y": y, "colorId": PALETTE[v]["id"]})
    return {"id": title, "title": title, "category": "custom", "createdBy": "user",
            "grid": {"width": cols, "height": rows}, "palette": pal, "cells": cells,
            "difficulty": "medium", "tags": [], "version": 1}


PAL_LAB = srgb_to_lab(
    np.array([[int(c["hex"][i:i+2], 16) / 255.0 for i in (1, 3, 5)] for c in PALETTE])
)
