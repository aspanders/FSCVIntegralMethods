"""BeadSnap app icon: one polished lapis-lazuli fuse bead on a crisp white
background, ray-marched from the real part dimensions.

Geometry comes from an actual fuse bead: 5.0 mm outer diameter, 2.0 mm inner
diameter, 5.0 mm height. Two consequences matter for the image:

  * The bead is exactly as tall as it is wide, so it reads as a short tube,
    not a flat disc.
  * The bore is 5 mm deep but only 2 mm across, so beyond atan(2/5) = 21.8
    degrees of tilt you cannot see through it. At the 31-degree view used
    here the far bore wall occludes the opening, making the dark center real
    occlusion rather than a painted-on dot.

The bead is a signed-distance field (rounded cylinder, smooth-subtracted
bore) rather than a hard analytic cylinder. Real beads have rounded edges,
and that rounding is what produces the highlight along the rim and the
gradient across the top face. A hard cylinder renders dead flat on top
because its normal is constant there.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# ── Real fuse-bead dimensions (mm) ───────────────────────────────────────────
OD, ID, HEIGHT = 5.0, 2.0, 5.0
R = OD / 2.0
RI = ID / 2.0
H = HEIGHT
EDGE = 0.42          # edge rounding radius; real beads are noticeably soft
LIP = 0.30           # smoothing on the bore lip

PHI = math.radians(31.0)
S, K = math.sin(PHI), math.cos(PHI)
BOUND = math.sqrt(R * R + (H / 2.0) ** 2) + 0.2

# ── Lapis lazuli ─────────────────────────────────────────────────────────────
LAPIS_DEEP = np.array([13, 26, 74], dtype=np.float32)     # shadowed ultramarine
LAPIS_MID = np.array([28, 62, 152], dtype=np.float32)
LAPIS_LIT = np.array([68, 122, 214], dtype=np.float32)    # lit face
PYRITE = np.array([206, 168, 84], dtype=np.float32)       # gold inclusions
CALCITE = np.array([196, 208, 232], dtype=np.float32)     # pale veining

LIGHT = np.array([-0.40, -0.52, 0.75], dtype=np.float32)
LIGHT /= np.linalg.norm(LIGHT)
FILL = np.array([0.55, 0.30, 0.30], dtype=np.float32)     # soft bounce
FILL /= np.linalg.norm(FILL)
VIEW = np.array([0.0, -S, K], dtype=np.float32)
HALF = LIGHT + VIEW
HALF /= np.linalg.norm(HALF)


def _sdf(x, y, z):
    """Rounded cylinder with the bore smoothly subtracted."""
    rho = np.sqrt(x * x + y * y)
    dx = rho - (R - EDGE)
    dz = np.abs(z) - (H / 2.0 - EDGE)
    body = (np.minimum(np.maximum(dx, dz), 0.0)
            + np.sqrt(np.maximum(dx, 0.0) ** 2 + np.maximum(dz, 0.0) ** 2)
            - EDGE)
    bore = rho - RI
    # smooth subtraction, so the bore lip is a soft chamfer that catches light
    h = np.clip(0.5 - 0.5 * (body + bore) / LIP, 0.0, 1.0)
    return (body * (1.0 - h) + (-bore) * h) + LIP * h * (1.0 - h)


def _normal(x, y, z):
    """Tetrahedral 4-tap gradient of the SDF."""
    e = 1e-3
    o = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], dtype=np.float32)
    nx = ny = nz = 0.0
    for k in o:
        d = _sdf(x + k[0] * e, y + k[1] * e, z + k[2] * e)
        nx = nx + k[0] * d
        ny = ny + k[1] * d
        nz = nz + k[2] * d
    n = np.sqrt(nx * nx + ny * ny + nz * nz) + 1e-9
    return nx / n, ny / n, nz / n


def _hash3(cx, cy, cz):
    """Deterministic per-cell pseudo-random in [0,1)."""
    v = np.sin(cx * 127.1 + cy * 311.7 + cz * 74.7) * 43758.5453
    return v - np.floor(v)


def _mottle(x, y, z):
    """Smooth organic variation, for the cloudiness real lapis has. Built from
    incommensurate sine waves so it never falls into a visible grid."""
    return (np.sin(2.9 * x + 1.7 * y + 0.4)
            + np.sin(2.3 * y - 3.1 * z + 1.1)
            + np.sin(3.7 * z + 2.2 * x + 2.6)
            + 0.5 * np.sin(6.1 * x - 5.3 * y + 0.9)) * 0.25


def _trace(N, wpp):
    xs = (np.arange(N, dtype=np.float32) - (N - 1) / 2.0) * wpp
    ys = ((N - 1) / 2.0 - np.arange(N, dtype=np.float32)) * wpp
    U, V = np.meshgrid(xs, ys)

    # Only march rays that can reach the bounding sphere; U,V are already the
    # perpendicular offsets from the axis, so this is an exact cull.
    live = (U * U + V * V) < (BOUND * BOUND)
    u = U[live].astype(np.float32)
    v = V[live].astype(np.float32)

    START = 12.0
    ox = u
    oy = v * K - START * S
    oz = v * S + START * K
    dx, dy, dz = 0.0, S, -K

    # Rays that graze past the object without hitting can dawdle near a small
    # SDF value for many steps; hard-clamp t so they can never run away to a
    # magnitude that overflows float32 on the next SDF evaluation. Cheap and
    # exact: anything past START+BOUND is already a guaranteed miss.
    t_cap = np.float32(START + BOUND + 1.0)
    t = np.full(u.shape, START - BOUND, dtype=np.float32)
    hit = np.zeros(u.shape, dtype=bool)
    with np.errstate(over="ignore", invalid="ignore"):
        for _ in range(96):
            px = ox + t * dx
            py = oy + t * dy
            pz = oz + t * dz
            d = _sdf(px, py, pz)
            newly = (~hit) & (d < 1e-3)
            hit |= newly
            t = np.where(hit, t, np.minimum(t + np.maximum(d, 1e-4) * 0.92, t_cap))
            if np.all(hit | (t >= t_cap)):
                break
    hit &= t <= START + BOUND

    px = ox + t * dx
    py = oy + t * dy
    pz = oz + t * dz
    nx, ny, nz = _normal(px, py, pz)

    ndl = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0.0, 1.0)
    ndf = np.clip(nx * FILL[0] + ny * FILL[1] + nz * FILL[2], 0.0, 1.0)
    ndh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0.0, 1.0)
    ndv = np.clip(nx * VIEW[0] + ny * VIEW[1] + nz * VIEW[2], 0.0, 1.0)

    # Base stone colour: shadow -> mid -> lit, with lapis mottling.
    m = np.clip(_mottle(px, py, pz) * 0.5 + 0.5, 0.0, 1.0)
    base = (LAPIS_DEEP[None, :] * (1.0 - ndl[:, None])
            + LAPIS_MID[None, :] * (0.55 + 0.45 * m[:, None]) * ndl[:, None] * 0.55
            + LAPIS_LIT[None, :] * (ndl[:, None] ** 1.6) * 0.85)
    base = base + LAPIS_MID[None, :] * 0.22 * ndf[:, None]

    # Pyrite flecks and faint calcite veining, keyed to a spatial grid so they
    # sit on the stone rather than shimmering per-pixel.
    cell = 9.0
    hsh = _hash3(np.floor(px * cell), np.floor(py * cell), np.floor(pz * cell))
    fl = np.clip((hsh - 0.988) * 90.0, 0.0, 1.0)
    base = base + PYRITE[None, :] * fl[:, None] * (0.30 + 0.70 * ndl[:, None])
    vein = np.clip((np.abs(_mottle(px * 1.9, py * 1.9, pz * 1.9)) - 0.93) * 12.0, 0.0, 1.0)
    base = base + CALCITE[None, :] * vein[:, None] * 0.30 * (0.3 + 0.7 * ndl[:, None])

    # Bore falls off into shadow with depth.
    rho = np.sqrt(px * px + py * py)
    in_bore = rho < (RI + LIP * 1.2)
    depth = np.clip((H / 2.0 - pz) / H, 0.0, 1.0)
    occ = np.where(in_bore, np.clip(0.42 - 0.34 * depth, 0.04, 1.0), 1.0)
    base = base * occ[:, None]

    # Polished specular: a tight lobe plus a broad sheen, killed inside the bore.
    spec = 0.95 * np.power(ndh, 90.0) + 0.30 * np.power(ndh, 14.0)
    spec = spec * np.where(in_bore, 0.06, 1.0)
    # Fresnel rim, which is what makes polished stone read as glossy.
    fres = np.power(1.0 - ndv, 3.2) * 0.30
    col = base + 255.0 * (spec + fres)[:, None]

    # Contact darkening where the wall meets the ground.
    foot = np.clip((pz + H / 2.0) / (H * 0.40), 0.0, 1.0)
    col = col * (0.60 + 0.40 * foot)[:, None]

    rgb = np.zeros((N, N, 3), dtype=np.float32)
    alpha = np.zeros((N, N), dtype=np.float32)
    tmp = np.zeros((u.shape[0], 3), dtype=np.float32)
    tmp[hit] = np.clip(col[hit], 0, 255)
    rgb[live] = tmp
    a = np.zeros(u.shape, dtype=np.float32)
    a[hit] = 1.0
    alpha[live] = a
    return rgb, alpha


def render(px, ss=2, margin=0.16, white_bg=True):
    N = px * ss
    bead_w = 2 * R
    bead_h = H * S + 2 * R * K
    wpp = max(bead_w, bead_h) / (N * (1.0 - 2 * margin))

    rgb, alpha = _trace(N, wpp)
    bead = Image.fromarray(
        np.dstack([rgb, alpha * 255.0]).astype(np.uint8), "RGBA")

    # Soft contact shadow hugging the bottom face.
    shadow = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    cy = (N - 1) / 2.0 + (H / 2.0 * S) / wpp
    sx = (R * 1.04) / wpp
    sy = (R * K * 1.04) / wpp
    sd.ellipse([(N - 1) / 2.0 - sx, cy - sy + N * 0.004,
                (N - 1) / 2.0 + sx, cy + sy + N * 0.004],
               fill=(30, 42, 74, 105))
    shadow = shadow.filter(ImageFilter.GaussianBlur(N * 0.013))

    base = Image.new("RGBA", (N, N), (255, 255, 255, 255) if white_bg else (0, 0, 0, 0))
    out = Image.alpha_composite(base, shadow)
    out = Image.alpha_composite(out, bead)
    return out.resize((px, px), Image.LANCZOS)


DENSITIES = {"mdpi": 1.0, "hdpi": 1.5, "xhdpi": 2.0, "xxhdpi": 3.0, "xxxhdpi": 4.0}


def main():
    ios = render(1024, ss=2, margin=0.15, white_bg=True).convert("RGB")
    ios_path = os.path.join(REPO, "BeadSnap", "BeadSnap", "Resources",
                            "Assets.xcassets", "AppIcon.appiconset", "AppIcon-1024.png")
    ios.save(ios_path, "PNG")
    print("iOS:", ios_path, ios.size, ios.mode)

    # Android adaptive icon: the launcher masks the outer ~25%, so the bead
    # needs a wider margin. Rendered once and downscaled so all densities match.
    res = os.path.join(REPO, "BeadSnapAndroid", "app", "src", "main", "res")
    fg_master = render(432, ss=3, margin=0.23, white_bg=False)
    for name, scale in DENSITIES.items():
        canvas = int(round(108 * scale))
        d = os.path.join(res, f"mipmap-{name}")
        os.makedirs(d, exist_ok=True)
        fg_master.resize((canvas, canvas), Image.LANCZOS).save(
            os.path.join(d, "ic_launcher_foreground.png"), "PNG")
        Image.new("RGB", (canvas, canvas), (255, 255, 255)).save(
            os.path.join(d, "ic_launcher_background.png"), "PNG")
        print("Android:", name, canvas)

    # Google Play "Store listing" icon: separate from the launcher icon,
    # exactly 512x512, 32-bit PNG WITH an alpha channel (unlike the iOS
    # master, which must have none). Opaque white background, alpha=255
    # throughout, to satisfy the format literally while looking identical.
    store_dir = os.path.join(REPO, "store", "icon")
    os.makedirs(store_dir, exist_ok=True)
    play = render(512, ss=2, margin=0.15, white_bg=True)
    play.putalpha(255)
    play_path = os.path.join(store_dir, "play-store-icon-512.png")
    play.save(play_path, "PNG")
    print("Play Store:", play_path, play.size, play.mode)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == "preview":
        render(1024, ss=2, margin=0.15, white_bg=True).convert("RGB").save(sys.argv[2])
        print("wrote", sys.argv[2])
    else:
        main()
