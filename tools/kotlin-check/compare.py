"""Python reference for the fixture, diffed against the Kotlin harness dumps.

This is an INDEPENDENT implementation of the same maths (see
tools/library/pipeline_test.py), not a wrapper around the Kotlin. Agreement
between the two is what makes it evidence.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "library"))
import pipeline_test as pt          # noqa: E402

IDS = [c["id"] for c in pt.PALETTE]
# ImageConverter.autoPalette excludes the translucent "clear" bead.
ALLOW = np.array([i for i in range(len(IDS)) if IDS[i] != "clear"])
PAL = pt.PAL_LAB[ALLOW]
W, H = 288, 384


def aspect_crop(w, h, cols, rows):
    t = cols / rows
    if w / h > t:
        nw = max(1, min(w, round(h * t)))
        left = (w - nw) // 2
        return (left, 0, left + nw, h)
    nh = max(1, min(h, round(w / t)))
    top = (h - nh) // 2
    return (0, top, w, top + nh)


def convert(rgb, mask, crop, n, ncol, gains=(1, 1, 1), shape=None):
    x0, y0, x1, y1 = crop
    sub = rgb[y0:y1, x0:x1].astype(np.float64) / 255.0
    al = mask[y0:y1, x0:x1].astype(np.float64)
    hh, ww = sub.shape[:2]
    lin = pt.srgb_to_linear(sub)
    out = np.full((n, n, 3), np.nan)
    for cy in range(n):
        sy0 = cy * hh // n
        sy1 = max(sy0 + 1, min((cy + 1) * hh // n, hh))
        for cx in range(n):
            sx0 = cx * ww // n
            sx1 = max(sx0 + 1, min((cx + 1) * ww // n, ww))
            a = al[sy0:sy1, sx0:sx1]
            blk = lin[sy0:sy1, sx0:sx1]
            cnt, acc_a = a.size, a.sum()
            if cnt == 0 or acc_a / cnt < 0.35:
                continue
            fw = a.ravel()
            sel = fw > 0
            acc = pt.resolve_cell(blk.reshape(-1, 3)[sel], fw[sel])
            acc = np.clip(acc * np.asarray(gains), 0, 1)
            out[cy, cx] = pt.linear_rgb_to_lab(acc[0], acc[1], acc[2])
    if shape == "circle":
        r = n / 2.0
        yy, xx = np.mgrid[0:n, 0:n]
        out[((xx + 0.5 - n / 2.0) ** 2 + (yy + 0.5 - n / 2.0) ** 2) > r * r] = np.nan
    out = np.where(np.isnan(out), out, pt.chroma_lift(out, 1.0))
    live = ~np.isnan(out[..., 0])
    labs = out[live]
    res = np.full((n, n), -1, int)
    if labs.size == 0:
        return res
    dist = pt.bead_distance(labs, PAL)
    chosen, best = [], np.full(len(labs), np.inf)
    for _ in range(ncol):
        cand = np.minimum(best[:, None], dist).sum(axis=0)
        cand[chosen] = np.inf
        p = int(np.argmin(cand))
        if not np.isfinite(cand[p]):
            break
        chosen.append(p)
        best = np.minimum(best, dist[:, p])
    picked = np.array(chosen)[np.argmin(dist[:, chosen], axis=1)]
    res[live] = ALLOW[picked]
    return res


def read_dump(d, tag):
    lines = open(os.path.join(d, f"out_{tag}.txt")).read().strip().split("\n")
    return np.array([l.split(",") for l in lines[2:]], dtype=object)


def check(d, tag, ref):
    kot = read_dump(d, tag)
    py = np.where(ref < 0, ".", np.array(IDS, dtype=object)[np.clip(ref, 0, None)])
    occ = ((kot == ".") == (py == ".")).mean()
    both = (kot != ".") & (py != ".")
    ag = (kot[both] == py[both]).mean() if both.sum() else 1.0
    ok = occ == 1.0 and ag == 1.0
    print(f"  {tag:14s} occupancy {100*occ:6.2f}%  beads {100*ag:7.3f}%  "
          f"({both.sum():5d})  {'OK' if ok else 'MISMATCH'}")
    return ok


def main(d):
    argb = np.fromfile(os.path.join(d, "photo.argb"), dtype='<i4').reshape(H, W).astype(np.uint32)
    rgb = np.dstack([(argb >> 16) & 0xFF, (argb >> 8) & 0xFF, argb & 0xFF]).astype(np.uint8)
    mask = np.load(os.path.join(d, "mask.npy"))
    allm = np.ones((H, W), bool)
    crop = json.load(open(os.path.join(d, "crops.json")))

    ok = True
    ok &= check(d, "plain", convert(rgb, allm, aspect_crop(W, H, 48, 48), 48, 16))
    ok &= check(d, "circle", convert(rgb, allm, aspect_crop(W, H, 48, 48), 48, 12, shape="circle"))
    ok &= check(d, "cutout", convert(rgb, mask, tuple(crop["subject"]), 48, 16))
    g = crop["gains"]
    ok &= check(d, "wb50", convert(rgb, mask, tuple(crop["subject"]), 48, 16,
                                   gains=[1 + 0.5 * (x - 1) for x in g]))
    print("REFERENCE CHECK:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/kcheck"))
