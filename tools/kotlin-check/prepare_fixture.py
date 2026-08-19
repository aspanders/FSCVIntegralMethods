"""Write the deterministic fixture the Kotlin harness and the Python reference
both read: a synthetic photo and a keep-mask.

Synthetic on purpose. The point of the fixture is to exercise every branch of
the conversion - smooth gradients, flat patches, saturated and near-neutral
colour, and a mask edge that cuts cells in half - not to look like anything.
A generated fixture also means the check runs in a fresh clone with no photo
to ship and no PII to worry about.
"""
import os
import sys

import numpy as np

W, H = 288, 384


def build():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    u = xx / (W - 1)
    v = yy / (H - 1)

    # Base: a hue sweep across x, a luma ramp down y. Covers the whole gamut
    # the quantizer has to choose over, including the near-neutral middle.
    hue = u * 6.0
    i = np.floor(hue).astype(int) % 6
    f = hue - np.floor(hue)
    p, q, t = np.zeros_like(f), 1 - f, f
    one = np.ones_like(f)
    r = np.choose(i, [one, q, p, p, t, one])
    g = np.choose(i, [t, one, one, q, p, p])
    b = np.choose(i, [p, p, t, one, one, q])
    sat = 0.15 + 0.85 * np.abs(np.sin(v * np.pi * 1.5))   # sweeps through pastel
    val = 0.20 + 0.75 * (1 - v * 0.6)
    rgb = np.dstack([r, g, b])
    rgb = (1 - sat[..., None]) + sat[..., None] * rgb
    rgb = rgb * val[..., None]

    # Flat patches: regions where many cells share one colour exactly.
    for k, (cx, cy, col) in enumerate([
        (0.25, 0.20, (0.05, 0.05, 0.05)),
        (0.70, 0.25, (0.98, 0.98, 0.98)),
        (0.30, 0.62, (0.85, 0.10, 0.15)),
        (0.72, 0.70, (0.10, 0.25, 0.80)),
        (0.50, 0.88, (0.50, 0.50, 0.52)),
    ]):
        m = (np.abs(u - cx) < 0.10) & (np.abs(v - cy) < 0.07)
        rgb[m] = col

    px = np.clip(rgb * 255, 0, 255).astype(np.uint32)
    argb = (np.full((H, W), 255, dtype=np.uint32) << 24) | \
           (px[..., 0] << 16) | (px[..., 1] << 8) | px[..., 2]

    # An off-centre ellipse: its edge crosses cells at every angle, so
    # partially-masked cells (the 0.35 alpha threshold) are exercised.
    mask = (((xx - W * 0.46) / (W * 0.34)) ** 2 +
            ((yy - H * 0.52) / (H * 0.36)) ** 2) <= 1.0
    return argb, mask


def main(outdir):
    os.makedirs(outdir, exist_ok=True)
    argb, mask = build()
    argb.astype('<i4').tofile(os.path.join(outdir, "photo.argb"))
    mask.astype(np.uint8).tofile(os.path.join(outdir, "mask.u8"))
    np.save(os.path.join(outdir, "mask.npy"), mask)
    print(f"fixture {W}x{H}, kept {mask.mean():.3f} -> {outdir}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/kcheck")
